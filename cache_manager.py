import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict
import logging
from threading import Lock
import shutil

class CacheManager:
    """מנהל מטמון מתקדם עם תמיכה בפריטים מרובים"""
    
    def __init__(self, cache_dir: str, max_size_bytes: int = 1024*1024*1024, ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_bytes
        self.ttl_seconds = ttl_seconds
        self.metadata_file = self.cache_dir / 'metadata.json'
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)
        
        # יצירת תיקיית המטמון אם לא קיימת
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # טעינת מטא-דאטה
        self.metadata = self._load_metadata()
        
        # ניקוי פריטים שפג תוקפם
        self._cleanup_expired()

    def get(self, key: str) -> Optional[Any]:
        """קבלת פריט מהמטמון
        
        Args:
            key: מפתח הפריט
            
        Returns:
            Any: הפריט המבוקש או None אם לא נמצא
        """
        with self.lock:
            try:
                cache_path = self._get_cache_path(key)
                if not cache_path.exists():
                    return None
                
                # בדיקת תוקף
                metadata = self.metadata.get(key, {})
                if time.time() - metadata.get('timestamp', 0) > self.ttl_seconds:
                    self._remove_item(key)
                    return None
                
                # קריאת הפריט
                with open(cache_path, 'rb') as f:
                    return f.read()
                    
            except Exception as e:
                self.logger.error(f"שגיאה בקריאה מהמטמון: {str(e)}")
                return None

    def set(self, key: str, value: Any, metadata: Dict = None) -> bool:
        """שמירת פריט במטמון
        
        Args:
            key: מפתח הפריט
            value: הערך לשמירה
            metadata: מטא-דאטה נוסף
            
        Returns:
            bool: האם השמירה הצליחה
        """
        with self.lock:
            try:
                # בדיקת מקום פנוי
                if self._get_cache_size() > self.max_size_bytes:
                    self._cleanup_old_items()
                
                # שמירת הפריט
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'wb') as f:
                    if isinstance(value, (str, bytes)):
                        f.write(value if isinstance(value, bytes) else value.encode())
                    else:
                        f.write(json.dumps(value).encode())
                
                # עדכון מטא-דאטה
                self.metadata[key] = {
                    'timestamp': time.time(),
                    'size': cache_path.stat().st_size,
                    **metadata or {}
                }
                self._save_metadata()
                return True
                
            except Exception as e:
                self.logger.error(f"שגיאה בשמירה למטמון: {str(e)}")
                return False

    def invalidate(self, key: str) -> bool:
        """ביטול תוקף פריט במטמון
        
        Args:
            key: מפתח הפריט
            
        Returns:
            bool: האם הביטול הצליח
        """
        with self.lock:
            return self._remove_item(key)

    def clear(self) -> bool:
        """ניקוי כל המטמון
        
        Returns:
            bool: האם הניקוי הצליח
        """
        with self.lock:
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True)
                self.metadata = {}
                self._save_metadata()
                return True
            except Exception as e:
                self.logger.error(f"שגיאה בניקוי המטמון: {str(e)}")
                return False

    def _get_cache_path(self, key: str) -> Path:
        """יצירת נתיב לפריט במטמון"""
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / hashed_key

    def _load_metadata(self) -> Dict:
        """טעינת מטא-דאטה"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"שגיאה בטעינת מטא-דאטה: {str(e)}")
        return {}

    def _save_metadata(self) -> bool:
        """שמירת מטא-דאטה"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
            return True
        except Exception as e:
            self.logger.error(f"שגיאה בשמירת מטא-דאטה: {str(e)}")
            return False

    def _cleanup_expired(self):
        """ניקוי פריטים שפג תוקפם"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.metadata.items()
            if current_time - data.get('timestamp', 0) > self.ttl_seconds
        ]
        for key in expired_keys:
            self._remove_item(key)

    def _cleanup_old_items(self):
        """ניקוי פריטים ישנים כשהמטמון מלא"""
        if not self.metadata:
            return
            
        # מיון לפי זמן שימוש אחרון
        sorted_items = sorted(
            self.metadata.items(),
            key=lambda x: x[1].get('timestamp', 0)
        )
        
        # מחיקת פריטים ישנים עד שיש מספיק מקום
        current_size = self._get_cache_size()
        for key, _ in sorted_items:
            if current_size <= self.max_size_bytes * 0.8:  # שמירת 20% רזרבה
                break
            item_size = self.metadata[key].get('size', 0)
            if self._remove_item(key):
                current_size -= item_size

    def _remove_item(self, key: str) -> bool:
        """הסרת פריט מהמטמון"""
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
            self.metadata.pop(key, None)
            self._save_metadata()
            return True
        except Exception as e:
            self.logger.error(f"שגיאה בהסרת פריט מהמטמון: {str(e)}")
            return False

    def _get_cache_size(self) -> int:
        """חישוב גודל המטמון הנוכחי"""
        return sum(
            f.stat().st_size
            for f in self.cache_dir.glob('*')
            if f.is_file()
        ) 