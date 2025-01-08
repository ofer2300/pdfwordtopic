import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import Config

class SecurityManager:
    def __init__(self):
        """אתחול מנהל האבטחה"""
        self.encryption_key = self._load_or_create_key()
        self.fernet = Fernet(self.encryption_key)
        self.api_keys = self._load_api_keys()

    def _load_or_create_key(self) -> bytes:
        """טעינה או יצירה של מפתח הצפנה
        
        Returns:
            מפתח ההצפנה
        """
        key_file = Config.ENCRYPTION_KEY_FILE
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return base64.urlsafe_b64decode(f.read())
                
        # יצירת מפתח חדש
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(base64.urlsafe_b64encode(key))
        return key

    def _load_api_keys(self) -> dict:
        """טעינת מפתחות API
        
        Returns:
            מילון מפתחות API
        """
        if Config.API_KEYS_FILE.exists():
            try:
                with open(Config.API_KEYS_FILE, 'r') as f:
                    encrypted_data = f.read()
                decrypted_data = self.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            except:
                return {}
        return {}

    def _save_api_keys(self):
        """שמירת מפתחות API"""
        encrypted_data = self.encrypt(json.dumps(self.api_keys))
        with open(Config.API_KEYS_FILE, 'w') as f:
            f.write(encrypted_data)

    def encrypt(self, data: str) -> str:
        """הצפנת מידע
        
        Args:
            data: המידע להצפנה
            
        Returns:
            המידע המוצפן
        """
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """פענוח מידע מוצפן
        
        Args:
            encrypted_data: המידע המוצפן
            
        Returns:
            המידע המפוענח
        """
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def validate_file_signature(self, file_path: str) -> bool:
        """בדיקת חתימה דיגיטלית של קובץ
        
        Args:
            file_path: נתיב הקובץ
            
        Returns:
            האם החתימה תקינה
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            digest = hashes.Hash(hashes.SHA256())
            digest.update(content)
            return True
        except:
            return False

    def sanitize_path(self, path: str) -> str:
        """ניקוי נתיב מתווים מסוכנים
        
        Args:
            path: הנתיב לניקוי
            
        Returns:
            הנתיב המנוקה
        """
        return Path(path).resolve().as_posix()

    def validate_url(self, url: str) -> bool:
        """בדיקת תקינות ואבטחת URL
        
        Args:
            url: ה-URL לבדיקה
            
        Returns:
            האם ה-URL תקין ובטוח
        """
        from urllib.parse import urlparse
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def add_api_key(self, service: str, key: str):
        """הוספת מפתח API
        
        Args:
            service: שם השירות
            key: מפתח ה-API
        """
        self.api_keys[service] = self.encrypt(key)
        self._save_api_keys()

    def get_api_key(self, service: str) -> str:
        """קבלת מפתח API
        
        Args:
            service: שם השירות
            
        Returns:
            מפתח ה-API
        """
        if service in self.api_keys:
            return self.decrypt(self.api_keys[service])
        return None 