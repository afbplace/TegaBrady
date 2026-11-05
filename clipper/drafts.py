"""Draft hooks, titles and captions ONLY from the creator's own talking points.

Deliberately deterministic (no AI model): every word of substance in the output
comes from text the creator typed. The only additions are neutral formatting
(numbering, a source credit line, and hashtags the creator supplied). This
guarantees no political facts or opinions are invented on the creator's behalf.
"""
import re

YOUTUBE_TITLE_MAX = 100       # YouTube rejects titles over 100 characters
CAPTION_MAX = 2200            # Instagram caption limit (TikTok's is larger)


def split_points(talking_points: str):
    """One talking point per non-empty line (bullets stripped)."""
    pts = []
    for line in (talking_points or "").splitlines():
        line = re.sub(r"^\s*([-*•]|\d+[.)])\s*", "", line).strip()
        if line:
            pts.append(line)
    return pts


def _first_sentence(text: str):
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return (m.group(1) if m else text).strip()


def _trim_words(text: str, max_chars: int):
    if len(text) <= max_chars:
        return text
    cut = text[: max_chars - 1].rsplit(" ", 1)[0].rstrip(",;:-")
    return cut + "…"


def normalize_hashtags(raw: str):
    tags = []
    for tok in re.split(r"[\s,]+", raw or ""):
        tok = tok.strip().lstrip("#")
        tok = re.sub(r"[^\w]", "", tok)
        if tok and ("#" + tok).lower() not in [t.lower() for t in tags]:
            tags.append("#" + tok)
    return tags


def draft(talking_points: str, hashtags: str = "", source_credit: str = ""):
    """Return editable draft options. Empty talking points -> empty drafts."""
    pts = split_points(talking_points)
    tags = normalize_hashtags(hashtags)
    if not pts:
        return {"hooks": [], "titles": [], "captions": [],
                "note": "Add your talking points first. Nothing is drafted without them."}

    first = _first_sentence(pts[0])
    hooks = []
    for p in pts[:3]:
        h = _trim_words(_first_sentence(p), 90)
        if h not in hooks:
            hooks.append(h)

    titles = []
    for cand in (first, f"Peezy Report: {first}", pts[0]):
        t = _trim_words(cand, YOUTUBE_TITLE_MAX)
        if t not in titles:
            titles.append(t)

    tag_line = " ".join(tags)
    credit = f"Source: {source_credit.strip()}" if source_credit.strip() else ""

    def build(body):
        parts = [body]
        if credit:
            parts.append(credit)
        if tag_line:
            parts.append(tag_line)
        return _trim_words("\n\n".join(parts), CAPTION_MAX)

    captions = [
        build("\n".join(pts)),
        build("\n".join(f"{i}. {p}" for i, p in enumerate(pts, 1))),
        build(first),
    ]
    # de-dupe while keeping order
    captions = list(dict.fromkeys(captions))
    return {"hooks": hooks, "titles": titles, "captions": captions,
            "note": "Drafted only from your talking points. Edit freely before approving."}
