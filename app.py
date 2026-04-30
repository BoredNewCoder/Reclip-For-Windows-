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
from html import unescape
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")
YTDLP = [sys.executable, "-m", "yt_dlp"]
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def base_cmd():
    cmd = YTDLP + ["--no-playlist", "--js-runtimes", "node", "--remote-components", "ejs:github"]
    if os.path.isfile(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]
    return cmd

jobs = {}
jobs_lock = threading.Lock()


def run_download(job_id, url, format_choice, format_id):
    job = jobs[job_id]
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    cmd = base_cmd() + ["-o", out_template]

    if format_choice == "audio":
        cmd += ["-x", "--audio-format", "mp3"]
    elif format_id:
        cmd += ["-f", f"{format_id}+bestaudio/best", "--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]

    cmd.append(url)

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        last_error = ""

        for line in proc.stdout:
            last_error = line.strip()
            match = re.search(r'\[download\]\s+([\d.]+)%', line)
            if match:
                with jobs_lock:
                    job["progress"] = float(match.group(1))

        returncode = proc.wait()
        if returncode != 0:
            with jobs_lock:
                job["status"] = "error"
                job["error"] = last_error if last_error else "Download failed"
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
            return "".join(ch for ch in s if ch not in r'\/:*?"<>|').strip()

        title = sanitize(job.get("title", ""))
        uploader = sanitize(job.get("uploader", ""))
        source = sanitize(job.get("source", ""))

        if title:
            parts = [title[:100]]
            if uploader:
                parts.append(uploader[:50])
            if source:
                parts.append(source[:30])
            final_name = " - ".join(parts) + ext
        else:
            final_name = os.path.basename(chosen)

        stem, suffix = os.path.splitext(final_name)
        final_path = os.path.join(DOWNLOAD_DIR, final_name)
        counter = 1
        while os.path.exists(final_path) and final_path != chosen:
            final_path = os.path.join(DOWNLOAD_DIR, f"{stem} ({counter}){suffix}")
            counter += 1
        if final_path != chosen:
            try:
                shutil.move(chosen, final_path)
                chosen = final_path
            except OSError:
                pass

        with jobs_lock:
            job["status"] = "done"
            job["progress"] = 100
            job["file"] = chosen
            job["filename"] = os.path.basename(chosen)
    except subprocess.TimeoutExpired:
        with jobs_lock:
            job["status"] = "error"
            job["error"] = "Download timed out (5 min limit)"
    except Exception as e:
        with jobs_lock:
            job["status"] = "error"
            job["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cmd = base_cmd() + ["-j", url]
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

        # Build quality options — keep best landscape format per resolution
        all_formats = info.get("formats", [])
        best_by_height = {}
        for f in all_formats:
            height = f.get("height")
            if not height or not is_video_fmt(f):
                continue
            # Skip portrait orientations
            width = f.get("width") or 0
            if width and width < height:
                continue
            tbr = f.get("tbr") or 0
            if height not in best_by_height or tbr > (best_by_height[height].get("tbr") or 0):
                best_by_height[height] = f

        def format_filesize(bytes_val):
            if not bytes_val:
                return None
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_val < 1024:
                    return f"{bytes_val:.1f}{unit}".replace('.0', '')
                bytes_val /= 1024
            return f"{bytes_val:.1f}TB"

        formats = []
        for height, f in best_by_height.items():
            filesize = f.get("filesize") or f.get("filesize_approx")
            size_str = format_filesize(filesize) if filesize else None
            vcodec = f.get("vcodec", "").split('.')[0] if f.get("vcodec") else ""
            acodec = f.get("acodec", "").split('.')[0] if f.get("acodec") else ""
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
        return jsonify({"error": "Timed out fetching video info"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    title = data.get("title", "")
    uploader = data.get("uploader", "")
    source = data.get("source", "")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Prune jobs older than 1 hour
    cutoff = time.time() - 3600
    with jobs_lock:
        for jid in [k for k, v in jobs.items() if v.get("created", 0) < cutoff]:
            jobs.pop(jid, None)

        job_id = uuid.uuid4().hex[:10]
        jobs[job_id] = {"status": "downloading", "url": url, "title": title, "uploader": uploader, "source": source, "created": time.time(), "progress": 0}

    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    with jobs_lock:
        return jsonify({
            "status": job["status"],
            "error": job.get("error"),
            "filename": job.get("filename"),
            "progress": job.get("progress", 0),
        })


@app.route("/api/file/<job_id>")
def download_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "File not ready"}), 404
    return send_file(job["file"], as_attachment=True, download_name=job["filename"])


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
            cur = con.execute(
                "SELECT host, path, isSecure, expiry, name, value FROM moz_cookies"
            )
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
    f.save(COOKIES_FILE)
    return jsonify({"ok": True})


@app.route("/api/cookies/clear", methods=["POST"])
def clear_cookies():
    if os.path.isfile(COOKIES_FILE):
        os.remove(COOKIES_FILE)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8899))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port)
