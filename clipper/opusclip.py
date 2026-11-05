"""OpusClip integration: LIVE client + clearly labelled MOCK.

LIVE mode requires OPUSCLIP_API_KEY. Endpoint paths below come from OpusClip's
API reference (help.opus.pro/api-reference) as summarised by search results on
2026-11-05; the docs host was not reachable from the build environment, so the
response field mapping is defensive and MUST be re-checked against the live
docs on first real use (see SETUP.md).

MOCK mode (no key): cuts evenly spaced segments from your uploaded file with
FFmpeg. Mock clips are labelled MOCK everywhere in the UI. They are not
AI-selected highlights.
"""
import os
import time
from pathlib import Path

import requests

import render

BASE = os.environ.get("OPUSCLIP_BASE_URL", "https://api.opus.pro/api")
TIMEOUT = 60


class OpusError(RuntimeError):
    pass


def mode():
    return "live" if os.environ.get("OPUSCLIP_API_KEY") else "mock"


def _headers():
    h = {"Authorization": f"Bearer {os.environ['OPUSCLIP_API_KEY']}"}
    if os.environ.get("OPUSCLIP_ORG_ID"):
        h["x-opus-org-id"] = os.environ["OPUSCLIP_ORG_ID"]
    return h


def _check(resp):
    if resp.status_code >= 400:
        raise OpusError(f"OpusClip HTTP {resp.status_code}: {resp.text[:400]}")
    return resp.json() if resp.content else {}


# ------------------------------------------------------------------ LIVE
def upload_file(path):
    """Upload a local file via OpusClip's signed resumable upload; returns uploadId."""
    link = _check(requests.post(f"{BASE}/upload-links", headers=_headers(), json={}, timeout=TIMEOUT))
    url, upload_id = link.get("url"), link.get("uploadId")
    if not url or not upload_id:
        raise OpusError(f"Unexpected upload-links response: {link}")
    start = requests.post(url, headers={"x-goog-resumable": "start"}, timeout=TIMEOUT)
    session = start.headers.get("Location")
    if not session:
        raise OpusError(f"Upload session not started (HTTP {start.status_code})")
    with open(path, "rb") as f:
        put = requests.put(session, data=f, timeout=None)
    if put.status_code >= 400:
        raise OpusError(f"Upload failed HTTP {put.status_code}: {put.text[:300]}")
    return upload_id


def create_project(video_ref):
    body = {"videoUrl": video_ref,
            "curationPref": {"clipDurations": [[15, 90]], "genre": "Auto"}}
    data = _check(requests.post(f"{BASE}/clip-projects", headers=_headers(), json=body, timeout=TIMEOUT))
    pid = data.get("projectId") or data.get("id")
    if not pid:
        raise OpusError(f"No project id in response: {data}")
    return pid


def fetch_clips(project_id):
    data = _check(requests.get(
        f"{BASE}/exportable-clips", headers=_headers(), timeout=TIMEOUT,
        params={"q": "findByProjectId", "projectId": project_id, "pageSize": 50}))
    items = data.get("data") if isinstance(data, dict) else data
    if isinstance(items, dict):
        items = items.get("list") or items.get("items") or []
    out = []
    for c in items or []:
        out.append({
            "opus_clip_id": str(c.get("id")),
            "title": c.get("title") or c.get("name") or "",
            "start_s": _num(c, "startSec", "start", "startTime"),
            "end_s": _num(c, "endSec", "end", "endTime"),
            "score": _num(c, "viralityScore", "score"),
            "transcript": c.get("transcript") or c.get("text") or "",
            "remote_url": c.get("uriForExport") or c.get("uriForPreview") or c.get("videoUrl") or "",
        })
    return out


def _num(d, *keys):
    for k in keys:
        if d.get(k) is not None:
            try:
                return float(d[k])
            except (TypeError, ValueError):
                pass
    return None


def download(url, dest):
    with requests.get(url, stream=True, timeout=TIMEOUT) as r:
        if r.status_code >= 400:
            raise OpusError(f"Clip download failed HTTP {r.status_code}")
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def run_live(source_url, source_file, clip_dir, poll_every=20, max_wait=3 * 3600):
    ref = upload_file(source_file) if source_file else source_url
    pid = create_project(ref)
    yield ("processing", pid, None)
    deadline = time.time() + max_wait
    while time.time() < deadline:
        clips = fetch_clips(pid)
        if clips:
            for i, c in enumerate(clips):
                if c["remote_url"]:
                    dest = Path(clip_dir) / f"opus_{pid}_{i}.mp4"
                    download(c["remote_url"], dest)
                    c["file_path"] = str(dest)
            yield ("ready", pid, clips)
            return
        time.sleep(poll_every)
    raise OpusError("Timed out waiting for OpusClip clips")


# ------------------------------------------------------------------ MOCK
def run_mock(source_url, source_file, clip_dir, n=4):
    if not source_file:
        raise OpusError("MOCK mode can't fetch remote URLs. Upload the video file "
                        "or set OPUSCLIP_API_KEY for live clipping.")
    info = render.probe(source_file)
    dur = info["duration"]
    seg = min(30.0, max(2.0, dur / n))
    clips = []
    for i in range(n):
        start = i * (dur / n)
        end = min(dur, start + seg)
        if end - start < 1:
            break
        dest = Path(clip_dir) / f"mock_{Path(source_file).stem}_{i}.mp4"
        render.cut_segment(source_file, start, end, dest)
        clips.append({"opus_clip_id": f"mock-{i}", "title": f"MOCK segment {i + 1}",
                      "start_s": round(start, 2), "end_s": round(end, 2), "score": None,
                      "transcript": "", "remote_url": "", "file_path": str(dest)})
    yield ("ready", "mock", clips)
