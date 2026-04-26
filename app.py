import os
import uuid
import threading
import time
from flask import Flask, request, jsonify, send_file, render_template, abort
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

jobs = {}

ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "instagram.com",
    "facebook.com", "fb.watch",
]

def is_allowed(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        host = urlparse(url).hostname or ""
        return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False

def do_download(job_id: str, url: str, quality: str, fmt: str):
    job = jobs[job_id]
    out_tmpl = os.path.join(DOWNLOAD_DIR, job_id + "_%(title).80s.%(ext)s")

    format_str = "bestvideo+bestaudio/best"
    if quality == "1080":
        format_str = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif quality == "720":
        format_str = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif quality == "480":
        format_str = "bestvideo[height<=480]+bestaudio/best[height<=480]"
    elif quality == "360":
        format_str = "bestvideo[height<=360]+bestaudio/best[height<=360]"

    ydl_opts = {
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    if fmt == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
        ydl_opts.pop("merge_output_format", None)
    else:
        ydl_opts["format"] = format_str

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(job_id)]
            if not files:
                raise Exception("Downloaded file not found")
            filename = files[0]
            job["status"] = "done"
            job["filename"] = filename
            job["title"] = info.get("title", "video")
            job["duration"] = info.get("duration", 0)
            job["thumbnail"] = info.get("thumbnail", "")
            job["ext"] = filename.rsplit(".", 1)[-1]
            job["filesize"] = os.path.getsize(os.path.join(DOWNLOAD_DIR, filename))
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json(force=True)
    url     = (data.get("url") or "").strip()
    quality = data.get("quality", "max")
    fmt     = data.get("format", "video")

    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not is_allowed(url):
        return jsonify({"error": "Unsupported platform"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "url": url}

    thread = threading.Thread(target=do_download, args=(job_id, url, quality, fmt), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/file/<job_id>")
def serve_file(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        abort(404)
    filepath = os.path.join(DOWNLOAD_DIR, job["filename"])
    if not os.path.exists(filepath):
        abort(404)
    return send_file(
        filepath,
        as_attachment=True,
        download_name=job["filename"].split("_", 1)[-1],
    )


def cleanup_loop():
    while True:
        time.sleep(300)
        now = time.time()
        for fname in os.listdir(DOWNLOAD_DIR):
            fpath = os.path.join(DOWNLOAD_DIR, fname)
            try:
                if now - os.path.getmtime(fpath) > 3600:
                    os.remove(fpath)
            except Exception:
                pass

threading.Thread(target=cleanup_loop, daemon=True).start()

if __name__ == "__main__":
    # Railway injects PORT environment variable — must use it
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
