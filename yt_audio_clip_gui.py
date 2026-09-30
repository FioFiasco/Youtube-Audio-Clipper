#!/usr/bin/env python3
"""
YouTube Audio Clipper - simple window (GUI) version.

Keep this file in the same folder as yt_audio_clip.py.
Start it with:   python yt_audio_clip_gui.py     (or double-click the file)

Requirements: the same as the command-line version (yt-dlp and ffmpeg).
"""

import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from yt_audio_clip import download_clip, parse_time

FORMATS = ["mp3", "m4a", "wav", "flac", "opus", "aac"]
LOSSY = {"mp3", "m4a", "opus", "aac"}
BITRATES = ["128", "192", "256", "320"]
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def clean_url(text: str) -> str:
    """Tidy a pasted address (quotes, spaces, '[text](https://...)' link formatting)."""
    text = text.strip().strip('"').strip("'").strip()
    match = re.search(r"\((https?://[^)\s]+)\)", text)
    if match:
        text = match.group(1)
    if text and not text.lower().startswith(("http://", "https://")):
        text = "https://" + text
    return text


def read_times(start_text: str, end_text: str):
    """Return (start_seconds, end_seconds_or_None); raise ValueError on bad input."""
    try:
        start = parse_time(start_text.strip() or "0")
        end = parse_time(end_text) if end_text.strip() else None
    except Exception:
        raise ValueError("Please enter times like 4:30 or 1:02:10 (minutes:seconds).")
    if end is not None and end <= start:
        raise ValueError("The end time must be after the start time.")
    return start, end


def default_folder() -> str:
    downloads = Path.home() / "Downloads"
    return str(downloads if downloads.is_dir() else Path(__file__).resolve().parent)


class QueueLogger:
    """Passes yt-dlp messages to the window."""

    def __init__(self, q: "queue.Queue"):
        self.q = q

    def debug(self, msg):
        if not msg.startswith("[debug]"):
            self.q.put(("log", msg))

    def info(self, msg):
        self.q.put(("log", msg))

    def warning(self, msg):
        self.q.put(("log", "Warning: " + msg))

    def error(self, msg):
        self.q.put(("log", msg))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Audio Clipper")
        self.minsize(580, 480)
        self.queue: "queue.Queue" = queue.Queue()
        self.worker = None

        self.url_var = tk.StringVar()
        self.start_var = tk.StringVar(value="0:00")
        self.end_var = tk.StringVar()
        self.format_var = tk.StringVar(value="mp3")
        self.bitrate_var = tk.StringVar(value="192")
        self.folder_var = tk.StringVar(value=default_folder())
        self.status_var = tk.StringVar(value="Ready.")

        self._build()
        self.after(100, self._poll)

    # ---------- layout ----------
    def _build(self):
        pad = {"padx": 8, "pady": 5}
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="YouTube URL:").grid(row=0, column=0, sticky="w", **pad)
        url_entry = ttk.Entry(frame, textvariable=self.url_var)
        url_entry.grid(row=0, column=1, columnspan=3, sticky="ew", **pad)
        url_entry.focus()

        ttk.Label(frame, text="Start (e.g. 4:30):").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.start_var, width=12).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(frame, text="End (empty = until the end):").grid(row=1, column=2, sticky="e", **pad)
        ttk.Entry(frame, textvariable=self.end_var, width=12).grid(row=1, column=3, sticky="w", **pad)

        ttk.Label(frame, text="Format:").grid(row=2, column=0, sticky="w", **pad)
        fmt_box = ttk.Combobox(frame, textvariable=self.format_var, values=FORMATS,
                               state="readonly", width=10)
        fmt_box.grid(row=2, column=1, sticky="w", **pad)
        fmt_box.bind("<<ComboboxSelected>>", self._on_format)
        ttk.Label(frame, text="Bitrate (kbps):").grid(row=2, column=2, sticky="e", **pad)
        self.bitrate_box = ttk.Combobox(frame, textvariable=self.bitrate_var, values=BITRATES,
                                        state="readonly", width=10)
        self.bitrate_box.grid(row=2, column=3, sticky="w", **pad)

        ttk.Label(frame, text="Save to:").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.folder_var).grid(row=3, column=1, columnspan=2, sticky="ew", **pad)
        ttk.Button(frame, text="Browse...", command=self._browse).grid(row=3, column=3, sticky="w", **pad)

        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=4, sticky="ew", **pad)
        self.download_btn = ttk.Button(buttons, text="Download", command=self.start)
        self.download_btn.pack(side="left")
        self.open_btn = ttk.Button(buttons, text="Open folder", command=self._open_folder)
        self.open_btn.pack(side="left", padx=8)
        ttk.Label(buttons, textvariable=self.status_var).pack(side="left", padx=8)

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=4, sticky="ew", **pad)

        log_frame = ttk.Frame(frame)
        log_frame.grid(row=6, column=0, columnspan=4, sticky="nsew", **pad)
        frame.rowconfigure(6, weight=1)
        self.log = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.bind("<Return>", lambda _e: self.start())
        self._on_format()

    # ---------- helpers ----------
    def _on_format(self, _event=None):
        lossy = self.format_var.get() in LOSSY
        self.bitrate_box.configure(state="readonly" if lossy else "disabled")

    def _browse(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or None)
        if folder:
            self.folder_var.set(folder)

    def _open_folder(self):
        folder = self.folder_var.get()
        if not os.path.isdir(folder):
            return
        if sys.platform.startswith("win"):
            os.startfile(folder)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", folder])
        else:
            subprocess.run(["xdg-open", folder])

    def _log(self, text: str):
        text = ANSI.sub("", text)
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy: bool):
        self.download_btn.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    # ---------- download ----------
    def start(self):
        if self.worker and self.worker.is_alive():
            return
        try:
            url = clean_url(self.url_var.get())
            if not url:
                raise ValueError("Please enter a YouTube URL.")
            start, end = read_times(self.start_var.get(), self.end_var.get())
            folder = self.folder_var.get().strip()
            if not folder:
                raise ValueError("Please choose a folder to save to.")
            os.makedirs(folder, exist_ok=True)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Please check your input", str(exc))
            return

        audio_format = self.format_var.get()
        quality = self.bitrate_var.get() if audio_format in LOSSY else "192"
        opts = {
            "logger": QueueLogger(self.queue),
            "noprogress": True,
            "color": "no_color",
        }

        self._log(f"Starting: {url}")
        self.status_var.set("Downloading...")
        self._set_busy(True)
        self.worker = threading.Thread(
            target=self._run, args=(url, start, end, audio_format, quality, folder, opts), daemon=True
        )
        self.worker.start()

    def _run(self, url, start, end, audio_format, quality, folder, opts):
        try:
            download_clip(url, start, end, audio_format, quality, folder, opts)
            self.queue.put(("done", folder))
        except Exception as exc:  # show any error in the window
            self.queue.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "done":
                    self._set_busy(False)
                    self.status_var.set("Done!")
                    self._log(f"Done! Saved in: {payload}")
                elif kind == "error":
                    self._set_busy(False)
                    self.status_var.set("Failed.")
                    message = ANSI.sub("", payload)
                    if message not in self.log.get("1.0", "end"):
                        self._log("Error: " + message)
                    messagebox.showerror("Download failed", message)
        except queue.Empty:
            pass
        self.after(100, self._poll)


if __name__ == "__main__":
    App().mainloop()
