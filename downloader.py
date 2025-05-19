import os
import yt_dlp
import hashlib
import json

COOKIES_FILE = 'cookies.txt'

def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()

def search_youtube(query, limit=1):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': f'ytsearch{limit}',
        'quiet': True,
        'cookiefile': COOKIES_FILE,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        entries = info.get('entries', [])
        return [{
            'title': e['title'],
            'url': e['webpage_url']
        } for e in entries]

def extract_playlist(playlist_url):
    ydl_opts = {
        'quiet': True,
        'cookiefile': COOKIES_FILE,
        'extract_flat': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        entries = info.get('entries', [])
        return [{
            'title': e.get('title'),
            'url': e.get('url') if e.get('url', '').startswith('http') else f"https://www.youtube.com/watch?v={e['id']}"
        } for e in entries]

def download_audio_file(url, output_dir):
    file_hash = hash_url(url)
    mp3_path = os.path.join(output_dir, f"{file_hash}.mp3")
    meta_path = os.path.join(output_dir, f"{file_hash}.json")

    if os.path.exists(mp3_path) and os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        return mp3_path, meta.get('title')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f"{file_hash}.%(ext)s"),
        'quiet': True,
        'cookiefile': COOKIES_FILE,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        with open(meta_path, 'w') as f:
            json.dump({'title': info['title']}, f)
        return mp3_path, info['title']
