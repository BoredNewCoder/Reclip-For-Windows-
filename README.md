> **Legal Disclaimer:** ReClip is intended for **personal, private use only**. You are solely responsible for ensuring your use complies with the terms of service of any platform you download from, as well as all applicable copyright laws in your jurisdiction. The authors of this software do not condone or encourage downloading copyrighted content without permission. Downloading DRM-protected content may be illegal under laws such as the DMCA. Use at your own risk.

# ReClip for Windows

**Self-hosted video and audio downloader** — Paste links from YouTube, TikTok, Instagram, X/Twitter, Twitch, and 1000+ other sites. Download as MP4 (video) or MP3 (audio) directly to your `downloads\` folder.

Made for Windows users who want it to **just work**.

## Requirements

- Windows 11
- Internet connection (first run only)

**Everything else (Python, FFmpeg, dependencies) is installed automatically** by `reclip.bat`.

Double-click **reclip.bat**.

First run downloads everything automatically (~80MB). Your browser opens when ready.

## Usage

1. Paste one or more URLs into the input box
2. Choose **MP4** (video) or **MP3** (audio)
3. Click **Fetch** — shows available formats with quality, codec, and file size
4. Select quality (higher resolution = larger file)
5. Click **Download** — real-time progress bar shows download % · file saves to `downloads\` folder

### Batch Downloads

- Paste multiple URLs, then click **Download All** — all videos download simultaneously
- Progress shows live % for each download

Downloads are saved to the `downloads\` folder inside the ReClip directory.

### Useful Features
- **Remove Sponsors**: Enable to automatically skip sponsor segments using SponsorBlock.
- **Batch Downloads**: Paste multiple URLs (one per line) and click **Download All**.
- **Cookies for Restricted Content**: Click the cookie icon → **Import Firefox** (easiest) or upload `cookies.txt`.

- Click the cookie icon (🍪) next to the Fetch button, then **Import Firefox** (one click, no extensions needed)
- Or click **Upload .txt** and export cookies manually using the [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension

The cookie icon turns green when cookies are active. Click it again to remove cookies at any time.

## Changing the Port
Run from Command Prompt:
set PORT=9000 && reclip.bat

## Interface

- **Dark mode** — click the sun/moon icon in the top-right corner; preference persists across sessions and respects your OS setting automatically

## Notes

- First run takes longer (installs tools + dependencies)
- Run `reclip.bat` anytime — it auto-cleans old processes
- To use a different port: Edit `reclip.bat` or set `PORT=9000` before running
- Downloads saved to `downloads\` folder with filename format: `Title - Channel - Source.mp4`
- Duplicate filenames get a counter suffix: `Title (1).mp4`, `Title (2).mp4`
- Supports 1000+ sites via [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- yt-dlp updates automatically on each launch to stay compatible with sites
- Python and ffmpeg are self-contained in the `python\` folder — nothing installed system-wide
- Re-launching `reclip.bat` automatically clears any stale server process

## Disclaimer

For personal use only. You are responsible for complying with the terms of service and copyright laws of the sites you use.

---

Made for Windows users who just want it to work.

## License

MIT — see [LICENSE](LICENSE). This tool is provided as-is with no warranty. You are responsible for your own use.
