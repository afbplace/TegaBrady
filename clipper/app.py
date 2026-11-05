#!/usr/bin/env python3
"""Peezy Report clipper - local draft, preview, approve and publish dashboard.

Run:  python app.py   (serves on http://127.0.0.1:5050 only)
"""
import datetime
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from pathlib import Path

import requests
from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

import drafts
import opusclip
import publisher
import render
from db import DB, dumps

ALLOWED_VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
EDITABLE = ("talking_points", "layout", "subtitles", "hook", "title", "caption", "hashtags")
LAYOUTS = ("stack", "sequence", "clip_only")


def _load_dotenv(path):
    """Minimal .env loader so keys stay in a git-ignored file, server-side."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def create_app(data_dir=None, run_async=True):
    here = Path(__file__).resolve().parent
    _load_dotenv(here / ".env")
    data = Path(data_dir or os.environ.get("CLIPPER_DATA_DIR", here / "data")).resolve()
    dirs = {k: data / k for k in ("sources", "clips", "reactions", "renders")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("CLIPPER_MAX_UPLOAD_MB", "2048")) * 1024 * 1024
    db = DB(data / "clipper.db")
    app.db = db

    def background(fn, *a):
        if run_async:
            threading.Thread(target=fn, args=a, daemon=True).start()
        else:
            fn(*a)

    def save_upload(fs, folder):
        name = secure_filename(fs.filename or "")
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED_VIDEO:
            abort(400, f"Unsupported file type {ext or '(none)'}; use {', '.join(sorted(ALLOWED_VIDEO))}")
        dest = dirs[folder] / f"{uuid.uuid4().hex[:10]}_{name}"
        fs.save(dest)
        try:
            render.probe(dest)
        except render.RenderError as e:
            dest.unlink(missing_ok=True)
            abort(400, str(e))
        return dest

    def rel(p):
        return str(Path(p).resolve().relative_to(data)) if p else None

    def fingerprint(v):
        raw = "|".join([v.get("output_sha256") or "", v.get("title") or "", v.get("caption") or ""])
        return hashlib.sha256(raw.encode()).hexdigest()

    def video_view(v):
        v = dict(v)
        clip = db.one("SELECT * FROM clips WHERE id=?", (v["clip_id"],))
        v["clip"] = clip_view(clip)
        v["output_url"] = f"/media/{rel(v['output_file'])}?v={(v['output_sha256'] or '')[:8]}" if v["output_file"] else None
        v["reaction_url"] = f"/media/{rel(v['reaction_file'])}" if v["reaction_file"] else None
        v["drafts"] = json.loads(v.pop("drafts_json") or "{}")
        for k in ("output_file", "reaction_file"):
            v[k] = bool(v[k])  # don't expose server paths
        v["approval_valid"] = bool(v["approved"]) and v["approved_fingerprint"] == fingerprint(v) \
            and v["render_status"] == "rendered"
        v["publications"] = db.all("SELECT id, platform, provider, is_mock, status, provider_post_id, post_url,"
                                   " error, updated_at FROM publications WHERE video_id=? ORDER BY platform, is_mock",
                                   (v["id"],))
        return v

    def clip_view(c):
        if not c:
            return None
        c = dict(c)
        c["url"] = f"/media/{rel(c['file_path'])}" if c["file_path"] else None
        c.pop("file_path", None)  # don't expose server paths
        return c

    # ------------------------------------------------------------ pages
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/media/<path:p>")
    def media(p):
        return send_from_directory(data, p, conditional=True)

    @app.get("/api/status")
    def status():
        return jsonify({"opusclip": opusclip.mode(), "publisher": publisher.mode(),
                        "provider": publisher.provider_name(), "platforms": publisher.PLATFORMS})

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    def err(e):
        return jsonify({"error": getattr(e, "description", str(e))}), e.code

    # ------------------------------------------------------------ projects / clips
    @app.post("/api/projects")
    def create_project():
        if request.form.get("rights_confirmed") != "true":
            abort(400, "Confirm you own or are authorized to use this video.")
        url = (request.form.get("source_url") or "").strip()
        fs = request.files.get("file")
        if not url and not (fs and fs.filename):
            abort(400, "Provide a video URL or upload a file.")
        if url and not url.startswith(("http://", "https://")):
            abort(400, "URL must start with http:// or https://")
        src = save_upload(fs, "sources") if fs and fs.filename else None
        m = opusclip.mode()
        pid = db.execute("INSERT INTO projects (source_url, source_file, rights_confirmed, opus_mode, status)"
                         " VALUES (?,?,1,?, 'submitted')", (url or None, str(src) if src else None, m))
        background(process_project, pid)
        return jsonify({"id": pid, "mode": m}), 201

    def process_project(pid):
        p = db.one("SELECT * FROM projects WHERE id=?", (pid,))
        runner = opusclip.run_live if p["opus_mode"] == "live" else opusclip.run_mock
        try:
            for stage, opus_id, clips in runner(p["source_url"], p["source_file"], dirs["clips"]):
                db.update("projects", pid, status=stage, opus_project_id=opus_id)
                for c in clips or []:
                    if not c.get("file_path"):
                        continue
                    db.execute("INSERT INTO clips (project_id, opus_clip_id, title, start_s, end_s, score,"
                               " transcript, file_path, remote_url, is_mock, source_kind, subtitles)"
                               " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                               (pid, c["opus_clip_id"], c["title"], c["start_s"], c["end_s"], c["score"],
                                c["transcript"], c["file_path"], c["remote_url"],
                                1 if p["opus_mode"] == "mock" else 0, c.get("source_kind"), c.get("subtitles") or ""))
        except Exception as e:  # surfaced in the UI
            db.update("projects", pid, status="failed", error=str(e)[:1000])

    @app.get("/api/projects")
    def list_projects():
        out = []
        for p in db.all("SELECT * FROM projects ORDER BY id DESC"):
            p["clips"] = [clip_view(c) for c in db.all("SELECT * FROM clips WHERE project_id=? ORDER BY id", (p["id"],))]
            p.pop("source_file", None)
            out.append(p)
        return jsonify(out)

    @app.post("/api/clips/<int:cid>/select")
    def select_clip(cid):
        c = db.one("SELECT * FROM clips WHERE id=?", (cid,)) or abort(404, "clip not found")
        if not c["file_path"]:  # raw DB row here, not clip_view
            abort(400, "This clip has no downloadable file yet.")
        db.update("clips", cid, selected=1)
        v = db.one("SELECT id FROM videos WHERE clip_id=?", (cid,))
        vid = v["id"] if v else db.execute(
            "INSERT INTO videos (clip_id, subtitles) VALUES (?,?)", (cid, c["subtitles"] or ""))
        return jsonify({"video_id": vid})

    # ------------------------------------------------------------ videos
    @app.get("/api/videos")
    def list_videos():
        return jsonify([video_view(v) for v in db.all("SELECT * FROM videos ORDER BY id DESC")])

    def get_video(vid):
        return db.one("SELECT * FROM videos WHERE id=?", (vid,)) or abort(404, "video not found")

    @app.get("/api/videos/<int:vid>")
    def one_video(vid):
        return jsonify(video_view(get_video(vid)))

    @app.post("/api/videos/<int:vid>")
    def edit_video(vid):
        get_video(vid)
        body = request.get_json(force=True) or {}
        fields = {k: str(body[k]) for k in EDITABLE if k in body}
        if "layout" in fields and fields["layout"] not in LAYOUTS:
            abort(400, "bad layout")
        if fields:
            # Any edit invalidates a previous approval.
            db.update("videos", vid, **fields, approved=0, approved_fingerprint=None, approved_at=None)
            if {"layout", "subtitles"} & fields.keys():
                db.update("videos", vid, render_status="draft")
        return jsonify(video_view(get_video(vid)))

    @app.post("/api/videos/<int:vid>/reaction")
    def upload_reaction(vid):
        get_video(vid)
        fs = request.files.get("file")
        if not fs or not fs.filename:
            abort(400, "No reaction file uploaded")
        dest = save_upload(fs, "reactions")
        db.update("videos", vid, reaction_file=str(dest), render_status="draft",
                  approved=0, approved_fingerprint=None, approved_at=None)
        return jsonify(video_view(get_video(vid)))

    @app.post("/api/videos/<int:vid>/drafts")
    def make_drafts(vid):
        v = get_video(vid)
        clip = db.one("SELECT c.*, p.source_url FROM clips c JOIN projects p ON p.id=c.project_id WHERE c.id=?",
                      (v["clip_id"],))
        d = drafts.draft(v["talking_points"], v["hashtags"], clip.get("source_url") or "")
        db.update("videos", vid, drafts_json=dumps(d))
        return jsonify(video_view(get_video(vid)))

    @app.post("/api/videos/<int:vid>/render")
    def start_render(vid):
        v = get_video(vid)
        if v["render_status"] == "rendering":
            abort(409, "Already rendering")
        db.update("videos", vid, render_status="rendering", render_error=None,
                  approved=0, approved_fingerprint=None, approved_at=None)
        background(do_render, vid)
        return jsonify(video_view(get_video(vid))), 202

    def do_render(vid):
        v = get_video(vid)
        clip = db.one("SELECT * FROM clips WHERE id=?", (v["clip_id"],))
        out = dirs["renders"] / f"video_{vid}.mp4"
        try:
            res = render.render(clip["file_path"], v["reaction_file"], v["layout"], v["subtitles"], out)
            db.update("videos", vid, output_file=str(out), output_sha256=res["sha256"], render_status="rendered")
        except Exception as e:
            db.update("videos", vid, render_status="failed", render_error=str(e)[:1500])

    @app.post("/api/videos/<int:vid>/approve")
    def approve(vid):
        v = get_video(vid)
        body = request.get_json(force=True) or {}
        if v["render_status"] != "rendered":
            abort(400, "Render and preview the video before approving.")
        if not (body.get("video_reviewed") and body.get("captions_reviewed")):
            abort(400, "Confirm you watched the final video AND reviewed the title/caption.")
        if not (v["caption"] or "").strip() or not (v["title"] or "").strip():
            abort(400, "Title and caption are required before approval.")
        if len(v["title"]) > drafts.YOUTUBE_TITLE_MAX:
            abort(400, f"Title is over {drafts.YOUTUBE_TITLE_MAX} characters (YouTube limit).")
        if len(v["caption"]) > drafts.CAPTION_MAX:
            abort(400, f"Caption is over {drafts.CAPTION_MAX} characters (Instagram limit).")
        db.update("videos", vid, approved=1, approved_fingerprint=fingerprint(v),
                  approved_at=datetime.datetime.now().isoformat(timespec="seconds"))
        return jsonify(video_view(get_video(vid)))

    @app.post("/api/videos/<int:vid>/unapprove")
    def unapprove(vid):
        get_video(vid)
        db.update("videos", vid, approved=0, approved_fingerprint=None, approved_at=None)
        return jsonify(video_view(get_video(vid)))

    # ------------------------------------------------------------ publishing
    @app.post("/api/videos/<int:vid>/publish")
    def publish(vid):
        v = get_video(vid)
        view = video_view(v)
        if not view["approval_valid"]:
            abort(400, "Video is not approved (or changed since approval). Re-approve first.")
        body = request.get_json(force=True) or {}
        platforms = [p for p in body.get("platforms", []) if p in publisher.PLATFORMS]
        if not platforms:
            abort(400, "Choose at least one platform.")
        fp = view["approved_fingerprint"]
        is_mock = 1 if publisher.mode() == "mock" else 0
        claimed, skipped = [], {}
        for p in platforms:  # atomic claim per platform -> duplicate protection
            try:
                db.execute("INSERT INTO publications (video_id, platform, content_fingerprint, provider, is_mock, status)"
                           " VALUES (?,?,?,?,?, 'submitting')", (vid, p, fp, publisher.provider_name(), is_mock))
                claimed.append(p)
            except sqlite3.IntegrityError:
                row = db.one("SELECT * FROM publications WHERE content_fingerprint=? AND platform=? AND is_mock=?",
                             (fp, p, is_mock))
                if row["status"] == "failed":
                    db.update("publications", row["id"], status="submitting", error=None)
                    claimed.append(p)
                else:
                    skipped[p] = f"already {row['status']} - not posting again"
        if claimed:
            background(do_publish, vid, claimed, fp, is_mock)
        return jsonify({"submitted": claimed, "skipped": skipped, "video": video_view(get_video(vid))}), 202

    def pubrow(fp, p, is_mock):
        return db.one("SELECT * FROM publications WHERE content_fingerprint=? AND platform=? AND is_mock=?",
                      (fp, p, is_mock))

    def set_pub(fp, p, is_mock, **f):
        db.update("publications", pubrow(fp, p, is_mock)["id"], **f,
                  updated_at=utcnow().isoformat(timespec="seconds"))

    def do_publish(vid, platforms, fp, is_mock):
        v = get_video(vid)
        if is_mock:
            for p in platforms:
                set_pub(fp, p, 1, status="mock_published",
                        error="MOCK: nothing was posted. Add Upload-Post credentials to publish for real.")
            return
        req_id = publisher.new_request_id()
        for p in platforms:   # record our request id BEFORE sending, so a lost response is traceable
            set_pub(fp, p, 0, request_id=req_id)
        try:
            results, raw = publisher.submit(v["output_file"], platforms, v["title"], v["caption"],
                                            request_id=req_id, external_id=f"peezy-video-{vid}")
        except (requests.Timeout, requests.ConnectionError) as e:
            for p in platforms:   # don't re-send: the status check will tell us what happened
                set_pub(fp, p, 0, status="pending",
                        error=f"Connection dropped ({type(e).__name__}); checking with Upload-Post by request id.")
            return
        except Exception as e:
            for p in platforms:
                set_pub(fp, p, 0, status="failed", error=str(e)[:900])
            return
        for p in platforms:
            st, post_id, url, message = publisher.interpret(p, results.get(p))
            set_pub(fp, p, 0, status=st, provider_post_id=post_id, post_url=url,
                    error=message or ("Submitted; waiting for Upload-Post to report back." if st == "pending" else None),
                    raw_response=dumps(raw)[:20000])

    @app.post("/api/videos/<int:vid>/refresh")
    def refresh(vid):
        get_video(vid)
        rows = db.all("SELECT * FROM publications WHERE video_id=? AND is_mock=0 AND status='pending'"
                      " AND request_id IS NOT NULL", (vid,))
        now = utcnow()
        for req_id in {r["request_id"] for r in rows}:
            group = [r for r in rows if r["request_id"] == req_id]
            try:
                overall, results, raw = publisher.status(req_id)
            except Exception as e:
                for r in group:
                    db.update("publications", r["id"], error=f"Status check failed: {e}"[:900])
                continue
            for r in group:
                age = (now - datetime.datetime.fromisoformat(r["updated_at"].replace(" ", "T"))).total_seconds() \
                    if r["updated_at"] else 0
                if overall == "not_found":
                    if age > 600:   # Upload-Post never received it -> safe to retry
                        db.update("publications", r["id"], status="failed",
                                  error="Upload-Post has no record of this upload; nothing was posted. You can retry.")
                    continue
                res = results.get(r["platform"])
                if res is None and overall == "failed":
                    st, post_id, url, msg = "failed", None, None, (raw.get("message") or "Upload failed")
                else:
                    st, post_id, url, msg = publisher.interpret(r["platform"], res)
                db.update("publications", r["id"], status=st, provider_post_id=post_id or r["provider_post_id"],
                          post_url=url or r["post_url"], error=msg, raw_response=dumps(raw)[:20000])
        return jsonify(video_view(get_video(vid)))

    @app.get("/api/check")
    def check():
        out = {}
        for name, mod in (("opusclip", opusclip), ("publisher", publisher)):
            if mod.mode() == "mock":
                out[name] = {"mode": "mock", "detail": "No credentials set: MOCK mode."}
                continue
            try:
                out[name] = {"mode": "live", "ok": True, **mod.check_connection()}
            except Exception as e:
                out[name] = {"mode": "live", "ok": False, "detail": str(e)[:500]}
        return jsonify(out)

    return app


if __name__ == "__main__":
    port = int(os.environ.get("CLIPPER_PORT", "5050"))
    app = create_app()
    print(f"Peezy clipper on http://127.0.0.1:{port}  (OpusClip: {opusclip.mode().upper()}, "
          f"publishing: {publisher.mode().upper()})")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
