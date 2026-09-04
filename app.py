import os
import sys
import uuid
import glob
import json
import shutil
import sqlite3
import tempfile
import subprocess
import threading
import time
import re
import webbrowser
import static_ffmpeg
from html import unescape
from flask import Flask, request, jsonify, send_file, render_template

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

app = Flask(__name__, template_folder=os.path.join(RESOURCE_DIR, "templates"))
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload size
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
JOBS_DIR = os.path.join(BASE_DIR, ".jobs")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
YTDLP = [sys.executable, "-m", "yt_dlp"]

# ffmpeg + ffprobe. static-ffmpeg downloads both on first add_paths() and puts them
# on PATH; a bundled ffmpeg\ dir next to the app wins if present. (ffprobe matters —
# SponsorBlock needs it, which is why imageio-ffmpeg, ffmpeg-only, was dropped.)
static_ffmpeg.add_paths()
local_ffmpeg_dir = os.path.join(BASE_DIR, "ffmpeg")
if os.path.isdir(local_ffmpeg_dir):
    FFMPEG_DIR = local_ffmpeg_dir
else:
    _ffmpeg_bin = shutil.which("ffmpeg")
    FFMPEG_DIR = os.path.dirname(_ffmpeg_bin) if _ffmpeg_bin else ""

if FFMPEG_DIR:
    os.environ['PATH'] = FFMPEG_DIR + os.pathsep + os.environ.get('PATH', '')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

# Cap on how many downloads actually run at once. "Download All" still queues every
# item immediately, but only this many hit the network — keeps 20 links from
# spawning 20 yt-dlp+ffmpeg processes and tripping rate limits / bot detection.
MAX_CONCURRENT = max(1, int(os.environ.get("MAX_CONCURRENT", "3")))
_download_sem = threading.BoundedSemaphore(MAX_CONCURRENT)

# Windows can't create a file named after a reserved device, even with an extension.
_WIN_RESERVED = {"CON", "PRN", "AUX", "NUL"} \
    | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


