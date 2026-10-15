"""Record the demo as a video: a clinical note pasted, read into terms, checked, diagnosed.

Playwright drives a real browser through the demo page and records it — the way
end-to-end tests and product demos are recorded, so the video can be made again
after any change. Start the service (reading notes) and the page, then record:

    RAREDX_SERVICE_READ_NOTES=true uv run raredx serve &
    uv run raredx demo &
    uv run --group record playwright install chromium   # once
    uv run --group record python scripts/record_demo.py docs/img/demo-note

It writes demo-note.mp4 and a smaller demo-note.gif (ffmpeg). The note is one of
those written for the demo from a published patient's findings; a run costs about
one US cent (the note read, then the agent's answer).
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

EXAMPLE = "One the agent rescued"  # the galactosemia patient: its note is in service/notes/
SIZE = {"width": 1280, "height": 860}


def pause(page: Page, seconds: float) -> None:
    page.wait_for_timeout(seconds * 1000)


def scroll(page: Page, pixels: int, steps: int = 8, seconds: float = 1.6) -> None:
    """Scroll the page's main area smoothly, as a person would."""
    for _ in range(steps):
        page.mouse.wheel(0, pixels / steps)
        pause(page, seconds / steps)


def record(page: Page, url: str) -> None:
    page.goto(url)
    page.get_by_text("Start from", exact=True).wait_for(timeout=60_000)  # the note mode, first
    page.mouse.move(640, 430)  # over the main area, where the wheel scrolls
    pause(page, 2)
    page.get_by_text(EXAMPLE, exact=False).first.click()
    note = page.get_by_label("Clinical note")
    # The page reruns on the click: wait for this patient's note before copying it.
    page.wait_for_function(
        "() => (document.querySelector('textarea[aria-label=\"Clinical note\"]') || {}).value"
        "?.includes('galactose')"
    )
    text = note.input_value()
    note.fill("")  # an empty box, then the note pasted in
    note.press("Control+Enter")  # Streamlit takes a text area's value on submit or blur
    pause(page, 1.5)
    note.click()
    page.keyboard.insert_text(text)
    note.press("Control+Enter")
    page.wait_for_function(
        "() => document.querySelector('textarea[aria-label=\"Clinical note\"]').value.length > 100"
    )
    pause(page, 2.5)
    page.get_by_role("button", name="Read the note").click()
    page.get_by_text("terms ticked").wait_for(timeout=120_000)
    pause(page, 1)
    scroll(page, 330)
    pause(page, 3)  # the note, its words marked
    scroll(page, 420)
    pause(page, 3.5)  # the terms, each with a tick
    page.get_by_role("button", name="Diagnose").click()
    page.get_by_text("Answered by the agent").wait_for(timeout=180_000)
    pause(page, 1)
    page.get_by_text("Published diagnosis").first.scroll_into_view_if_needed()
    pause(page, 3.5)  # where the published diagnosis landed
    scroll(page, 450)
    pause(page, 3)  # the ranking
    scroll(page, 500)
    pause(page, 4)  # the evidence for the first diagnosis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path, help="Path without extension: .mp4 and .gif are written")
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder, sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=SIZE, record_video_dir=folder, record_video_size=SIZE, color_scheme="light"
        )
        page = context.new_page()
        try:
            record(page, args.url)
        finally:
            context.close()  # the video is written when its page closes
            browser.close()
        [video] = Path(folder).glob("*.webm")
        webm = args.out.with_suffix(".webm")
        shutil.move(video, webm)
    mp4, gif = args.out.with_suffix(".mp4"), args.out.with_suffix(".gif")
    ffmpeg = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm)]
    h264 = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26"]
    subprocess.run([*ffmpeg, *h264, str(mp4)], check=True)
    # A GIF plays inline in a README: fewer frames, smaller, its own 64-colour palette.
    palette = (
        "fps=5,scale=760:-1:flags=lanczos,split[a][b];"
        "[a]palettegen=max_colors=48[p];[b][p]paletteuse=dither=bayer"
    )
    subprocess.run([*ffmpeg, "-vf", palette, str(gif)], check=True)
    webm.unlink()
    for path in (mp4, gif):
        print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
