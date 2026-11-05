# Peezy Report Clipper: setup and accounts

A local dashboard that runs on `http://127.0.0.1:5050` only (it is never exposed publicly).
The workflow is: source video → OpusClip candidate clips → you pick clips and add
talking points and a reaction → drafts built from your words → FFmpeg renders a
1080×1920 video with subtitles → you preview and approve → publish to Reels, TikTok
and Shorts.

## Run it

```bash
cd clipper
pip install -r requirements.txt     # also needs ffmpeg + ffprobe on PATH (with libass)
cp .env.example .env                # optional: fill in keys later
python app.py
python -m pytest -q tests           # 12 tests, all offline
```

With no keys set, both integrations run in **MOCK** mode and are labelled that way everywhere:
- **OpusClip MOCK** cuts evenly spaced segments from an *uploaded* file with FFmpeg.
  These are not AI-picked highlights. A URL-only source fails with a clear message in mock mode.
- **Publishing MOCK** posts nothing. Rows show "MOCK: not posted".

## How it protects you
- **Rights:** every source needs the "I own / am authorized" checkbox.
- **No invented content:** hooks, titles and captions are built only from your talking
  points (plus your hashtags and the source URL as a credit). No AI writes opinions or facts.
- **Approval:** you can approve only after a render, with both "watched the video" and
  "reviewed the title/caption" ticked. Approval is tied to a fingerprint of the exact
  video file, title and caption. Any edit or re-render revokes it.
- **Duplicate protection:** the database allows only one post per platform for each
  approved fingerprint. A failed post can be retried. A post whose result is
  *unknown* (network dropped after sending) cannot be retried until you check the
  provider dashboard.
- **"Published" means confirmed:** a platform shows Published only when the provider
  response says success **and** returns a post ID or URL. Otherwise it stays
  Pending (use "Refresh status") or Failed.
- **Credentials:** keys live in `clipper/.env` (git-ignored) and are read server-side only.
  Social accounts are linked through the provider's official OAuth. No social passwords
  are ever stored.

## Accounts and keys you need

| # | Account | Why | Cost (unverified, see note) |
|---|---------|-----|-----------------------------|
| 1 | **OpusClip** on a plan with API access (Pro Beta, Max, or Business) | Candidate clips | Plan subscription. API use is billed at 1 credit per source minute, 10-credit minimum per project. The plan includes about 900 credits/month |
| 2 | **Upload-Post** on a paid plan (Basic or higher; TikTok is not available on Free) | One API for Reels, TikTok and Shorts | About $16/mo billed annually or $24/mo monthly |
| 3 | **Instagram Professional account** (Business or Creator) | Required for Reels publishing via API | Free |
| 4 | **TikTok account** | Target account | Free |
| 5 | **YouTube channel** (Google account) | Shorts target | Free |

### Steps
1. **OpusClip:** sign up at opus.pro and choose a plan that includes API access
   (or request access at opus.pro/contact-api). Copy the API key from the bottom-left
   of the dashboard into `OPUSCLIP_API_KEY`. Add `OPUSCLIP_ORG_ID` if the API asks for one.
2. **Upload-Post:** create an account at upload-post.com, pick a paid plan, and create an
   API key in the dashboard → `UPLOAD_POST_API_KEY`.
3. In Upload-Post, create a **profile** (for example `peezy`) → `UPLOAD_POST_USER`. From that
   profile, connect Instagram, TikTok and YouTube. Each opens the platform's own OAuth
   login. If Instagram is still a personal account, first switch it to Creator or
   Business in the Instagram app.
4. Restart `python app.py`. The header badges change from MOCK to LIVE.
5. **First live test:** publish one throwaway video to a single platform. Watch the
   status row and compare it with the post on the platform before going wider.

## Platform specs the renderer targets
The output is 1080×1920 (9:16), H.264 High at 30 fps with yuv420p, AAC 48 kHz, and `+faststart`.
Renders are capped at **180 s**:
- YouTube treats vertical or square uploads of 3 minutes or less as Shorts. There is no API flag for this.
- TikTok's API default limit is 3 minutes.
- Reels allow longer.

Subtitles sit about 420 px above the bottom edge, clear of the platforms' on-screen buttons.

## ⚠️ Verify before going live
The OpusClip and Upload-Post doc sites were **blocked from the build environment** on
2026-11-05. The endpoints and field names below come from search-engine summaries of
their official docs, so they are unverified. Before the first live use, check them against:
- `opusclip.py`: `POST /api/upload-links`, `POST /api/clip-projects` (`videoUrl`, `curationPref`),
  `GET /api/exportable-clips?q=findByProjectId&projectId=…`. The response fields for title,
  start/end, score and download URL are mapped defensively. Confirm them at
  help.opus.pro/api-reference.
- `publisher.py`: `POST /api/upload` (multipart, `Authorization: Apikey …`, `platform[]`,
  `privacy_level`, `privacyStatus`, `media_type=REELS`) and
  `GET /api/uploadposts/status?request_id=…`. Confirm them at docs.upload-post.com/api/upload-video.

The status logic never trusts an ambiguous response. If a field name is wrong, the post
shows as Pending or Failed, never as falsely Published.

## Alternatives considered
- **Ayrshare:** mature, with built-in duplicate rejection, but about $149/mo or more for video,
  and it needs a public media URL (an extra upload step).
- **Zernio (formerly Late):** cheapest, about $6/mo per account beyond 2 free, but it needs
  a presigned upload step. You could swap it in by rewriting `publisher.py` only.