def base_cmd(impersonate=False):
    cmd = YTDLP + ["--no-playlist",
                   "--retries", "50", "--fragment-retries", "50", "--retry-sleep", "5"]
    if FFMPEG_DIR:
        cmd += ["--ffmpeg-location", FFMPEG_DIR]
    if os.path.isfile(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    if impersonate:
        cmd += ["--impersonate", "chrome"]
    return cmd


# yt-dlp --download-sections wants "*START-END" with times as SS, MM:SS, HH:MM:SS, or "inf".
def parse_timecode(v):
    """'' / None -> None. '90' / '1:30' / '01:02:03' -> seconds (float). Raises ValueError."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) > 3 or not all(p.strip() != "" for p in parts):
        raise ValueError(f"bad timecode: {v!r}")
    total = 0.0
    for p in parts:
        total = total * 60 + float(p)
    if total < 0:
        raise ValueError("timecode cannot be negative")
    return total


def clip_section_arg(start_sec, end_sec):
    """Returns the '*START-END' string for --download-sections, or None if no clip."""
    if start_sec is None and end_sec is None:
        return None
    s = start_sec if start_sec is not None else 0.0
    e = end_sec if end_sec is not None else None
    return f"*{s:g}-{e:g}" if e is not None else f"*{s:g}-inf"


jobs = {}
jobs_lock = threading.Lock()


def save_job_state(job_id):
    job = jobs.get(job_id)
    if not job:
        return
    state = {
        "job_id": job_id,
        "status": job.get("status"),
        "url": job.get("url", ""),
        "title": job.get("title", ""),
        "thumbnail": job.get("thumbnail", ""),
        "uploader": job.get("uploader", ""),
        "source": job.get("source", ""),
        "duration": job.get("duration"),
        "format_choice": job.get("format_choice", "video"),
        "format_id": job.get("format_id"),
        "sponsorblock": job.get("sponsorblock", False),
        "impersonate": job.get("impersonate", False),
        "clip_start": job.get("clip_start"),
        "clip_end": job.get("clip_end"),
        "progress": job.get("progress", 0),
        "created": job.get("created", time.time()),
    }
    try:
        with open(os.path.join(JOBS_DIR, f"{job_id}.json"), "w") as f:
            json.dump(state, f)
    except OSError:
        pass


def delete_job_state(job_id):
    try:
        os.remove(os.path.join(JOBS_DIR, f"{job_id}.json"))
    except OSError:
        pass


def run_download(job_id, url, format_choice, format_id, sponsorblock=False, resume=False,
                 impersonate=False, clip_start=None, clip_end=None):
    if job_id not in jobs:
        return
    job = jobs[job_id]
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    cmd = base_cmd(impersonate=impersonate) + ["-o", out_template]

    if resume:
        cmd += ["--continue"]

    # SponsorBlock: cut the sponsor segments out of the file entirely (needs ffmpeg re-mux).
    if sponsorblock:
        cmd += ["--sponsorblock-remove", "sponsor"]

    # Clip: download only the requested slice. --force-keyframes-at-cuts makes the
    # boundaries frame-accurate (a re-encode of the edge GOPs) instead of snapping to
    # the nearest keyframe.
    section = clip_section_arg(clip_start, clip_end)
    if section:
        cmd += ["--download-sections", section, "--force-keyframes-at-cuts"]

    if format_choice == "audio":
        cmd += ["-x", "--audio-format", "mp3"]
    elif format_id:
        cmd += ["-f", f"{format_id}+bestaudio/best", "--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]

    cmd.append(url)

    # Wait for a concurrency slot. The job shows as "queued" while it blocks here.
    with jobs_lock:
        if job.get("status") != "downloading":
            return
        job["phase"] = "queued"
    _download_sem.acquire()
    sem_held = True
    try:
        with jobs_lock:
            if job.get("status") != "downloading":
                return
            job["phase"] = None

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        with jobs_lock:
            job["proc"] = proc

        def _kill_on_timeout():
            try:
                proc.kill()
            except Exception:
                pass
            with jobs_lock:
                if job.get("status") == "downloading":
                    job["status"] = "error"
                    job["error"] = "Download timed out after 2 hours"

        timeout_timer = threading.Timer(7200, _kill_on_timeout)
        timeout_timer.start()

        last_error = ""
        _pp_re = re.compile(r'\[(Merger|ExtractAudio|SponsorBlock|VideoRemuxer|VideoConvertor|Fixup\w*|Metadata|EmbedSubtitle|SplitChapters)\]')
        try:
            for line in proc.stdout:
                last_error = line.strip()
                match = re.search(r'\[download\]\s+([\d.]+)%', line)
                if match:
                    with jobs_lock:
                        if job.get("status") == "downloading":
                            job["progress"] = float(match.group(1))
                            job["phase"] = None
                elif _pp_re.search(line):
                    with jobs_lock:
                        if job.get("status") == "downloading":
                            job["phase"] = "processing"
        except Exception:
            pass
        finally:
            timeout_timer.cancel()

        try:
            returncode = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            returncode = -1

        with jobs_lock:
            if job.get("status") != "downloading":
                return

        if returncode != 0:
            with jobs_lock:
                job["status"] = "error"
                job["error"] = last_error if last_error else "Download failed"
            delete_job_state(job_id)
            return

        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
        if not files:
            with jobs_lock:
                job["status"] = "error"
                job["error"] = "Download completed but no file was found"
            return

        if format_choice == "audio":
            target = [f for f in files if f.endswith(".mp3")]
            chosen = target[0] if target else files[0]
        else:
            target = [f for f in files if f.endswith(".mp4")]
            chosen = target[0] if target else files[0]

        for f in files:
            if f != chosen:
                try:
                    os.remove(f)
                except OSError:
                    pass

        ext = os.path.splitext(chosen)[1]

        def sanitize(s):
            s = "".join(ch for ch in s if ch not in r'\/:*?"<>|' and ord(ch) >= 32)
            s = s.strip().strip(".").strip()
            if s.upper() in _WIN_RESERVED or s.split(".")[0].upper() in _WIN_RESERVED:
                s = "_" + s
            return s

        title = sanitize(job.get("title", ""))
        uploader = sanitize(job.get("uploader", ""))
        source = sanitize(job.get("source", ""))
        clip_tag = " [clip]" if section else ""

        if title:
            parts = [title[:100]]
            if uploader:
                parts.append(uploader[:50])
            if source:
                parts.append(source[:30])
            final_name = " - ".join(parts) + clip_tag + ext
        else:
            final_name = os.path.splitext(os.path.basename(chosen))[0] + clip_tag + ext

        stem, suffix = os.path.splitext(final_name)
        final_path = os.path.join(DOWNLOAD_DIR, final_name)
        counter = 1
        while os.path.exists(final_path) and final_path != chosen:
            final_path = os.path.join(DOWNLOAD_DIR, f"{stem} ({counter}){suffix}")
            counter += 1
        if final_path != chosen:
            try:
                if os.path.exists(chosen):
                    shutil.move(chosen, final_path)
                    chosen = final_path
            except OSError:
                pass

        with jobs_lock:
            job["status"] = "done"
            job["progress"] = 100
            job["phase"] = None
            job["file"] = chosen
            job["filename"] = os.path.basename(chosen)
        delete_job_state(job_id)
    except Exception as e:
        with jobs_lock:
            if job.get("status") == "downloading":
                job["status"] = "error"
                job["error"] = str(e)
        delete_job_state(job_id)
    finally:
        if sem_held:
            _download_sem.release()


@app.route("/favicon.svg")
def favicon():
    return send_file(os.path.join(RESOURCE_DIR, "templates", "favicon.svg"), mimetype="image/svg+xml")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    impersonate = data.get("impersonate", False)
    cmd = base_cmd(impersonate=impersonate) + ["-j", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip().split("\n")[-1]}), 400

        info = json.loads(result.stdout)

        if info.get("_has_drm"):
            return jsonify({"error": "This video is DRM-protected and cannot be downloaded."}), 400

        def is_video_fmt(f):
            vcodec = f.get("vcodec") or "none"
            video_ext = f.get("video_ext") or "none"
            return vcodec not in ("none", "") or video_ext not in ("none", "")

        def is_audio_fmt(f):
            audio_ext = f.get("audio_ext") or "none"
            return audio_ext not in ("none", "")

        all_formats = info.get("formats", [])
        best_by_height = {}
        for f in all_formats:
            height = f.get("height")
            if not height or not is_video_fmt(f):
                continue
            width = f.get("width") or 0
            if width and width < height:
                continue
            tbr = f.get("tbr") or 0
            if height not in best_by_height or tbr > (best_by_height[height].get("tbr") or 0):
                best_by_height[height] = f

        def format_filesize(bytes_val):
            if not bytes_val:
                return None
            size = float(bytes_val)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f}".rstrip('0').rstrip('.') + unit
                size /= 1024
            return f"{size:.1f}".rstrip('0').rstrip('.') + "TB"

        formats = []
        for height, f in best_by_height.items():
            filesize = f.get("filesize") or f.get("filesize_approx")
            size_str = format_filesize(filesize) if filesize else None
            vcodec = f.get("vcodec", "").split('.')[0] if f.get("vcodec") else ""
            codec_str = f"{vcodec}" if vcodec and vcodec != "none" else ""

            label = f"{height}p"
            if size_str:
                label += f" · {size_str}"
            if codec_str:
                label += f" · {codec_str}"

            formats.append({
                "id": f["format_id"],
                "label": label,
                "height": height,
                "filesize": size_str,
                "codec": codec_str,
            })
        formats.sort(key=lambda x: x["height"], reverse=True)

        if not formats and not any(is_video_fmt(f) or is_audio_fmt(f) for f in all_formats):
            return jsonify({"error": "No downloadable formats found."}), 400

        return jsonify({
            "title": unescape(info.get("title", "")),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "source": info.get("extractor_key", ""),
            "formats": formats,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Network timeout fetching video info. Check your connection and try again."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    sponsorblock = data.get("sponsorblock", False)
    impersonate = data.get("impersonate", False)

    title = data.get("title", "")
    thumbnail = data.get("thumbnail", "")
    uploader = data.get("uploader", "")
    source = data.get("source", "")
    duration = data.get("duration")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        clip_start = parse_timecode(data.get("clip_start"))
        clip_end = parse_timecode(data.get("clip_end"))
    except ValueError:
        return jsonify({"error": "Clip times must look like 90, 1:30, or 01:02:03."}), 400
    if clip_start is not None and clip_end is not None and clip_end <= clip_start:
        return jsonify({"error": "Clip end must be after the start."}), 400

    cutoff = time.time() - 3600
    with jobs_lock:
        for jid in [k for k, v in jobs.items() if v.get("created", time.time()) < cutoff]:
            jobs.pop(jid, None)

        while True:
            job_id = uuid.uuid4().hex[:16]
            if job_id not in jobs:
                break
        jobs[job_id] = {
            "status": "downloading",
            "url": url,
            "title": title,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "source": source,
            "duration": duration,
            "created": time.time(),
            "progress": 0,
            "format_choice": format_choice,
            "format_id": format_id,
            "sponsorblock": sponsorblock,
            "impersonate": impersonate,
            "clip_start": clip_start,
            "clip_end": clip_end,
        }

    save_job_state(job_id)
    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id, sponsorblock),
                             kwargs={"impersonate": impersonate, "clip_start": clip_start, "clip_end": clip_end})
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify({
            "status": job["status"],
            "error": job.get("error"),
            "filename": job.get("filename"),
            "progress": job.get("progress", 0),
            "phase": job.get("phase"),
        })


@app.route("/api/file/<job_id>")
def download_file(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job or job["status"] != "done":
            return jsonify({"error": "File not ready"}), 404
        file_path = job["file"]
        filename = job["filename"]
    return send_file(file_path, as_attachment=True, download_name=filename)


@app.route("/api/pause/<job_id>", methods=["POST"])
def pause_download(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        proc = job.get("proc")
        job["status"] = "paused"
    if proc:
        try:
            proc.kill()
        except Exception:
            pass
    save_job_state(job_id)
    return jsonify({"ok": True})


@app.route("/api/resume/<job_id>", methods=["POST"])
def resume_download(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if job["status"] != "paused":
            return jsonify({"error": "Job is not paused"}), 400
        job["status"] = "downloading"
        job["proc"] = None
        url = job["url"]
        format_choice = job["format_choice"]
        format_id = job["format_id"]
        sponsorblock = job["sponsorblock"]
        impersonate = job.get("impersonate", False)
        clip_start = job.get("clip_start")
        clip_end = job.get("clip_end")

    save_job_state(job_id)
    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id, sponsorblock),
                             kwargs={"resume": True, "impersonate": impersonate,
                                     "clip_start": clip_start, "clip_end": clip_end})
    thread.daemon = True
    thread.start()
    return jsonify({"ok": True})


@app.route("/api/cancel/<job_id>", methods=["POST"])
def cancel_download(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        proc = job.get("proc")
        job["status"] = "cancelled"
        job["error"] = "Cancelled"
    if proc:
        try:
            proc.kill()
        except Exception:
            pass
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*")):
        try:
            os.remove(f)
        except OSError:
            pass
    delete_job_state(job_id)
    return jsonify({"ok": True})


def recover_jobs():
    for path in glob.glob(os.path.join(JOBS_DIR, "*.json")):
        try:
            with open(path) as f:
                state = json.load(f)
            job_id = state.get("job_id")
            status = state.get("status")
            if not job_id or status not in ("downloading", "paused"):
                os.remove(path)
                continue
            with jobs_lock:
                jobs[job_id] = {
                    "status": status,
                    "url": state.get("url", ""),
                    "title": state.get("title", ""),
                    "thumbnail": state.get("thumbnail", ""),
                    "uploader": state.get("uploader", ""),
                    "source": state.get("source", ""),
                    "duration": state.get("duration"),
                    "format_choice": state.get("format_choice", "video"),
                    "format_id": state.get("format_id"),
                    "sponsorblock": state.get("sponsorblock", False),
                    "impersonate": state.get("impersonate", False),
                    "clip_start": state.get("clip_start"),
                    "clip_end": state.get("clip_end"),
                    "progress": state.get("progress", 0),
                    "created": state.get("created", time.time()),
                }
            if status == "downloading":
                url = state.get("url", "")
                format_choice = state.get("format_choice", "video")
                format_id = state.get("format_id")
                sponsorblock = state.get("sponsorblock", False)
                impersonate = state.get("impersonate", False)
                thread = threading.Thread(
                    target=run_download,
                    args=(job_id, url, format_choice, format_id, sponsorblock),
                    kwargs={"resume": True, "impersonate": impersonate,
                            "clip_start": state.get("clip_start"), "clip_end": state.get("clip_end")}
                )
                thread.daemon = True
                thread.start()
        except Exception:
            pass


@app.route("/api/jobs")
def list_jobs():
    with jobs_lock:
        active = [
            {
                "job_id": jid,
                "status": job["status"],
                "url": job.get("url", ""),
                "title": job.get("title", ""),
                "thumbnail": job.get("thumbnail", ""),
                "uploader": job.get("uploader", ""),
                "source": job.get("source", ""),
                "duration": job.get("duration"),
                "progress": job.get("progress", 0),
                "phase": job.get("phase"),
            }
            for jid, job in jobs.items()
            if job.get("status") in ("downloading", "paused")
        ]
    return jsonify(active)


def find_firefox_cookies():
    roaming = os.environ.get("APPDATA", "")
    profiles_dir = os.path.join(roaming, "Mozilla", "Firefox", "Profiles")
    if not os.path.isdir(profiles_dir):
        return None
    candidates = glob.glob(os.path.join(profiles_dir, "*.default-release")) + \
                 glob.glob(os.path.join(profiles_dir, "*.default"))
    return os.path.join(candidates[0], "cookies.sqlite") if candidates else None


def firefox_sqlite_to_netscape(sqlite_path):
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        tmp_path = tmp.name
    shutil.copy2(sqlite_path, tmp_path)
    try:
        con = sqlite3.connect(tmp_path)
        try:
            cur = con.execute("SELECT host, path, isSecure, expiry, name, value FROM moz_cookies")
            lines = ["# Netscape HTTP Cookie File"]
            for host, path, secure, expiry, name, value in cur.fetchall():
                include_sub = "TRUE" if host.startswith(".") else "FALSE"
                secure_str = "TRUE" if secure else "FALSE"
                lines.append(f"{host}\t{include_sub}\t{path}\t{secure_str}\t{expiry}\t{name}\t{value}")
        finally:
            con.close()
        return "\n".join(lines)
    finally:
        os.unlink(tmp_path)


@app.route("/api/cookies/status")
def cookies_status():
    active = os.path.isfile(COOKIES_FILE)
    firefox_db = find_firefox_cookies()
    return jsonify({
        "active": active,
        "firefox_available": firefox_db is not None,
    })


@app.route("/api/cookies/from-firefox", methods=["POST"])
def import_from_firefox():
    db = find_firefox_cookies()
    if not db:
        return jsonify({"error": "Firefox not found"}), 400
    try:
        content = firefox_sqlite_to_netscape(db)
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        count = content.count("\n")
        return jsonify({"ok": True, "cookies": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cookies/upload", methods=["POST"])
def upload_cookies():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file provided"}), 400
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > 10 * 1024 * 1024:
        return jsonify({"error": "File too large (max 10MB)"}), 400
    f.save(COOKIES_FILE)
    return jsonify({"ok": True})


@app.route("/api/cookies/clear", methods=["POST"])
def clear_cookies():
    if os.path.isfile(COOKIES_FILE):
        os.remove(COOKIES_FILE)
    return jsonify({"ok": True})


if __name__ == "__main__":
    recover_jobs()
    port = int(os.environ.get("PORT", 8899))
    host = os.environ.get("HOST", "127.0.0.1")

    if host not in ("127.0.0.1", "localhost", "::1"):
        print(
            f"\n  !! ReClip has NO authentication. Bound to {host}:{port} — anyone who can\n"
            f"     reach this machine on that port can download through your IP and read\n"
            f"     your downloads/ folder. Use the default 127.0.0.1 unless you mean this.\n"
        )

    def open_browser():
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    threading.Timer(1.5, open_browser).start()
    app.run(host=host, port=port)