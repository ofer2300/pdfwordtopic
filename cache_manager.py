import os
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional
from config import Config

class CacheManager:
    def __init__(self):
        """אתחול מנהל המטמון"""
        self.cache_dir = Config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / 'metadata.json'
        self.metadata = self._load_metadata()
        self._cleanup_old_entries()

    def _load_metadata(self) -> dict:
        """טעינת מטא-דאטה של המטמון"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_metadata(self):
        """שמירת מטא-דאטה של המטמון"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def _get_cache_key(self, key: str) -> str:
        """יצירת מפתח מטמון מוצפן
        
        Args:
            key: המפתח המקורי
            
        Returns:
            מפתח מוצפן
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def _cleanup_old_entries(self):
        """ניקוי רשומות ישנות מהמטמון"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, metadata in self.metadata.items():
            if current_time - metadata['timestamp'] > Config.CACHE_TTL:
                keys_to_remove.append(key)
                cache_file = self.cache_dir / f"{key}.cache"
                if cache_file.exists():
                    cache_file.unlink()
                    
        for key in keys_to_remove:
            del self.metadata[key]
            
        if keys_to_remove:
            self._save_metadata()

    def get(self, key: str) -> Optional[Any]:
        """קבלת ערך מהמטמון
        
        Args:
            key: מפתח הערך
            
        Returns:
            הערך המבוקש או None אם לא נמצא
        """
        if not Config.CACHE_ENABLED:
            return None
            
        cache_key = self._get_cache_key(key)
        if cache_key not in self.metadata:
            return None
            
        metadata = self.metadata[cache_key]
        if time.time() - metadata['timestamp'] > Config.CACHE_TTL:
            return None
            
        cache_file = self.cache_dir / f"{cache_key}.cache"
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'rb') as f:
                return f.read()
        except:
            return None

    def set(self, key: str, value: Any):
        """שמירת ערך במטמון
        
        Args:
            key: מפתח הערך
            value: הערך לשמירה
        """
        if not Config.CACHE_ENABLED:
            return
            
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        try:
            with open(cache_file, 'wb') as f:
                f.write(value)
                
            self.metadata[cache_key] = {
                'timestamp': time.time(),
                'size': len(value)
            }
            self._save_metadata()
            
        except Exception as e:
            print(f"שגיאה בשמירה במטמון: {str(e)}")

    def clear(self):
        """ניקוי כל המטמון"""
        for file in self.cache_dir.glob('*.cache'):
            file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        self.metadata = {} 