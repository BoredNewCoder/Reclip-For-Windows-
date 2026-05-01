> **Legal Disclaimer:** ReClip is intended for **personal, private use only**. You are solely responsible for ensuring your use complies with the terms of service of any platform you download from, as well as all applicable copyright laws in your jurisdiction. The authors of this software do not condone or encourage downloading copyrighted content without permission. Downloading DRM-protected content may be illegal under laws such as the DMCA. Use at your own risk.

# ReClip for Windows

**Self-hosted video and audio downloader** — Paste links from YouTube, TikTok, Instagram, X/Twitter, Twitch, and 1000+ other sites. Download as MP4 (video) or MP3 (audio) directly to your `downloads\` folder.

Made for Windows users who want it to **just work**.

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Internet connection (for first-time setup)

**Everything else (Python, FFmpeg, dependencies) is installed automatically** by `reclip.bat`.

## Setup Instructions (Super Easy)

1. Download the latest release (or clone/extract the repository) into any folder.
2. **Double-click** `reclip.bat`.

### First Run (Setup Phase)
- The launcher will automatically:
  - Check/install **winget** (App Installer)
  - Install **Python 3.13** for the current user (no administrator rights required)
  - Install **FFmpeg**
- When prompted, **close the window completely** and **double-click `reclip.bat` again**.

### Second Run (Normal Launch)
- Creates virtual environment (if needed)
- Updates all dependencies from `requirements.txt`
- Starts the ReClip server

Open your browser and go to: **http://localhost:8899**

## Usage

1. Paste one or more URLs into the box.
2. Select **Video (MP4)** or **Audio (MP3)**.
3. Click **Fetch** to see available quality options.
4. Choose your preferred format/quality and click **Download**.

Downloads are saved to the `downloads\` folder inside the ReClip directory.

### Useful Features
- **Remove Sponsors**: Enable to automatically skip sponsor segments using SponsorBlock.
- **Batch Downloads**: Paste multiple URLs (one per line) and click **Download All**.
- **Cookies for Restricted Content**: Click the cookie icon → **Import Firefox** (easiest) or upload `cookies.txt`.

> **Note**: True DRM-protected content (most YouTube Premium movies, Netflix, etc.) cannot be downloaded.

### Dark Mode
Click the sun/moon icon in the top right. Your preference is saved and respects your Windows theme.

## Changing the Port
Run from Command Prompt:
set PORT=9000 && reclip.bat

## Notes

- First run takes longer (installs tools + dependencies)
- Run `reclip.bat` anytime — it auto-cleans old processes
- To use a different port: Edit `reclip.bat` or set `PORT=9000` before running
- Downloads saved to `downloads\` folder with filename format: `Title - Channel - Source.mp4`
- Duplicate filenames get a counter suffix: `Title (1).mp4`, `Title (2).mp4`
- Supports 1000+ sites via [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- Re-launching `reclip.bat` automatically clears any stale server process

## Disclaimer

For personal use only. You are responsible for complying with the terms of service and copyright laws of the sites you use.

---

Made for Windows users who just want it to work.

## License

MIT — see [LICENSE](LICENSE). This tool is provided as-is with no warranty. You are responsible for your own use.
