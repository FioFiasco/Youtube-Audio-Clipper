# YouTube Audio Clipper

A small Python program that downloads **only a selected section** of a YouTube video as an audio file, for example minute 4:30 to 8:35 of a long mix.

- Choose the start and end time
- Choose the format (MP3, M4A, WAV, FLAC, Opus, AAC) and bitrate
- **Window version (GUI)**: type in the URL and times, click Download, no commands needed
- Or use it from the command line, or by double-clicking the script (it asks you questions)
- Only the selected section is downloaded, not the whole video

> **Legal note:** Only download content you have the right to use, or for personal use where that is permitted. Downloading from YouTube may violate its Terms of Service. You are responsible for how you use this tool.

---

## 1. Installation (one time)

### Step 1: Install Python
1. Download Python from <https://www.python.org/downloads/>.
2. **Windows:** on the first installer screen, tick **"Add Python to PATH"**, then install.
3. Check it worked. Open a terminal (see "Opening a terminal" below) and type:
   - Windows: `python --version`
   - Mac/Linux: `python3 --version`

### Step 2: Install yt-dlp
In a terminal:

```
pip install -U yt-dlp
```
(On Mac/Linux use `pip3` instead of `pip`.)

### Step 3: Install ffmpeg
ffmpeg converts the audio. Official download page: <https://ffmpeg.org/download.html>

- **Windows:** `winget install ffmpeg` (then close and reopen the terminal)
- **Mac:** `brew install ffmpeg` (needs [Homebrew](https://brew.sh))
- **Linux:** `sudo apt install ffmpeg`

Check it worked: `ffmpeg -version`

**Manual install on Windows (if winget doesn't work):**
1. Go to <https://www.gyan.dev/ffmpeg/builds/> (the Windows builds linked from ffmpeg.org) and download `ffmpeg-release-essentials.zip`.
2. Unzip it and move the folder to `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your PATH: press the Windows key, search for **"Edit the system environment variables"**, click **Environment Variables**, select **Path** under your user variables, click **Edit**, then **New**, and paste `C:\ffmpeg\bin`. Confirm with OK.
4. Close and reopen the terminal, then run `ffmpeg -version`.

### Step 4 (recommended): Install Deno
YouTube sometimes requires a JavaScript runtime. If you get "video not available" errors, install it:

- **Windows:** `winget install DenoLand.Deno`
- **Mac:** `brew install deno`

### Step 5: Get the program
Download `yt_audio_clip.py` and `yt_audio_clip_gui.py` from this repository (click each file, then the download icon) and save them **in the same folder**. Or clone the repository:

```
git clone https://github.com/YOUR-USERNAME/youtube-audio-clipper.git
```

---

## 2. How to use it

### Option A: Window version (easiest)
Keep `yt_audio_clip_gui.py` and `yt_audio_clip.py` **in the same folder**, then double-click `yt_audio_clip_gui.py` (or run `python yt_audio_clip_gui.py`).

1. Paste the YouTube address.
2. Enter the start time (e.g. `4:30`) and the end time (e.g. `8:35`). Leave the end empty to go to the end of the video.
3. Choose the format and bitrate, and the folder to save to (default: your Downloads folder).
4. Click **Download**. The log shows what is happening. When it says "Done!", click **Open folder**.

A black console window may open behind the program. Leave it open; closing it closes the program.
On Windows, tkinter (the window toolkit) is included with the normal Python installer. On Linux you may need `sudo apt install python3-tk`.

### Option B: Double-click the command-line script
Double-click `yt_audio_clip.py`. It asks you for:

1. The YouTube URL
2. Start time (e.g. `4:30`)
3. End time (e.g. `8:35`, leave empty for "until the end")
4. Format (Enter = mp3)
5. Bitrate (Enter = 192)

The audio file is saved **in the same folder as the script**. The window stays open at the end so you can read the result.

### Option C: Command line

```
python yt_audio_clip.py "https://www.youtube.com/watch?v=XXXX" -s 4:30 -e 8:35
```

**Opening a terminal in the right folder (Windows):** open the folder in File Explorer, click the address bar, type `cmd` and press Enter.
**Mac:** right-click the folder, then Services, then New Terminal at Folder.

### Options

| Option | Meaning | Default |
|---|---|---|
| `-s`, `--start` | Start time | `0:00` |
| `-e`, `--end` | End time | end of video |
| `-f`, `--format` | `mp3`, `m4a`, `wav`, `flac`, `opus`, `aac` | `mp3` |
| `-q`, `--quality` | Bitrate in kbps (lossy formats only) | `192` |
| `-o`, `--output-dir` | Folder to save to | current folder (script folder on double-click) |

Times can be written as `mm:ss`, `h:mm:ss` or plain seconds (`270`). Use a colon: `4:30`, not `4.30`.

### Examples

```
# 320 kbps MP3 from 31:30 to 35:11
python yt_audio_clip.py "URL" -s 31:30 -e 35:11 -q 320

# M4A from 1h 02m 10s to 1h 07m 45s
python yt_audio_clip.py "URL" -s 1:02:10 -e 1:07:45 -f m4a

# From 4:30 to the end, saved in a Music folder
python yt_audio_clip.py "URL" -s 4:30 -o "C:\Users\YourName\Music"
```

**About quality:** YouTube's own audio is roughly 128 to 160 kbps, so going above 192 kbps mostly makes files bigger without sounding better.

---

## 3. Troubleshooting

| Problem | Solution |
|---|---|
| `This video is unavailable` / `Video not available` (but it plays in your browser) | **Check the URL first.** A single wrong character in the video ID gives this same error. Copy the address directly from your browser's address bar (not from a chat or web page, which can add formatting like `[ ]( )`), keep it in quotes, and remove extras like `&list=...`. If the URL is right, update yt-dlp: `pip install -U yt-dlp`, and install Deno (Step 4). |
| `ffmpeg exited with code 4294967283` | Permission denied when saving. Use the latest version of the script, or save to a normal folder with `-o`. |
| `ffmpeg not found` | Install ffmpeg (Step 3) and reopen the terminal. |
| The window version doesn't open / `No module named 'yt_audio_clip'` | Keep `yt_audio_clip_gui.py` and `yt_audio_clip.py` together in the same folder. |
| Window closes immediately | Use the latest version of the script, or run it from a terminal to see the message. |
| "The system cannot accept the time entered" | The script had already stopped and you were typing into the Windows prompt. Fix the earlier error first. |
| Stopped working after weeks or months | YouTube changes often. Run `pip install -U yt-dlp`. |

---

## 4. How it works

The script uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download just the chosen time range and [ffmpeg](https://ffmpeg.org/) to convert it to your chosen audio format.

## Support

If this tool saved you time, you can support its development via PayPal: https://www.paypal.me/michaelfiolka69

## License

MIT, see [LICENSE](LICENSE). yt-dlp and ffmpeg have their own licenses.
