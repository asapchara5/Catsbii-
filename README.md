# CATSBI — Video Downloader
招き猫 × Y2K × RuTracker vibes. Powered by yt-dlp.

## What it does
Downloads videos from YouTube, TikTok, Instagram, and Facebook
directly on your own server — no third-party sites, no redirects.

## Stack
- **Backend**: Python + Flask + yt-dlp
- **Frontend**: Pure HTML/CSS/JS (no frameworks)
- **FFmpeg**: Required for audio extraction and video merging

---

## Deploy on Railway (FREE, easiest)

1. Create account at https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Upload this folder to a GitHub repo first, then connect it
   OR use "New Project" → "Empty project" → drag & drop this folder
4. Railway auto-detects `nixpacks.toml` and installs ffmpeg + python
5. Your site is live at `yourapp.railway.app` in ~2 minutes

---

## Deploy on Render (FREE)

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo with this code
3. Set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python app.py`
4. Add environment: Python 3.11
5. NOTE: Render free tier sleeps after 15min inactivity

---

## Deploy on a VPS (DigitalOcean, Hetzner, etc.)

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3 python3-pip ffmpeg -y

# 2. Upload this folder to your server, then:
cd catsbi_app
pip3 install -r requirements.txt

# 3. Run (dev)
python3 app.py

# 4. Run with gunicorn (production)
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 5. Point nginx to port 5000 and add SSL with certbot
```

---

## Local dev / testing

```bash
# Install ffmpeg first:
# Mac:     brew install ffmpeg
# Ubuntu:  sudo apt install ffmpeg
# Windows: download from ffmpeg.org

pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

---

## Notes
- Files are auto-deleted after 1 hour
- No database needed — jobs stored in memory
- For high traffic, add Redis + a job queue (Celery)
- yt-dlp updates frequently — run `pip install -U yt-dlp` to keep it fresh
