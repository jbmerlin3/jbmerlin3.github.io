"""Turn a downloaded clip into the site's video files for one player.

Usage: python3 scripts/prep_video.py <downloaded.mp4> scouting/<player>/ [--start S] [--end S]

Writes clip.mp4 (H.264, at most 720p tall, ~2-4 MB, starts playing before it fully
downloads) and poster.jpg (the still shown on the page before anyone clicks).
Needs ffmpeg. Keeps the clip's own audio, since contact sound matters on a swing.
"""
import argparse
import json
import subprocess
from pathlib import Path


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("folder")
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    a = ap.parse_args()
    folder = Path(a.folder)
    clip, poster = folder / "clip.mp4", folder / "poster.jpg"
    trim = []
    if a.start is not None:
        trim += ["-ss", str(a.start)]
    if a.end is not None:
        trim += ["-to", str(a.end)]
    subprocess.run(["ffmpeg", "-y", "-v", "error", *trim, "-i", a.src,
                    "-vf", "scale=-2:'min(720,ih)'", "-c:v", "libx264", "-preset", "slow", "-crf", "26",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(clip)],
                   check=True)
    # poster from a third of the way in, past any lead-in
    t = duration(clip) / 3
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(clip), "-frames:v", "1",
                    "-vf", "scale=-2:360", "-q:v", "4", str(poster)], check=True)
    print(f"{clip}  {clip.stat().st_size // 1024} KB, {duration(clip):.1f}s")
    print(f"{poster}  {poster.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
