"""OpusClip integration: LIVE client + clearly labelled MOCK.

Verified against OpusClip's official API reference and OpenAPI spec
(help.opus.pro/api-reference, openapi.json) on 2026-11-05:
  POST /api/upload-links            body {"video": {"usecase": "LocalUpload"}} -> {url, uploadId}
  POST <url>  x-goog-resumable:start -> Location header; PUT file there
  POST /api/clip-projects           {videoUrl (URL or uploadId), curationPref, importPref, brandTemplateId}
  GET  /api/clip-projects/{id}      -> stage: PENDING|QUEUED|IMPORT|CURATE|REFINE|RENDER|UPLOAD|COMPLETE|STALLED
  GET  /api/exportable-clips?q=findByProjectId&projectId=..  -> [ {id, title, text, durationMs,
                                     timeRanges, uriForPreview, uriForExport, ...} ]
  GET  /api/transcripts?q=findByProjectId&projectId=..       -> {data: [{start,end,text,words:[{word,start,end}]}]}
Limits: 30 req/min per key; API projects cost >= 10 credits; Pro Beta/Max cap 900 credits/month.

OpusClip's AI-written clip titles/descriptions/hashtags are used ONLY as labels in the
clip picker. They are never copied into your post captions.

MOCK mode (no key): cuts evenly spaced segments from your uploaded file with FFmpeg.
"""
import os
import time
from pathlib import Path

import requests

import render

BASE = os.environ.get("OPUSCLIP_BASE_URL", "https://api.opus.pro/api")
TIMEOUT = 60
POLL_SECONDS = 30            # well under the 30 requests/minute limit
DONE, STALLED = "COMPLETE", "STALLED"


class OpusError(RuntimeError):
    pass


def mode():
    return "live" if os.environ.get("OPUSCLIP_API_KEY") else "mock"


def _headers(json_body=True):
    h = {"Authorization": f"Bearer {os.environ['OPUSCLIP_API_KEY']}", "Accept": "application/json"}
    if json_body:
        h["Content-Type"] = "application/json"
    if os.environ.get("OPUSCLIP_ORG_ID"):
        h["x-opus-org-id"] = os.environ["OPUSCLIP_ORG_ID"]
    return h


def _check(resp):
    if resp.status_code == 403 and "API_MONTHLY_CAP_REACHED" in resp.text:
        raise OpusError("OpusClip monthly API cap reached (900 credits on Pro Beta/Max). "
                        "Resets on the 1st of the month (UTC).")
    if resp.status_code == 429:
        raise OpusError("OpusClip rate/concurrency limit hit (429). Wait a minute and resubmit.")
    if resp.status_code >= 400:
        raise OpusError(f"OpusClip HTTP {resp.status_code}: {resp.text[:400]}")
    return resp.json() if resp.content else {}


# ------------------------------------------------------------------ LIVE
def check_connection():
    """Read-only key check (lists brand templates; creates nothing, costs no credits)."""
    resp = requests.get(f"{BASE}/brand-templates", headers=_headers(False), timeout=TIMEOUT)
    _check(resp)
    return {"ok": True}


def upload_file(path):
    """Upload a local file via OpusClip's signed resumable upload; returns uploadId."""
    link = _check(requests.post(f"{BASE}/upload-links", headers=_headers(),
                                json={"video": {"usecase": "LocalUpload"}}, timeout=TIMEOUT))
    url, upload_id = link.get("url"), link.get("uploadId")
    if not url or not upload_id:
        raise OpusError(f"Unexpected upload-links response: {str(link)[:300]}")
    start = requests.post(url, headers={"x-goog-resumable": "start", "Content-Length": "0"},
                          data=b"", timeout=TIMEOUT)
    session = start.headers.get("Location") or start.headers.get("location")
    if not session:
        raise OpusError(f"Upload session not started (HTTP {start.status_code})")
    with open(path, "rb") as f:
        put = requests.put(session, data=f, headers={"Content-Type": "application/octet-stream"},
                           timeout=None)
    if put.status_code >= 400:
        raise OpusError(f"Upload failed HTTP {put.status_code}: {put.text[:300]}")
    return upload_id


def create_project(video_ref):
    body = {"videoUrl": video_ref,
            "curationPref": {"clipDurations": [[0, 90]], "genre": "Auto", "enableAutoHook": False},
            "importPref": {"sourceLang": os.environ.get("OPUSCLIP_SOURCE_LANG", "auto")}}
    if os.environ.get("OPUSCLIP_BRAND_TEMPLATE_ID"):
        body["brandTemplateId"] = os.environ["OPUSCLIP_BRAND_TEMPLATE_ID"]
    data = _check(requests.post(f"{BASE}/clip-projects", headers=_headers(), json=body, timeout=TIMEOUT))
    pid = data.get("projectId") or data.get("id")
    if not pid:
        raise OpusError(f"No project id in response: {str(data)[:300]}")
    return pid


def get_project(project_id):
    return _check(requests.get(f"{BASE}/clip-projects/{project_id}", headers=_headers(False), timeout=TIMEOUT))


