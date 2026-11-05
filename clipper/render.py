"""FFmpeg assembly of 1080x1920 vertical videos with burned-in subtitles."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

W, H = 1080, 1920
FPS = 30
MAX_SECONDS = 180  # YouTube Shorts ceiling; also within IG Reels / TikTok API limits


class RenderError(RuntimeError):
    pass


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", str(path)], capture_output=True, text=True)
    if out.returncode != 0:
        raise RenderError(f"ffprobe failed on {Path(path).name}: {out.stderr.strip()[:300]}")
    info = json.loads(out.stdout)
    kinds = {s.get("codec_type") for s in info.get("streams", [])}
    if "video" not in kinds:
        raise RenderError(f"{Path(path).name} has no video stream")
    return {"duration": float(info["format"].get("duration") or 0), "has_audio": "audio" in kinds}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- subtitles
_SRT_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def parse_subtitles(text, duration):
    """Accept SRT, or plain lines (auto-timed evenly across the video)."""
    text = (text or "").strip()
    if not text:
        return []
    if _SRT_TIME.search(text):
        cues = []
        for block in re.split(r"\n\s*\n", text):
            m = _SRT_TIME.search(block)
            if not m:
                continue
            g = list(map(int, m.groups()))
            start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
            end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
            body = block[m.end():].strip()
            if body:
                cues.append((start, end, body))
        return cues
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    step = duration / len(lines) if duration > 0 else 2.0
    return [(i * step, (i + 1) * step, l) for i, l in enumerate(lines)]


def _ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _ass_escape(s):
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def write_ass(cues, path, margin_v=420):
    """ASS file at native 1080x1920 so font sizes are predictable.

    margin_v keeps captions above the bottom UI overlays of Reels/TikTok/Shorts.
    """
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,90,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = "".join(
        f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},Default,,0,0,0,,{_ass_escape(t)}\n"
        for s, e, t in cues)
    Path(path).write_text(head + body, encoding="utf-8")


# ---------------------------------------------------------------- filters
def _fit_blur(inp, out):
    """Fit any aspect into 1080x1920 over a blurred, zoomed copy of itself."""
    return (f"[{inp}:v]fps={FPS},split[{out}a][{out}b];"
            f"[{out}a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=20:2[{out}bg];"
            f"[{out}b]scale={W}:{H}:force_original_aspect_ratio=decrease[{out}fg];"
            f"[{out}bg][{out}fg]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[{out}]")


def _fill(inp, out, w, h):
    return (f"[{inp}:v]fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1,format=yuv420p[{out}]")


def _audio(idx, info, out, volume=1.0, pad_to=None):
    src = f"[{idx}:a]" if info["has_audio"] else None
    chain = "aresample=48000,aformat=channel_layouts=stereo"
    if volume != 1.0:
        chain += f",volume={volume}"
    if pad_to:
        chain += f",apad=whole_dur={pad_to:.3f}"
    if src:
        return f"{src}{chain}[{out}]"
    dur = pad_to or info["duration"]
    return f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}[{out}]"


def build_command(clip, reaction, layout, ass_name, out_name, clip_volume=0.35):
    """Return (ffmpeg args, expected duration). Paths are relative to cwd."""
    ci = probe(clip)
    inputs = ["-i", str(clip)]
    if layout != "clip_only" and not reaction:
        layout = "clip_only"
    if layout == "clip_only":
        dur = ci["duration"]
        fg = _fit_blur(0, "v0") + ";" + _audio(0, ci, "a0")
        vlabel, alabel = "v0", "a0"
    else:
        ri = probe(reaction)
        inputs += ["-i", str(reaction)]
        if layout == "stack":
            dur = max(ci["duration"], ri["duration"])
            half = H // 2
            fg = (_fill(0, "top0", W, half) + ";" + _fill(1, "bot0", W, half) + ";"
                  f"[top0]tpad=stop_mode=clone:stop_duration={dur:.3f}[top];"
                  f"[bot0]tpad=stop_mode=clone:stop_duration={dur:.3f}[bot];"
                  "[top][bot]vstack=inputs=2[v0];"
                  + _audio(0, ci, "ca", clip_volume, dur) + ";"
                  + _audio(1, ri, "ra", 1.0, dur) + ";"
                  "[ca][ra]amix=inputs=2:duration=longest:normalize=0[a0]")
        elif layout == "sequence":
            dur = ci["duration"] + ri["duration"]
            fg = (_fit_blur(0, "c") + ";" + _fit_blur(1, "r") + ";"
                  + _audio(0, ci, "ca") + ";" + _audio(1, ri, "ra") + ";"
                  "[c][ca][r][ra]concat=n=2:v=1:a=1[v0][a0]")
        else:
            raise RenderError(f"unknown layout {layout!r}")
        vlabel, alabel = "v0", "a0"
    if dur > MAX_SECONDS:
        raise RenderError(f"Result would be {dur:.0f}s; Shorts/Reels/TikTok target is "
                          f"{MAX_SECONDS}s max. Trim the clip or reaction.")
    if ass_name:
        fg += f";[{vlabel}]subtitles={ass_name}[vout]"
        vlabel = "vout"
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
            "-filter_complex", fg, "-map", f"[{vlabel}]", "-map", f"[{alabel}]",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-profile:v", "high", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart", str(out_name)]
    return args, dur


def render(clip, reaction, layout, subtitles_text, out_path):
    """Render to out_path. Subtitle file sits next to the output (relative path
    avoids FFmpeg filter-escaping problems)."""
    out_path = Path(out_path).resolve()
    workdir = out_path.parent
    workdir.mkdir(parents=True, exist_ok=True)
    clip = Path(clip).resolve()
    reaction = Path(reaction).resolve() if reaction else None
    # duration for auto-timed subtitles
    _, dur = build_command(clip, reaction, layout, None, out_path.name)
    cues = parse_subtitles(subtitles_text, dur)
    ass_name = None
    if cues:
        ass_name = out_path.stem + ".ass"
        write_ass(cues, workdir / ass_name)
    args, _ = build_command(clip, reaction, layout, ass_name, out_path.name)
    tmp = out_path.with_suffix(".tmp.mp4")
    args[-1] = tmp.name
    res = subprocess.run(args, cwd=workdir, capture_output=True, text=True)
    if res.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RenderError(res.stderr.strip()[-800:] or "ffmpeg failed")
    tmp.replace(out_path)
    info = probe(out_path)
    return {"duration": info["duration"], "sha256": sha256_file(out_path)}


def cut_segment(src, start, end, out_path):
    """Used by the MOCK OpusClip integration to cut local candidate clips."""
    res = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}",
         "-i", str(src), "-t", f"{end - start:.3f}", "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(out_path)],
        capture_output=True, text=True)
    if res.returncode != 0:
        raise RenderError(res.stderr.strip()[-500:])
