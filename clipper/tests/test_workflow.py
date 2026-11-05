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

    def json(self):
        return self._b


def go_live(monkeypatch):
    monkeypatch.setenv("UPLOAD_POST_API_KEY", "test-key")
    monkeypatch.setenv("UPLOAD_POST_USER", "peezy")


def test_live_requires_confirmation_to_mark_published(client, media, monkeypatch):
    vid = ready_video(client, media)
    approve(client, vid)
    go_live(monkeypatch)
    sent = {}

    def fake_post(url, headers, data, files, timeout):
        sent.update(headers=headers, data=data)
        return FakeResp({"request_id": "req1", "results": {
            "tiktok": {"success": True, "url": "https://tiktok.com/@p/video/1"},
            "youtube": {"success": True},                     # no id/url -> not confirmed
            "instagram": {"success": False, "error": "IG account not linked"}}})
    monkeypatch.setattr(requests, "post", fake_post)
    client.post(f"/api/videos/{vid}/publish", json={"platforms": ["instagram", "tiktok", "youtube"]})
    assert sent["headers"]["Authorization"] == "Apikey test-key"
    assert ("platform[]", "tiktok") in sent["data"]
    pubs = {p["platform"]: p for p in client.get(f"/api/videos/{vid}").get_json()["publications"] if not p["is_mock"]}
    assert pubs["tiktok"]["status"] == "published"
    assert pubs["youtube"]["status"] == "pending"
    assert pubs["instagram"]["status"] == "failed"

    # status poll confirms youtube
    monkeypatch.setattr(requests, "get", lambda url, headers, params, timeout: FakeResp(
        {"results": {"youtube": {"success": True, "video_id": "yt123"}}}))
    pubs = {p["platform"]: p for p in client.post(f"/api/videos/{vid}/refresh").get_json()["publications"]}
    assert pubs["youtube"]["status"] == "published" and pubs["youtube"]["provider_post_id"] == "yt123"

    # retry only the failed platform; published ones are skipped
    r = client.post(f"/api/videos/{vid}/publish", json={"platforms": ["instagram", "tiktok"]}).get_json()
    assert r["submitted"] == ["instagram"] and "tiktok" in r["skipped"]


def test_live_timeout_is_unknown_not_retryable(client, media, monkeypatch):
    vid = ready_video(client, media)
    approve(client, vid)
    go_live(monkeypatch)

    def boom(*a, **k):
        raise requests.Timeout("read timed out")
    monkeypatch.setattr(requests, "post", boom)
    client.post(f"/api/videos/{vid}/publish", json={"platforms": ["youtube"]})
    p = [p for p in client.get(f"/api/videos/{vid}").get_json()["publications"] if not p["is_mock"]][0]
    assert p["status"] == "unknown"
    r = client.post(f"/api/videos/{vid}/publish", json={"platforms": ["youtube"]}).get_json()
    assert r["submitted"] == []


def test_interpret():
    assert publisher.interpret("x", None)[0] == "pending"
    assert publisher.interpret("x", {"success": True})[0] == "pending"
    assert publisher.interpret("x", {"success": True, "post_id": "1"})[0] == "published"
