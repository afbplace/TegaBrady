import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def make_video(path, size="1280x720", dur=6, freq=440, src="testsrc2"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"{src}=size={size}:rate=30:duration={dur}", "-f", "lavfi", "-i",
                    f"sine=f={freq}:duration={dur}", "-shortest", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


@pytest.fixture(scope="session")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("media")
    return {"source": make_video(d / "source.mp4", dur=8),
            "reaction": make_video(d / "reaction.mp4", "720x1280", 3, 660, "smptebars")}


@pytest.fixture
def client(tmp_path, monkeypatch):
    for k in ("OPUSCLIP_API_KEY", "UPLOAD_POST_API_KEY", "UPLOAD_POST_USER"):
        monkeypatch.delenv(k, raising=False)
    import app as appmod
    monkeypatch.setattr(appmod, "_load_dotenv", lambda p: None)
    a = appmod.create_app(tmp_path / "data", run_async=False)
    a.testing = True
    return a.test_client()
