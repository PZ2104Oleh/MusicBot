import os
import yt_dlp
import hashlib
import json

def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()

def search_youtube(query, limit=1):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': f'ytsearch{limit}',
        'quiet': True,
        'cookiefile': 'cookies.txt',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        entries = info.get('entries', [])
        return [{
            'title': e['title'],
            'url': e['webpage_url']
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
        'cookiefile': 'cookies.txt',
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