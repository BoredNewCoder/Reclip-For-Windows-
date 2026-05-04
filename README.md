> **Legal Disclaimer:** ReClip is intended for **personal, private use only**. You are solely responsible for ensuring your use complies with the terms of service of any platform you download from, as well as all applicable copyright laws in your jurisdiction. The authors of this software do not condone or encourage downloading copyrighted content without permission. Downloading DRM-protected content may be illegal under laws such as the DMCA. Use at your own risk.

# ReClip

Self-hosted video and audio downloader. Paste URLs from YouTube, TikTok, Instagram, Twitter/X, Twitch, LinkedIn, and 1000+ sites — download as MP4 or MP3 directly to your `downloads\` folder.

## Requirements

- Windows 11
- Internet connection (first run only)

## Setup

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

## Unlocking Age-Restricted & Private Content

Some videos require you to be logged in (age-restricted YouTube, subscriber-only Twitch VODs, etc). ReClip can import your browser session to unlock them:

- Click the cookie icon (🍪) next to the Fetch button, then **Import Firefox** (one click, no extensions needed)
- Or click **Upload .txt** and export cookies manually using the [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension

The cookie icon turns green when cookies are active. Click it again to remove cookies at any time.

> **Note:** True Widevine DRM content (YouTube Premium movies, etc.) cannot be downloaded by any tool.

## Interface

- **Dark mode** — click the sun/moon icon in the top-right corner; preference persists across sessions and respects your OS setting automatically

## Notes

- Port can be changed: `set PORT=9000 && reclip.bat`
- Downloads saved to `downloads\` folder with filename format: `Title - Channel - Source.mp4`
- Duplicate filenames get a counter suffix: `Title (1).mp4`, `Title (2).mp4`
- Supports 1000+ sites via [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- yt-dlp updates automatically on each launch to stay compatible with sites
- Python and ffmpeg are self-contained in the `python\` folder — nothing installed system-wide
- Re-launching `reclip.bat` automatically clears any stale server process

## License

MIT — see [LICENSE](LICENSE). This tool is provided as-is with no warranty. You are responsible for your own use.
