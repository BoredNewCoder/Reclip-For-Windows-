# ReClip

Self-hosted video and audio downloader. Paste URLs from YouTube, TikTok, Instagram, Twitter/X, and 1000+ sites — download as MP4 or MP3.

## Requirements

- Windows 11
- [Python 3.8+](https://www.python.org/)
- [ffmpeg](https://ffmpeg.org/)

## Setup

**1. Install prerequisites** (one-time, open any terminal):

```
winget install Python.Python.3
winget install Gyan.FFmpeg
```

**2. Open a new terminal**, then run:

```
reclip.bat
```

First run installs Python dependencies automatically. Open **http://localhost:8899**.

## Usage

1. Paste one or more URLs into the input box
2. Choose **MP4** (video) or **MP3** (audio)
3. Click **Fetch**
4. Select quality if prompted
5. Click **Download**

## Notes

- Port can be changed: `set PORT=9000 && reclip.bat`
- Downloads saved to `downloads\` folder inside the app directory
- Supports 1000+ sites via [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
