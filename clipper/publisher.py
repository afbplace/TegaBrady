"""Publishing via Upload-Post (one API for Instagram Reels, TikTok, YouTube Shorts).

LIVE mode requires UPLOAD_POST_API_KEY and UPLOAD_POST_USER (the profile name
your social accounts are linked to through Upload-Post's official OAuth flow).
Field names follow docs.upload-post.com as summarised on 2026-11-05 (the docs
host was not reachable from the build environment). Re-check against the
live docs before the first real post; see SETUP.md.

A post is reported PUBLISHED only when the provider's response for that platform
says success AND gives a post id or URL. Anything else stays pending/failed.
MOCK mode never contacts any network and its results are labelled MOCK.
"""
import os

import requests

BASE = os.environ.get("UPLOAD_POST_BASE_URL", "https://api.upload-post.com/api")
PLATFORMS = ("instagram", "tiktok", "youtube")
TIMEOUT = 600


class PublishError(RuntimeError):
    pass


def mode():
    return "live" if (os.environ.get("UPLOAD_POST_API_KEY") and os.environ.get("UPLOAD_POST_USER")) else "mock"


def provider_name():
    return "upload-post" if mode() == "live" else "mock"


def _headers():
    return {"Authorization": f"Apikey {os.environ['UPLOAD_POST_API_KEY']}"}


def interpret(platform, result):
    """Map one provider per-platform result to (status, post_id, url, error)."""
    if not isinstance(result, dict):
        return "pending", None, None, None
    post_id = result.get("post_id") or result.get("video_id") or result.get("publish_id") or result.get("id")
    url = result.get("url") or result.get("post_url")
    if result.get("success") is True and (post_id or url):
        return "published", post_id, url, None
    if result.get("success") is False or result.get("error"):
        return "failed", post_id, url, str(result.get("error") or "provider reported failure")
    return "pending", post_id, url, None


def submit(video_path, platforms, title, caption, external_id, tiktok_privacy="PUBLIC_TO_EVERYONE",
           youtube_privacy="public"):
    """Submit one upload covering several platforms. Returns (request_id, {platform: result})."""
    data = [("user", os.environ["UPLOAD_POST_USER"]), ("title", title or caption[:100]),
            ("description", caption), ("async_upload", "true"), ("external_id", external_id),
            ("instagram_title", caption), ("media_type", "REELS"), ("share_to_feed", "true"),
            ("privacy_level", tiktok_privacy), ("tiktok_title", caption),
            ("youtube_title", title), ("youtube_description", caption), ("privacyStatus", youtube_privacy)]
    data += [("platform[]", p) for p in platforms]
    with open(video_path, "rb") as f:
        resp = requests.post(f"{BASE}/upload", headers=_headers(), data=data,
                             files={"video": (os.path.basename(video_path), f, "video/mp4")},
                             timeout=TIMEOUT)
    if resp.status_code >= 400:
        raise PublishError(f"Upload-Post HTTP {resp.status_code}: {resp.text[:500]}")
    body = resp.json()
    return body.get("request_id"), body.get("results") or {}, body


def status(request_id):
    resp = requests.get(f"{BASE}/uploadposts/status", headers=_headers(),
                        params={"request_id": request_id}, timeout=60)
    if resp.status_code >= 400:
        raise PublishError(f"Upload-Post status HTTP {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    return body.get("results") or {}, body
