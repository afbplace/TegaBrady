import json
import subprocess

import render


def stream(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,codec_name,pix_fmt", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)["streams"][0]


def test_layouts_produce_vertical_h264(media, tmp_path):
    for layout, react, expect in [("clip_only", None, 8), ("stack", media["reaction"], 8),
                                  ("sequence", media["reaction"], 11)]:
        out = tmp_path / f"{layout}.mp4"
        r = render.render(media["source"], react, layout, "Line one\nLine two", out)
        s = stream(out)
        assert (s["width"], s["height"], s["codec_name"], s["pix_fmt"]) == (1080, 1920, "h264", "yuv420p")
        assert abs(r["duration"] - expect) < 0.3
        assert (tmp_path / f"{layout}.ass").read_text().count("Dialogue:") == 2


def test_srt_parsing():
    cues = render.parse_subtitles("1\n00:00:01,000 --> 00:00:02,500\nHello\n\n2\n00:00:03,000 --> 00:00:04,000\nWorld", 10)
    assert cues == [(1.0, 2.5, "Hello"), (3.0, 4.0, "World")]
