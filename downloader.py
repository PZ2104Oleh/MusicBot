import os
import tempfile
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

def download_audio(url):
    # Получаем cookies из переменной окружения
    raw_cookies = os.getenv("YT_COOKIES", "")
    if not raw_cookies:
        raise Exception("No cookies found in environment variable 'YT_COOKIES'")

    # Заменяем \n на реальные переносы строк
    fixed_cookies = raw_cookies.replace("\\n", "\n")

    # Создаем временный файл cookies
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as cookie_file:
        cookie_file.write(fixed_cookies)
        cookie_file_path = cookie_file.name

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': cookie_file_path,
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info_dict).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    except DownloadError as e:
        raise Exception(f"Download error: {e}")
    finally:
        # Удаляем временный файл cookie
        if os.path.exists(cookie_file_path):
            os.remove(cookie_file_path)
