import re

import drafts


def words(s):
    return set(re.findall(r"[a-z0-9']+", s.lower()))


def test_empty_points_drafts_nothing():
    d = drafts.draft("", "#x")
    assert d["hooks"] == d["titles"] == d["captions"] == []


def test_drafts_only_use_creators_words():
    pts = "- The council vote is Tuesday.\n- I want to hear from residents first"
    d = drafts.draft(pts, "PeezyReport, #news", "https://example.com/v")
    allowed = words(pts) | words("peezy report source https example com v peezyreport news 1 2")
    for text in d["hooks"] + d["titles"] + d["captions"]:
        assert words(text) <= allowed, text
    assert all(len(t) <= 100 for t in d["titles"])
    assert "#PeezyReport #news" in d["captions"][0]


def test_hashtag_normalising():
    assert drafts.normalize_hashtags("a, #b #a c!") == ["#a", "#b", "#c"]
