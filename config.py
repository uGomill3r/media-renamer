from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_PATH = BASE_DIR / 'uploads'
#MEDIA_PATH = '/mnt/HDD/Library'
MEDIA_PATH = '/Volumes/NAS/Library'

VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.vtt', '.sub']

SECRET_KEY = "6efdd6116ae6569e5d0fdca0be9a8644"  # Reemplazar en producción
