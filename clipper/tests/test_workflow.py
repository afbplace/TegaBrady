import io

import requests

import publisher


def upload(client, media, rights=True):
    data = {"file": (open(media["source"], "rb"), "source.mp4")}
    if rights:
        data["rights_confirmed"] = "true"
    return client.post("/api/projects", data=data, content_type="multipart/form-data")


def ready_video(client, media):
    assert upload(client, media).status_code == 201
    proj = client.get("/api/projects").get_json()[0]
    assert proj["status"] == "ready" and proj["opus_mode"] == "mock"
    assert all(c["is_mock"] for c in proj["clips"]) and len(proj["clips"]) >= 2
    vid = client.post(f"/api/clips/{proj['clips'][0]['id']}/select").get_json()["video_id"]
    client.post(f"/api/videos/{vid}/reaction", data={"file": (open(media["reaction"], "rb"), "r.mp4")},
                content_type="multipart/form-data")
    client.post(f"/api/videos/{vid}", json={"talking_points": "My first point.\nSecond point",
                                           "title": "My first point.", "caption": "My first point.",
                                           "subtitles": "My first point.", "layout": "stack"})
    v = client.post(f"/api/videos/{vid}/render").get_json()
    v = client.get(f"/api/videos/{vid}").get_json()
    assert v["render_status"] == "rendered", v["render_error"]
    return vid


def approve(client, vid):
    return client.post(f"/api/videos/{vid}/approve", json={"video_reviewed": True, "captions_reviewed": True})


def test_rights_required(client, media):
    assert upload(client, media, rights=False).status_code == 400


def test_mock_url_only_fails_clearly(client):
    client.post("/api/projects", data={"source_url": "https://example.com/v", "rights_confirmed": "true"})
    p = client.get("/api/projects").get_json()[0]
    assert p["status"] == "failed" and "MOCK" in p["error"]


