"""Publishing via Upload-Post (Instagram Reels, TikTok, YouTube Shorts in one API).

Verified against docs.upload-post.com on 2026-11-05:
  POST /api/upload  (multipart; header "Authorization: Apikey <key>", optional Idempotency-Key)
       user, platform[], video (file), title (required for YouTube), async_upload, request_id,
       external_id, instagram_title, media_type=REELS, share_to_feed, tiktok_title, post_mode,
       privacy_level, disable_inbox_fallback, youtube_title, youtube_description, privacyStatus
  GET  /api/uploadposts/status?request_id=..  -> {status, results: [{platform, success, status,
       url|post_url, post_id|video_id|platform_post_id|publish_id, error, skipped, fallback_to_inbox}]}
  GET  /api/uploadposts/me, GET /api/uploadposts/users   (read-only connection checks)

We send our own request_id up front (stored before the request goes out) plus an
Idempotency-Key, so a timed-out upload can be tracked instead of re-sent.

A platform is reported PUBLISHED only when the provider says it succeeded AND gives a post
link or post id. Anything else stays pending / failed / needs_action.
MOCK mode never contacts any network and its results are labelled MOCK.
"""
import os
import uuid

import requests

BASE = os.environ.get("UPLOAD_POST_BASE_URL", "https://api.upload-post.com/api")
PLATFORMS = ("instagram", "tiktok", "youtube")
TIMEOUT = 900


class PublishError(RuntimeError):
    pass


def mode():
    return "live" if (os.environ.get("UPLOAD_POST_API_KEY") and os.environ.get("UPLOAD_POST_USER")) else "mock"


def provider_name():
    return "upload-post" if mode() == "live" else "mock"


def new_request_id():
    return "peezy-" + uuid.uuid4().hex


def _headers():
    return {"Authorization": f"Apikey {os.environ['UPLOAD_POST_API_KEY']}"}


def _err_text(resp):
    try:
        b = resp.json()
        return str(b.get("message") or b.get("error") or b)[:500]
    except ValueError:
        return resp.text[:500]


def results_by_platform(results):
    """Upload responses use {platform: {...}}; status responses use [{platform, ...}]."""
    if isinstance(results, dict):
        return {k: v for k, v in results.items() if isinstance(v, dict)}
    out = {}
    for r in results or []:
        if isinstance(r, dict) and r.get("platform"):
            out[r["platform"]] = r
    return out


def interpret(platform, r):
    """Map one provider per-platform result to (status, post_id, url, message)."""
    if not isinstance(r, dict):
        return "pending", None, None, None
    url = r.get("url") or r.get("post_url")
    real_id = r.get("post_id") or r.get("video_id")
    any_id = real_id or r.get("platform_post_id") or r.get("publish_id") or r.get("container_id")
    err = r.get("error") or r.get("message") if r.get("success") is False else None
    pstat = (r.get("status") or "").lower()
    if r.get("skipped"):
        return "failed", None, None, f"Not connected in Upload-Post: {r.get('error') or platform}"
    if r.get("fallback_to_inbox"):
        return ("needs_action", any_id, url,
                "TikTok put this in your app drafts/inbox (daily cap). It is NOT live. Open TikTok to post it.")
    if pstat == "failed" or (r.get("success") is False and pstat not in ("retryable", "queued", "processing")):
        return "failed", any_id, url, str(err or "provider reported failure")[:900]
    if r.get("success") is True and pstat in ("", "completed"):
        confirmed = url or (real_id if platform in ("youtube", "instagram") else None) or \
            (r.get("post_id") if platform == "tiktok" else None)
        if confirmed:
            if not url and platform == "youtube":
                url = f"https://www.youtube.com/shorts/{real_id}"
            return "published", real_id or any_id, url, None
        return "pending", any_id, url, "Provider reports success; waiting for the public post link."
    return "pending", any_id, url, (f"Provider status: {pstat}" if pstat else None)


def submit(video_path, platforms, title, caption, request_id, external_id):
    """Submit one async upload covering several platforms. Returns (results_by_platform, raw)."""
    data = [("user", os.environ["UPLOAD_POST_USER"]), ("title", title), ("async_upload", "true"),
            ("request_id", request_id), ("external_id", external_id)]
    if "instagram" in platforms:
        data += [("instagram_title", caption), ("media_type", "REELS"), ("share_to_feed", "true")]
    if "tiktok" in platforms:
        data += [("tiktok_title", caption), ("post_mode", "DIRECT_POST"), ("disable_inbox_fallback", "true")]
        if os.environ.get("TIKTOK_PRIVACY_LEVEL"):          # omit -> TikTok account's own default
            data.append(("privacy_level", os.environ["TIKTOK_PRIVACY_LEVEL"]))
    if "youtube" in platforms:
        data += [("youtube_title", title), ("youtube_description", caption),
                 ("privacyStatus", os.environ.get("YOUTUBE_PRIVACY", "public"))]
    data += [("platform[]", p) for p in platforms]
    headers = {**_headers(), "Idempotency-Key": request_id}
    with open(video_path, "rb") as f:
        resp = requests.post(f"{BASE}/upload", headers=headers, data=data,
                             files={"video": (os.path.basename(video_path), f, "video/mp4")},
                             timeout=TIMEOUT)
    if resp.status_code >= 400:
        raise PublishError(f"Upload-Post HTTP {resp.status_code}: {_err_text(resp)}")
    body = resp.json()
    if body.get("success") is False:
        raise PublishError(f"Upload-Post rejected the upload: {_err_text(resp)}")
    return results_by_platform(body.get("results")), body


def status(request_id):
    """Returns (overall_status, results_by_platform, raw). overall 'not_found' => never received."""
    resp = requests.get(f"{BASE}/uploadposts/status", headers=_headers(),
                        params={"request_id": request_id}, timeout=60)
    if resp.status_code == 404:
        return "not_found", {}, {}
    if resp.status_code >= 400:
        raise PublishError(f"Upload-Post status HTTP {resp.status_code}: {_err_text(resp)}")
    body = resp.json()
    return (body.get("status") or ""), results_by_platform(body.get("results")), body


def check_connection():
    """Read-only: validates the key and reports which platforms the profile has connected."""
    me = requests.get(f"{BASE}/uploadposts/me", headers=_headers(), timeout=30)
    if me.status_code >= 400:
        raise PublishError(f"API key check failed (HTTP {me.status_code}): {_err_text(me)}")
    users = requests.get(f"{BASE}/uploadposts/users", headers=_headers(), timeout=30)
    if users.status_code >= 400:
        raise PublishError(f"Profile lookup failed (HTTP {users.status_code}): {_err_text(users)}")
    want = os.environ["UPLOAD_POST_USER"]
    prof = next((p for p in users.json().get("profiles", []) if p.get("username") == want), None)
    if not prof:
        raise PublishError(f"Upload-Post profile '{want}' not found. Check UPLOAD_POST_USER.")
    accts = prof.get("social_accounts") or {}
    platforms = {}
    for p in PLATFORMS:
        a = accts.get(p)
        if not a:
            platforms[p] = "not connected"
        elif isinstance(a, dict) and a.get("reauth_required"):
            platforms[p] = "reconnect required"
        else:
            name = (a.get("handle") or a.get("display_name")) if isinstance(a, dict) else None
            platforms[p] = f"connected{f' ({name})' if name else ''}"
    return {"plan": me.json().get("plan"), "platforms": platforms}
