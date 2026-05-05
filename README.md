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
6. Click **Pause** to pause a download and resume it later — or **Cancel** to stop and discard it

### Batch Downloads

Paste multiple URLs (spaces, commas, or newlines), then click **Download All** — all downloads run simultaneously with live progress per item.

Downloads are saved to the `downloads\` folder inside the ReClip directory.

## Features

- **Remove Sponsors** — automatically skips sponsor segments via SponsorBlock (YouTube)
- **Dark mode** — click the sun/moon icon top-right; respects OS setting, persists across sessions
- **Pause & Resume** — pause any active download and resume it later; progress is preserved
- **Cancel downloads** — stop any in-progress or paused download and discard the partial file
- **Auto-retry on network drops** — retries failed requests up to 50 times automatically
- **Crash recovery** — if the server restarts mid-download, active and paused downloads are restored on next launch
- **2-hour timeout** — downloads that hang are automatically cancelled after 2 hours
- **Cookies for restricted content** — unlock age-restricted and subscriber-only videos

### Cookies

Click the cookie icon next to Fetch:

- **Import Firefox** — one click, no extensions needed
- **Upload .txt** — export cookies manually using a browser extension
- **Get Extension ↗** — opens [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) in Chrome Web Store directly from the panel

The cookie icon turns green when active. Click again to remove.

## Changing the Port

```
set PORT=9000 && reclip.bat
```

## Notes

- First run takes longer (installs tools + dependencies)
- Run `reclip.bat` anytime — it auto-cleans old processes
- Downloads saved to `downloads\` with filename format: `Title - Channel - Source.mp4`
- Duplicate filenames get a counter suffix: `Title (1).mp4`, `Title (2).mp4`
- Paused and interrupted downloads resume using yt-dlp's partial file (`.part`) — no re-downloading from scratch
- Paused/active job state is stored in `.jobs\` — do not delete this folder while downloads are in progress
- Pause/resume works within the same browser session; closing the tab while paused is safe (state survives server restart)
- Platform chips at the bottom are clickable — open each site in a new tab; **1000+ more** links to the full yt-dlp supported sites list
- Supports 1000+ sites via [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- yt-dlp updates automatically on each launch
- Python and FFmpeg are self-contained in `python\` — nothing installed system-wide
- Re-launching `reclip.bat` clears any stale server process

## License

MIT — see [LICENSE](LICENSE). Provided as-is, no warranty. You are responsible for your own use.
