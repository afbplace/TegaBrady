import requests

import opusclip
import render
from test_workflow import FakeResp


def test_time_ranges_unit_detection():
    assert opusclip._ranges_seconds({"timeRanges": [[192170, 211630]], "durationMs": 19460}) == [(192.17, 211.63)]
    assert opusclip._ranges_seconds({"timeRanges": [[10, 25.5]], "durationMs": 15500}) == [(10.0, 25.5)]


def test_srt_from_word_timings():
    words = [(9.0, 9.5, "skip"), (10.0, 10.4, "Hello"), (10.5, 11.0, "there"), (13.0, 13.5, "friends")]
    srt = opusclip.srt_for_ranges(words, [(10.0, 14.0)])
    assert srt.splitlines()[:3] == ["1", "00:00:00,000 --> 00:00:01,000", "Hello there"]
    assert "00:00:03,000 --> 00:00:03,500\nfriends" in srt
    assert len(render.parse_subtitles(srt, 4)) == 2


def test_run_live_upload_flow(media, tmp_path, monkeypatch):
    monkeypatch.setenv("OPUSCLIP_API_KEY", "k")
    calls = []

    def fake_post(url, headers=None, json=None, data=None, timeout=None):
        calls.append(("POST", url, json))
        if url.endswith("/upload-links"):
            assert json == {"video": {"usecase": "LocalUpload"}}
            return FakeResp({"url": "https://storage.example/upload", "uploadId": "up1"})
        if url == "https://storage.example/upload":
            assert headers["x-goog-resumable"] == "start"
            r = FakeResp({}, 201); r.headers = {"Location": "https://storage.example/session"}; r.content = b""
            return r
        if url.endswith("/clip-projects"):
            assert json["videoUrl"] == "up1" and json["curationPref"]["enableAutoHook"] is False
            return FakeResp({"id": "P1", "projectId": "P1", "stage": "QUEUED"})
        raise AssertionError(url)

    def fake_put(url, data=None, headers=None, timeout=None):
        assert url == "https://storage.example/session"
        return FakeResp({}, 200)

    stages = iter(["QUEUED", "CURATE", "COMPLETE"])

    def fake_get(url, headers=None, params=None, timeout=None, stream=None):
        calls.append(("GET", url, params))
        assert headers["Authorization"] == "Bearer k"
        if url.endswith("/clip-projects/P1"):
            return FakeResp({"id": "P1", "stage": next(stages)})
        if url.endswith("/exportable-clips"):
            return FakeResp([{"id": "P1.C1", "title": "AI title", "text": "hello there",
                              "durationMs": 3000, "timeRanges": [[2000, 5000]], "uriForExport": "https://cdn/x.mp4"}])
        if url.endswith("/transcripts"):
            return FakeResp({"data": [{"start": 2, "end": 5, "text": "hello there",
                                       "words": [{"word": "hello", "start": 2.1, "end": 2.5},
                                                 {"word": "there", "start": 2.6, "end": 3.0}]}]})
        raise AssertionError(url)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "put", fake_put)
    monkeypatch.setattr(requests, "get", fake_get)
    out = list(opusclip.run_live(None, str(media["source"]), tmp_path, sleep=lambda s: None))
    assert out[0][:2] == ("processing", "P1")
    stage, pid, clips = out[-1]
    assert stage == "ready" and len(clips) == 1
    c = clips[0]
    assert c["source_kind"] == "raw_cut" and (c["start_s"], c["end_s"]) == (2.0, 5.0)
    assert abs(render.probe(c["file_path"])["duration"] - 3.0) < 0.2
    assert "00:00:00,100 --> 00:00:01,000\nhello there" in c["subtitles"]


def test_stalled_project_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("OPUSCLIP_API_KEY", "k")
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResp({"id": "P2"}))
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp({"id": "P2", "stage": "STALLED"}))
    gen = opusclip.run_live("https://youtube.com/watch?v=x", None, tmp_path, sleep=lambda s: None)
    assert next(gen)[0] == "processing"
    try:
        next(gen)
        raise AssertionError("expected OpusError")
    except opusclip.OpusError as e:
        assert "STALLED" in str(e)


def test_monthly_cap_message():
    try:
        opusclip._check(FakeResp({"code": "API_MONTHLY_CAP_REACHED"}, 403))
    except opusclip.OpusError as e:
        assert "monthly API cap" in str(e)
