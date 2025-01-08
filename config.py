from pathlib import Path
import os

class Config:
    # נתיבי מערכת
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR = Path(r"C:\Users\user\Documents\pdf_output")
    TEMP_DIR = BASE_DIR / "temp"
    CACHE_DIR = BASE_DIR / "cache"
    LOG_DIR = BASE_DIR / "logs"

    # הגדרות קובץ
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_PAGES = 500
    SUPPORTED_FORMATS = {
        'pdf': ['.pdf'],
        'word': ['.docx', '.doc'],
        'html': ['.html', '.htm'],
        'url': ['http://', 'https://']
    }

    # הגדרות תמונה
    IMAGE_FORMATS = {
        'png': {'ext': '.png', 'quality': 95},
        'jpg': {'ext': '.jpg', 'quality': 90},
        'webp': {'ext': '.webp', 'quality': 85}
    }
    DEFAULT_IMAGE_FORMAT = 'png'
    DEFAULT_DPI = 300
    DEFAULT_IMAGE_SIZE = (1920, 1080)
    
    # הגדרות עיבוד
    BATCH_SIZE = 10
    MAX_WORKERS = os.cpu_count()
    CHUNK_SIZE = 1024 * 1024  # 1MB
    
    # הגדרות אבטחה
    ALLOWED_HOSTS = ['*']
    API_KEYS_FILE = BASE_DIR / 'api_keys.json'
    ENCRYPTION_KEY_FILE = BASE_DIR / 'encryption.key'
    
    # הגדרות מטמון
    CACHE_ENABLED = True
    CACHE_TTL = 3600  # שעה
    MAX_CACHE_SIZE = 1024 * 1024 * 1024  # 1GB
    
    # הגדרות לוג
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    @classmethod
    def init_directories(cls):
        """יצירת כל התיקיות הנדרשות"""
        for dir_path in [cls.OUTPUT_DIR, cls.TEMP_DIR, cls.CACHE_DIR, cls.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_file(cls, file_path: str) -> bool:
        """בדיקת תקינות הקובץ
        
        Args:
            file_path: נתיב הקובץ
            
        Returns:
            האם הקובץ תקין
        """
        path = Path(file_path)
        
        # בדיקת קיום הקובץ
        if not path.exists():
            return False
            
        # בדיקת גודל
        if path.stat().st_size > cls.MAX_FILE_SIZE:
            return False
            
        # בדיקת סיומת
        ext = path.suffix.lower()
        for format_exts in cls.SUPPORTED_FORMATS.values():
            if ext in format_exts:
                return True
                
        return False

    @classmethod
    def is_url(cls, path: str) -> bool:
        """בדיקה האם הנתיב הוא URL
        
        Args:
            path: הנתיב לבדיקה
            
        Returns:
            האם הנתיב הוא URL
        """
        return any(path.startswith(prefix) for prefix in cls.SUPPORTED_FORMATS['url']) 