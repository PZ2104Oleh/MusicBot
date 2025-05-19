import os
import yt_dlp
import hashlib
import json
import tempfile

# Создать временный файл cookies.txt из переменной окружения
def write_temp_cookies():
    raw_cookies = os.getenv("YT_COOKIES", "")
    if not raw_cookies:
        raise Exception("YT_COOKIES env var is missing")
    fixed_cookies = raw_cookies.replace("\\n", "\n")
    temp = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt")
    temp.write(fixed_cookies)
    temp.close()
    return temp.name

def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()

def search_youtube(query, limit=1):
    cookie_path = write_temp_cookies()
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': f'ytsearch{limit}',
        'quiet': True,
        'cookiefile': cookie_path,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [])
            return [{
                'title': e['title'],
                'url': e['webpage_url']
            } for e in entries]
    finally:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

def download_audio_file(url, output_dir):
    file_hash = hash_url(url)
    mp3_path = os.path.join(output_dir, f"{file_hash}.mp3")
    meta_path = os.path.join(output_dir, f"{file_hash}.json")

    if os.path.exists(mp3_path) and os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        return mp3_path, meta.get('title')

    cookie_path = write_temp_cookies()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f"{file_hash}.%(ext)s"),
        'quiet': True,
        'cookiefile': cookie_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            with open(meta_path, 'w') as f:
                json.dump({'title': info['title']}, f)
            return mp3_path, info['title']
    finally:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
