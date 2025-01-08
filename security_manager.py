import os
import json
from pathlib import Path
from typing import Optional, Dict
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import re
import requests
from urllib.parse import urlparse
import magic

class SecurityManager:
    """מנהל אבטחה מתקדם עם הצפנה ואימות"""
    
    def __init__(self, keys_dir: str):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # טעינת או יצירת מפתח הצפנה
        self.encryption_key = self._load_or_create_key()
        self.fernet = Fernet(self.encryption_key)
        
        # רשימת סוגי קבצים מורשים
        self.allowed_mime_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/html',
            'text/plain'
        }
        
        # רשימת דומיינים חסומים
        self.blocked_domains = set()
        self._load_blocked_domains()
        
        # הגדרות אבטחה
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_url_size = 10 * 1024 * 1024    # 10MB

    def validate_file(self, file_path: str) -> bool:
        """אימות קובץ
        
        Args:
            file_path: נתיב הקובץ
            
        Returns:
            bool: האם הקובץ תקין ומאובטח
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"הקובץ {file_path} לא קיים")
                return False
                
            # בדיקת גודל
            if path.stat().st_size > self.max_file_size:
                self.logger.warning(f"הקובץ {file_path} גדול מדי")
                return False
                
            # בדיקת סוג הקובץ
            mime_type = magic.from_file(str(path), mime=True)
            if mime_type not in self.allowed_mime_types:
                self.logger.warning(f"סוג הקובץ {mime_type} אינו נתמך")
                return False
                
            # בדיקת תוכן זדוני
            if self._contains_malicious_content(path):
                self.logger.warning(f"נמצא תוכן חשוד בקובץ {file_path}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה באימות הקובץ {file_path}: {str(e)}")
            return False

    def validate_url(self, url: str) -> bool:
        """אימות כתובת URL
        
        Args:
            url: הכתובת לבדיקה
            
        Returns:
            bool: האם הכתובת תקינה ומאובטחת
        """
        try:
            # בדיקת פורמט
            if not re.match(r'^https?://', url):
                self.logger.warning(f"פרוטוקול לא נתמך: {url}")
                return False
                
            # ניתוח הכתובת
            parsed = urlparse(url)
            
            # בדיקת דומיין חסום
            if parsed.netloc in self.blocked_domains:
                self.logger.warning(f"דומיין חסום: {parsed.netloc}")
                return False
                
            # בדיקת תגובה
            response = requests.head(url, allow_redirects=True, timeout=5)
            
            # בדיקת קוד תגובה
            if response.status_code != 200:
                self.logger.warning(f"קוד תגובה לא תקין: {response.status_code}")
                return False
                
            # בדיקת גודל
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_url_size:
                self.logger.warning(f"התוכן גדול מדי: {content_length} bytes")
                return False
                
            # בדיקת סוג תוכן
            content_type = response.headers.get('content-type', '').split(';')[0]
            if content_type not in self.allowed_mime_types:
                self.logger.warning(f"סוג תוכן לא נתמך: {content_type}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה באימות הכתובת {url}: {str(e)}")
            return False

    def encrypt_data(self, data: bytes) -> bytes:
        """הצפנת מידע
        
        Args:
            data: המידע להצפנה
            
        Returns:
            bytes: המידע המוצפן
        """
        try:
            return self.fernet.encrypt(data)
        except Exception as e:
            self.logger.error(f"שגיאה בהצפנת מידע: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """פענוח מידע מוצפן
        
        Args:
            encrypted_data: המידע המוצפן
            
        Returns:
            bytes: המידע המקורי
        """
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            self.logger.error(f"שגיאה בפענוח מידע: {str(e)}")
            raise

    def _load_or_create_key(self) -> bytes:
        """טעינה או יצירה של מפתח הצפנה"""
        key_file = self.keys_dir / 'encryption.key'
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return base64.urlsafe_b64decode(f.read())
                
        # יצירת מפתח חדש
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(base64.urlsafe_b64encode(key))
        return key

    def _load_blocked_domains(self):
        """טעינת רשימת דומיינים חסומים"""
        domains_file = self.keys_dir / 'blocked_domains.json'
        if domains_file.exists():
            try:
                with open(domains_file, 'r') as f:
                    self.blocked_domains = set(json.load(f))
            except Exception as e:
                self.logger.error(f"שגיאה בטעינת דומיינים חסומים: {str(e)}")

    def _contains_malicious_content(self, path: Path) -> bool:
        """בדיקת תוכן זדוני בקובץ"""
        try:
            # בדיקת תבניות חשודות
            with open(path, 'rb') as f:
                content = f.read()
                
            # בדיקת סקריפטים
            if b'<script' in content or b'javascript:' in content:
                return True
                
            # בדיקת קוד הרצה
            if b'eval(' in content or b'exec(' in content:
                return True
                
            # בדיקת פקודות מערכת
            if b'system(' in content or b'shell_exec(' in content:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"שגיאה בבדיקת תוכן זדוני: {str(e)}")
            return True  # במקרה של ספק, נחשיב כחשוד 