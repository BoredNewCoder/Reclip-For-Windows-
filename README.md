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
3. *(optional)* Toggle **Subtitles (EN)**, pick a **Codec** preference
4. Click **Fetch** — shows available formats with quality, codec, and file size
5. Select quality (higher resolution = larger file)
6. *(optional)* Fill in **Clip** start / end times to download just a section
7. Click **Download** — real-time progress bar shows download % · file saves to `downloads\` folder
8. Click **Pause** to pause a download and resume it later — or **Cancel** to stop and discard it

### Subtitles

The **Subtitles (EN)** toggle grabs English captions (auto-generated when there's no
human track). You get both: a `.srt` file next to the video, and — for MP4 — the track
embedded in the file itself.

### Codec preference

**Codec: Auto / H.264 / AV1 / VP9.** H.264 is the most compatible (every player and
editor); AV1 and VP9 are smaller but pickier. Picking a codec grabs the best quality
available *in that codec* — so it takes over from the per-video quality buttons.

### Clipping

Each result card has an optional **Clip** row — a start and an end time. Leave both
blank for the whole video; fill one or both to grab just a section:

- Formats accepted: `90` (seconds), `1:30` (mm:ss), or `1:02:03` (hh:mm:ss)
- Start only → from that point to the end · End only → from the beginning to that point
- Cuts are frame-accurate (`--force-keyframes-at-cuts`)
- Works for MP4 **and** MP3 · clipped files get a ` [clip]` name suffix

### Batch Downloads

Paste multiple URLs (spaces, commas, or newlines), then click **Download All**. Every
item is queued at once, but only a few download at a time (default 3 — set
`MAX_CONCURRENT` to change) so a long list doesn't hammer your machine or trip bot
detection. Queued items show a **Queued** state; live progress per item.

Downloads are saved to the `downloads\` folder inside the ReClip directory.

## Features

- **Clip a section** — download just the part you want, by start/end time (mp4 or mp3)
- **Subtitles** — English `.srt` sidecar + embedded track (MP4)
- **Codec preference** — force H.264 for compatibility, or AV1/VP9 for smaller files
- **Remove Sponsors** — automatically skips sponsor segments via SponsorBlock (YouTube)
- **Bypass Detection** — uses [curl-cffi](https://github.com/lexiforest/curl-cffi) to impersonate Chrome's TLS fingerprint, bypassing bot detection on sites like YouTube that block standard download tools
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

## Network Access

ReClip binds to `127.0.0.1` (this machine only) and has **no authentication**. If you
override `HOST` to expose it on your network, anyone who can reach the port can
download through your IP and read your `downloads\` folder — it prints a warning when
you do. Leave it on localhost unless you know what you're doing.

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
- yt-dlp updates automatically on each launch — the running version shows in the footer, with an **update now** link if you leave ReClip open for a while
- Python and FFmpeg are self-contained in `python\` — nothing installed system-wide
- Re-launching `reclip.bat` clears any stale server process

## License

MIT — see [LICENSE](LICENSE). Provided as-is, no warranty. You are responsible for your own use.


## Support

If this saved you time or you just want to say thanks:

**Cash App:** [$CVanZetta](https://cash.app/$CVanZetta)