def test_bad_upload_rejected(client):
    r = client.post("/api/projects", data={"rights_confirmed": "true", "file": (io.BytesIO(b"x"), "a.exe")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_full_mock_flow_approval_and_duplicates(client, media):
    vid = ready_video(client, media)
    v = client.post(f"/api/videos/{vid}/drafts").get_json()
    assert v["drafts"]["titles"][0] == "My first point."
    # cannot publish before approval
    assert client.post(f"/api/videos/{vid}/publish", json={"platforms": ["tiktok"]}).status_code == 400
    # approval needs both confirmations
    assert client.post(f"/api/videos/{vid}/approve", json={"video_reviewed": True}).status_code == 400
    assert approve(client, vid).get_json()["approval_valid"]
    r = client.post(f"/api/videos/{vid}/publish", json={"platforms": ["instagram", "tiktok", "youtube"]}).get_json()
    assert sorted(r["submitted"]) == ["instagram", "tiktok", "youtube"]
    pubs = client.get(f"/api/videos/{vid}").get_json()["publications"]
    assert {p["status"] for p in pubs} == {"mock_published"} and all(p["is_mock"] for p in pubs)
    # duplicate attempt is refused
    r = client.post(f"/api/videos/{vid}/publish", json={"platforms": ["tiktok"]}).get_json()
    assert r["submitted"] == [] and "tiktok" in r["skipped"]
    # editing the caption revokes approval
    client.post(f"/api/videos/{vid}", json={"caption": "changed"})
    v = client.get(f"/api/videos/{vid}").get_json()
    assert not v["approval_valid"]
    assert client.post(f"/api/videos/{vid}/publish", json={"platforms": ["tiktok"]}).status_code == 400


class FakeResp:
    def __init__(self, body, code=200):
        self.status_code, self._b, self.text, self.content = code, body, str(body), b"x"
        self.headers = {}

    def json(self):
        return self._b


def go_live(monkeypatch):
    monkeypatch.setenv("UPLOAD_POST_API_KEY", "test-key")
    monkeypatch.setenv("UPLOAD_POST_USER", "peezy")


def live_pubs(client, vid, path="get"):
    v = client.post(f"/api/videos/{vid}/refresh").get_json() if path == "refresh" \
        else client.get(f"/api/videos/{vid}").get_json()
    return {p["platform"]: p for p in v["publications"] if not p["is_mock"]}


def test_live_requires_confirmation_to_mark_published(client, media, monkeypatch):
    vid = ready_video(client, media)
    approve(client, vid)
    go_live(monkeypatch)
    sent = {}

    def fake_post(url, headers, data, files, timeout):
        sent.update(url=url, headers=headers, data=data)
        # documented async response: only a request_id, no per-platform results yet
        return FakeResp({"success": True, "message": "Upload initiated successfully in background.",
                         "request_id": dict(data)["request_id"], "total_platforms": 3})
    monkeypatch.setattr(requests, "post", fake_post)
    r = client.post(f"/api/videos/{vid}/publish", json={"platforms": ["instagram", "tiktok", "youtube"]}).get_json()
    assert sorted(r["submitted"]) == ["instagram", "tiktok", "youtube"]
    d = dict(sent["data"])
    assert sent["url"].endswith("/api/upload")
    assert sent["headers"]["Authorization"] == "Apikey test-key"
    assert sent["headers"]["Idempotency-Key"] == d["request_id"]
    assert d["user"] == "peezy" and d["title"] == "My first point." and d["async_upload"] == "true"
    assert d["media_type"] == "REELS" and d["post_mode"] == "DIRECT_POST" and d["disable_inbox_fallback"] == "true"
    assert "privacy_level" not in d                      # TikTok account default unless configured
    assert [v for k, v in sent["data"] if k == "platform[]"] == ["instagram", "tiktok", "youtube"]
    pubs = live_pubs(client, vid)
    assert {p["status"] for p in pubs.values()} == {"pending"}

    # documented status shape: results is a LIST with a platform field
    status_body = {"status": "in_progress", "results": [
        {"platform": "instagram", "success": False, "status": "failed", "error": "Expired access token"},
        {"platform": "tiktok", "success": True, "status": "completed", "post_url": None,
         "platform_post_id": "v_pub_123", "warnings": ["post id released later"]},
        {"platform": "youtube", "success": True, "status": "completed", "video_id": "yt123"}]}
    seen = {}

    def fake_get(url, headers, params, timeout):
        seen.update(url=url, params=params)
        return FakeResp(status_body)
    monkeypatch.setattr(requests, "get", fake_get)
    pubs = live_pubs(client, vid, "refresh")
    assert seen["url"].endswith("/api/uploadposts/status") and seen["params"]["request_id"] == d["request_id"]
    assert pubs["instagram"]["status"] == "failed" and "Expired" in pubs["instagram"]["error"]
    assert pubs["tiktok"]["status"] == "pending"      # success but no public post yet -> NOT published
    assert pubs["youtube"]["status"] == "published"
    assert pubs["youtube"]["post_url"] == "https://www.youtube.com/shorts/yt123"

    status_body["results"][1].update(post_url="https://www.tiktok.com/@peezy/video/42", post_id="42")
    assert live_pubs(client, vid, "refresh")["tiktok"]["status"] == "published"

    # retry only the failed platform; confirmed ones are skipped; retry gets a NEW request id
    r = client.post(f"/api/videos/{vid}/publish", json={"platforms": ["instagram", "tiktok"]}).get_json()
    assert r["submitted"] == ["instagram"] and "tiktok" in r["skipped"]
    assert dict(sent["data"])["request_id"] != d["request_id"]


def test_tiktok_inbox_fallback_is_not_published(client, media, monkeypatch):
    vid = ready_video(client, media)
    approve(client, vid)
    go_live(monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResp({"success": True, "results": {
        "tiktok": {"success": True, "fallback_to_inbox": True, "publish_id": "v_inbox_file~1"}}}))
    client.post(f"/api/videos/{vid}/publish", json={"platforms": ["tiktok"]})
    p = live_pubs(client, vid)["tiktok"]
    assert p["status"] == "needs_action" and "NOT live" in p["error"]
    assert client.post(f"/api/videos/{vid}/publish", json={"platforms": ["tiktok"]}).get_json()["submitted"] == []


def test_live_timeout_is_tracked_not_resent(client, media, monkeypatch):
    vid = ready_video(client, media)
    approve(client, vid)
    go_live(monkeypatch)
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise requests.Timeout("read timed out")
    monkeypatch.setattr(requests, "post", boom)
    client.post(f"/api/videos/{vid}/publish", json={"platforms": ["youtube"]})
    p = live_pubs(client, vid)["youtube"]
    assert p["status"] == "pending" and "request id" in p["error"]
    assert client.post(f"/api/videos/{vid}/publish", json={"platforms": ["youtube"]}).get_json()["submitted"] == []
    assert len(calls) == 1
    # Upload-Post did receive it and it went live
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp({"status": "completed", "results": [
        {"platform": "youtube", "success": True, "status": "completed", "url": "https://youtu.be/x", "video_id": "x"}]}))
    assert live_pubs(client, vid, "refresh")["youtube"]["status"] == "published"


def test_http_error_marks_failed(client, media, monkeypatch):
    vid = ready_video(client, media)
    approve(client, vid)
    go_live(monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResp(
        {"success": False, "message": "TikTok uploads are not available on the Free plan."}, 403))
    client.post(f"/api/videos/{vid}/publish", json={"platforms": ["tiktok"]})
    p = live_pubs(client, vid)["tiktok"]
    assert p["status"] == "failed" and "Free plan" in p["error"]


def test_interpret():
    assert publisher.interpret("x", None)[0] == "pending"
    assert publisher.interpret("tiktok", {"success": True, "publish_id": "1"})[0] == "pending"
    assert publisher.interpret("instagram", {"success": True, "url": "https://instagram.com/p/1"})[0] == "published"
    assert publisher.interpret("instagram", {"success": True, "status": "processing"})[0] == "pending"
    assert publisher.interpret("x", {"success": False, "status": "retryable"})[0] == "pending"
    assert publisher.interpret("youtube", {"success": False, "skipped": True, "error": "no account"})[0] == "failed"


def test_check_endpoint_mock(client):
    r = client.get("/api/check").get_json()
    assert r["opusclip"]["mode"] == "mock" and r["publisher"]["mode"] == "mock"


def test_check_connection_live(monkeypatch):
    go_live(monkeypatch)

    def fake_get(url, headers, timeout):
        if url.endswith("/me"):
            return FakeResp({"success": True, "plan": "Basic"})
        return FakeResp({"profiles": [{"username": "peezy", "social_accounts": {
            "instagram": {"handle": "peezyreport"}, "tiktok": "", "youtube": {"reauth_required": True}}}]})
    monkeypatch.setattr(requests, "get", fake_get)
    r = publisher.check_connection()
    assert r["plan"] == "Basic"
    assert r["platforms"] == {"instagram": "connected (peezyreport)", "tiktok": "not connected",
                              "youtube": "reconnect required"}
