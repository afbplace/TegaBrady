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
  approved fingerprint. Only a **Failed** post can be retried, and it gets a new request
  ID. Pending, Published and "NOT live: action needed" posts are never re-sent.
  Upload-Post's `Idempotency-Key` adds a second layer of protection.
- **"Published" means confirmed:** a platform shows Published only when the provider
  response says success **and** returns a post ID or URL. Otherwise it stays
  Pending (use "Refresh status") or Failed.
- **Credentials:** keys live in `clipper/.env` (git-ignored) and are read server-side only.
  Social accounts are linked through the provider's official OAuth. No social passwords
  are ever stored.

## Accounts and keys you need
Prices and limits below come from the providers' official docs as of 2026-11-05.

| # | Account | Why | Cost |
|---|---------|-----|------|
| 1 | **OpusClip** on **Pro (Beta), Max or Business** (API access is only on these plans) | Candidate clips | Plan price is on opus.pro/pricing. API use: 1 credit = 1 source minute, **10-credit minimum per API project**. Pro Beta and Max include **900 credits (15 h) per month**; past that the API returns 403 until the 1st (UTC). 30 requests/min, 4 projects at once |
| 2 | **Upload-Post Basic** or higher (TikTok returns 403 on Free) | Reels, TikTok and Shorts in one API | **$24/mo**, or **$16/mo billed yearly ($192)**. Unlimited uploads, 5 profiles |
| 3 | **Instagram Professional account** (Creator or Business) | Reels publishing | Free |
| 4 | **TikTok account** | Target | Free. Hard cap of 15 posts/day |
| 5 | **YouTube channel** | Shorts target | Free. Hard cap of 30 posts/day. No Google Cloud setup needed; Upload-Post uses its own quota |

### Steps
1. **OpusClip:** subscribe to Pro (Beta) or Max at opus.pro. Copy the API key from the
   bottom-left corner of clip.opus.pro/dashboard into `OPUSCLIP_API_KEY`. If you belong to
   more than one OpusClip organization, also set `OPUSCLIP_ORG_ID`.
2. **Upload-Post:** sign up at upload-post.com and choose Basic. Create an API key in the
   dashboard and put it in `UPLOAD_POST_API_KEY`.
3. In Upload-Post **Manage Users**, create a profile (for example `peezy`) and put that name in
   `UPLOAD_POST_USER`. Connect Instagram, TikTok and YouTube to the profile. Each one opens
   that platform's own OAuth login. If Instagram is a personal account, first switch it to
   Creator or Business in the Instagram app.
4. Restart `python app.py`. Click **Check connections**. It is read-only: it validates both keys
   and lists which platforms are connected or need reconnecting. It posts nothing and costs no credits.
5. **First live test:** set `YOUTUBE_PRIVACY=private` and publish one throwaway video to
   YouTube only. Confirm the status row matches what you see on YouTube, then remove the
   setting.

## How live mode behaves
- **OpusClip:** the app uploads your file (or passes your URL) and polls the project every
  30 s until its stage is `COMPLETE`.
  - **Uploaded sources:** each clip is cut from *your* original file at OpusClip's timestamps,
    so there are no OpusClip overlays.
  - **URL sources:** the app downloads OpusClip's rendered clip, which may already have
    OpusClip captions on it (marked "OpusClip render"). Clear the subtitle box if they double
    up, or set `OPUSCLIP_BRAND_TEMPLATE_ID` to a template without captions.
  - **Subtitles:** pre-filled as timed SRT from OpusClip's word-level transcript. Edit them freely.
  - **AI text:** OpusClip's AI clip titles and hashtags are only labels in the picker. They are
    never put into your captions, and the AI "auto hook" overlay is switched off.
- **Upload-Post:** one async upload per publish.
  - **Duplicates:** the app creates its own `request_id` and `Idempotency-Key` and saves them
    *before* sending. If the connection drops, nothing is re-sent; the status check finds out
    what happened.
  - **TikTok:** posts with `DIRECT_POST` and `disable_inbox_fallback=true`, so a daily-cap hit
    fails visibly instead of silently landing in your TikTok drafts. If it lands in drafts
    anyway, the row shows **NOT live: action needed**.
  - **Status updates:** pending posts are re-checked about every 30 s. **Published** needs a
    post link or post ID from the provider. TikTok can take minutes, sometimes hours under
    moderation, to release the public link, and the row stays Pending until then.

## Platform specs the renderer targets
Output is 1080×1920 (9:16), H.264 High at 30 fps with yuv420p, AAC 48 kHz, and `+faststart`.
Renders must be **3–180 s**:
- YouTube treats vertical uploads of 3 minutes or less as Shorts.
- TikTok allows 3–600 s via the API.
- Instagram Reels allow 3 s–15 min, up to 300 MB.

Titles are capped at 100 characters (YouTube) and captions at 2,200 (Instagram).
Subtitles sit about 420 px above the bottom edge, clear of the platforms' on-screen buttons.

## Alternatives considered
- **Ayrshare:** mature, but about $149/mo or more for video and it needs a public media URL.
- **Zernio (formerly Late):** cheaper per account, but needs a presigned upload step. Only
  `publisher.py` would change.
