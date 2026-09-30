#!/usr/bin/env python3
"""
Extract a section of audio from a YouTube video.

Examples:
    python yt_audio_clip.py "https://www.youtube.com/watch?v=XXXX" -s 4:30 -e 8:35
    python yt_audio_clip.py "URL" -s 1:02:10 -e 1:07:45 -f m4a
    python yt_audio_clip.py "URL" -s 4:30            # 4:30 until the end
    python yt_audio_clip.py                          # interactive prompts

Requirements:
    pip install yt-dlp
    ffmpeg installed and on your PATH (https://ffmpeg.org/download.html)
"""

import argparse
import os
import sys

from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func


def parse_time(value: str) -> float:
    """Convert '4:30', '1:02:10', or '270' into seconds."""
    parts = value.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise argparse.ArgumentTypeError(f"Invalid time: {value!r}")
    try:
        numbers = [float(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid time: {value!r}")
    seconds = 0.0
    for n in numbers:
        seconds = seconds * 60 + n
    return seconds


def fmt(seconds: float) -> str:
    """Format seconds as H-MM-SS / M-SS for use in a filename."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}-{m:02d}-{sec:02d}" if h else f"{m}-{sec:02d}"


def download_clip(url: str, start: float, end: float | None, audio_format: str,
                  quality: str, output_dir: str) -> None:
    end_value = end if end is not None else float("inf")
    label = f"{fmt(start)}_to_{fmt(end) if end is not None else 'end'}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_dir}/%(title)s [{label}].%(ext)s",
        # Only download the requested section
        "download_ranges": download_range_func(None, [(start, end_value)]),
        # Re-encode at the cut points so the clip starts/ends precisely
        "force_keyframes_at_cuts": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": quality,
            }
        ],
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a section of audio from a YouTube video.")
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument("-s", "--start", type=parse_time, help="Start time, e.g. 4:30 or 1:02:10")
    parser.add_argument("-e", "--end", type=parse_time, help="End time, e.g. 8:35 (default: end of video)")
    parser.add_argument("-f", "--format", default="mp3",
                        choices=["mp3", "m4a", "wav", "flac", "opus", "aac"],
                        help="Output audio format (default: mp3)")
    parser.add_argument("-q", "--quality", default="192",
                        help="Bitrate in kbps for lossy formats (default: 192)")
    parser.add_argument("-o", "--output-dir", default=None,
                        help="Folder to save to (default: current folder, or the script's folder "
                             "when started by double-click)")
    args = parser.parse_args()
    interactive = not args.url
    if args.output_dir is None:
        # When double-clicked, the "current folder" can be a protected system folder,
        # so save next to the script instead.
        args.output_dir = os.path.dirname(os.path.abspath(__file__)) if interactive else "."
    os.makedirs(args.output_dir, exist_ok=True)

    try:
        # Interactive mode (e.g. double-clicking the script)
        if interactive:
            args.url = input("YouTube URL: ").strip()
            args.start = parse_time(input("Start time (e.g. 4:30): ") or "0")
            end_in = input("End time (e.g. 8:35, blank = end of video): ").strip()
            args.end = parse_time(end_in) if end_in else None
            fmt_in = input("Format [mp3/m4a/wav/flac/opus/aac] (Enter = mp3): ").strip().lower()
            args.format = fmt_in if fmt_in in ("mp3", "m4a", "wav", "flac", "opus", "aac") else "mp3"
            if args.format in ("mp3", "m4a", "opus", "aac"):
                q_in = input("Bitrate in kbps, e.g. 128 / 192 / 256 / 320 (Enter = 192): ").strip()
                args.quality = q_in or "192"

        start = args.start if args.start is not None else 0.0
        if args.end is not None and args.end <= start:
            raise ValueError("End time must be after start time.")

        download_clip(args.url, start, args.end, args.format, args.quality, args.output_dir)
        print(f"\nDone! Saved in: {os.path.abspath(args.output_dir)}")
    except Exception as exc:  # show the error instead of closing the window
        print(f"\nError: {exc}")
    finally:
        if interactive:
            input("\nPress Enter to close this window...")


if __name__ == "__main__":
    main()