def _ranges_seconds(clip):
    """timeRanges: [[start, end], ...]. The spec says seconds but its example is in
    milliseconds, so pick whichever unit matches durationMs."""
    ranges = [r for r in (clip.get("timeRanges") or []) if isinstance(r, (list, tuple)) and len(r) == 2]
    if not ranges:
        return []
    span = sum(float(e) - float(s) for s, e in ranges)
    dur_ms = clip.get("durationMs")
    if dur_ms and abs(span - float(dur_ms)) <= abs(span * 1000 - float(dur_ms)):
        return [(float(s) / 1000, float(e) / 1000) for s, e in ranges]
    return [(float(s), float(e)) for s, e in ranges]


def fetch_clips(project_id):
    out, page = [], 1
    while True:
        items = _check(requests.get(
            f"{BASE}/exportable-clips", headers=_headers(False), timeout=TIMEOUT,
            params={"q": "findByProjectId", "projectId": project_id, "pageNum": page, "pageSize": 50}))
        if isinstance(items, dict):  # tolerate a wrapped shape
            items = items.get("data") or items.get("list") or []
        for c in items:
            ranges = _ranges_seconds(c)
            out.append({
                "opus_clip_id": str(c.get("id")),
                "title": c.get("title") or "",
                "start_s": ranges[0][0] if ranges else None,
                "end_s": ranges[-1][1] if ranges else None,
                "ranges": ranges,
                "score": None,          # the API does not expose a virality score
                "transcript": c.get("text") or "",
                "remote_url": c.get("uriForExport") or c.get("uriForPreview") or "",
            })
        if len(items) < 50:
            return out
        page += 1


def fetch_words(project_id):
    data = _check(requests.get(f"{BASE}/transcripts", headers=_headers(False), timeout=TIMEOUT,
                               params={"q": "findByProjectId", "projectId": project_id}))
    words = []
    for para in data.get("data") or []:
        for w in para.get("words") or []:
            if w.get("word") is not None and w.get("start") is not None:
                words.append((float(w["start"]), float(w["end"]), str(w["word"]).strip()))
    return words


def srt_for_ranges(words, ranges, max_words=6, max_gap=0.8):
    """Build clip-relative SRT from source-timeline word timings."""
    def fmt(t):
        ms = int(round(max(t, 0) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    cues, offset = [], 0.0
    for rs, re_ in ranges:
        cur = []
        for ws, we, w in words:
            if ws >= rs and we <= re_ + 0.05 and w:
                ws_rel, we_rel = ws - rs + offset, min(we, re_) - rs + offset
                if cur and (len(cur) >= max_words or ws_rel - cur[-1][1] > max_gap):
                    cues.append(cur)
                    cur = []
                cur.append((ws_rel, we_rel, w))
        if cur:
            cues.append(cur)
        offset += re_ - rs
    return "\n\n".join(f"{i}\n{fmt(c[0][0])} --> {fmt(c[-1][1])}\n{' '.join(w for _, _, w in c)}"
                       for i, c in enumerate(cues, 1))


def download(url, dest):
    with requests.get(url, stream=True, timeout=TIMEOUT) as r:
        if r.status_code >= 400:
            raise OpusError(f"Clip download failed HTTP {r.status_code}")
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def run_live(source_url, source_file, clip_dir, poll_every=POLL_SECONDS, max_wait=4 * 3600, sleep=time.sleep):
    ref = upload_file(source_file) if source_file else source_url
    pid = create_project(ref)
    yield ("processing", pid, None)
    deadline = time.time() + max_wait
    while True:
        proj = get_project(pid)
        stage = proj.get("stage")
        if stage == DONE:
            break
        if stage == STALLED or proj.get("error"):
            raise OpusError(f"OpusClip project {pid} {stage}: {proj.get('error') or 'stalled'}")
        if time.time() > deadline:
            raise OpusError(f"Timed out waiting for OpusClip project {pid} (last stage {stage})")
        sleep(poll_every)
    clips = fetch_clips(pid)
    try:
        words = fetch_words(pid)
    except OpusError:
        words = []
    for i, c in enumerate(clips):
        dest = Path(clip_dir) / f"opus_{pid}_{i}.mp4"
        if source_file and len(c["ranges"]) == 1:
            # Cut the raw moment from YOUR file: no OpusClip captions/overlays to double up.
            render.cut_segment(source_file, c["ranges"][0][0], c["ranges"][0][1], dest)
            c["source_kind"] = "raw_cut"
        elif c["remote_url"]:
            download(c["remote_url"], dest)
            c["source_kind"] = "opus_render"
        else:
            continue
        c["file_path"] = str(dest)
        c["subtitles"] = srt_for_ranges(words, c["ranges"]) if words and c["ranges"] else ""
    yield ("ready", pid, clips)


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
                      "transcript": "", "remote_url": "", "file_path": str(dest),
                      "source_kind": "mock", "subtitles": ""})
    yield ("ready", "mock", clips)
