"""Build the animated README avatar from the current GitHub profile picture."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, ImageSequence


ROOT = Path(__file__).resolve().parents[1]
USERNAME = "EmBeHocCode"
FRAME_PATH = ROOT / "assets" / "khung" / "a176.png"
OUTPUT_PATH = ROOT / "assets" / "avatar" / "mieow-avatar-framed.png"
CANVAS_SIZE = 288
AVATAR_SIZE = 216
HTTP_TIMEOUT_SECONDS = 30


def request_bytes(url: str, accept: str) -> bytes:
    headers = {
        "Accept": accept,
        "User-Agent": f"{USERNAME}-profile-avatar-sync",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token and urllib.parse.urlsplit(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return response.read()


def current_avatar() -> Image.Image:
    profile_data = request_bytes(
        f"https://api.github.com/users/{USERNAME}",
        "application/vnd.github+json",
    )
    profile = json.loads(profile_data)

    avatar_url = profile["avatar_url"]
    parsed = urllib.parse.urlsplit(avatar_url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("s", "460"))
    sized_avatar_url = urllib.parse.urlunsplit(
        parsed._replace(query=urllib.parse.urlencode(query))
    )

    avatar_data = request_bytes(sized_avatar_url, "image/*")
    with Image.open(BytesIO(avatar_data)) as image:
        return ImageOps.exif_transpose(image).convert("RGBA")


def avatar_layer(source: Image.Image) -> Image.Image:
    avatar = ImageOps.fit(
        source,
        (AVATAR_SIZE, AVATAR_SIZE),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
    ImageDraw.Draw(mask).ellipse(
        (0, 0, AVATAR_SIZE - 1, AVATAR_SIZE - 1),
        fill=255,
    )
    avatar.putalpha(mask)

    layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    offset = ((CANVAS_SIZE - AVATAR_SIZE) // 2,) * 2
    layer.alpha_composite(avatar, offset)
    return layer


def build_animation(destination: Path) -> None:
    base = avatar_layer(current_avatar())
    frames: list[Image.Image] = []
    durations: list[float] = []

    with Image.open(FRAME_PATH) as animation:
        loop = animation.info.get("loop", 0)
        for frame in ImageSequence.Iterator(animation):
            overlay = frame.convert("RGBA")
            if overlay.size != (CANVAS_SIZE, CANVAS_SIZE):
                raise ValueError(
                    f"Frame must be {CANVAS_SIZE}x{CANVAS_SIZE}, got {overlay.size}"
                )
            frames.append(Image.alpha_composite(base, overlay))
            durations.append(frame.info.get("duration", 100))

    frames[0].save(
        destination,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop,
        disposal=0,
        blend=0,
        optimize=True,
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        dir=OUTPUT_PATH.parent,
        prefix="mieow-avatar-",
        suffix=".png",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        build_animation(temporary_path)

        if OUTPUT_PATH.exists() and digest(OUTPUT_PATH) == digest(temporary_path):
            print("GitHub avatar is unchanged; no file update needed.")
            return

        temporary_path.replace(OUTPUT_PATH)
        with Image.open(OUTPUT_PATH) as result:
            print(
                f"Updated {OUTPUT_PATH.relative_to(ROOT)}: "
                f"{result.size[0]}x{result.size[1]}, {result.n_frames} frames."
            )
    finally:
        temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
