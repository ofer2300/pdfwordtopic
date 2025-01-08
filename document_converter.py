import argparse
import logging
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm

from document_analyzer import DocumentAnalyzer, DocumentInfo
from image_processor import ImageProcessor
from cache_manager import CacheManager
from security_manager import SecurityManager

class DocumentConverter:
    """ממיר מסמכים חכם עם תכונות מתקדמות"""
    
    def __init__(self, 
                 output_dir: str,
                 cache_dir: str = None,
                 security_dir: str = None,
                 max_workers: int = None,
                 batch_size: int = 10):
        
        # הגדרת לוגים
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # הגדרת נתיבים
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # אתחול רכיבים
        self.document_analyzer = DocumentAnalyzer()
        self.image_processor = ImageProcessor()
        self.cache_manager = CacheManager(
            cache_dir or str(Path.home() / '.document_converter' / 'cache')
        )
        self.security_manager = SecurityManager(
            security_dir or str(Path.home() / '.document_converter' / 'security')
        )
        
        # הגדרות עיבוד
        self.max_workers = max_workers
        self.batch_size = batch_size
        
        self.logger.info("מערכת המרת מסמכים אותחלה בהצלחה")

    def convert_files(self,
                     file_paths: List[str],
                     format: str = 'png',
                     quality: int = 95,
                     dpi: int = 300,
                     optimize: bool = True,
                     encrypt: bool = False,
                     validate: bool = True) -> bool:
        """המרת קבצים לתמונות
        
        Args:
            file_paths: רשימת נתיבי קבצים
            format: פורמט התמונות
            quality: איכות התמונות (1-100)
            dpi: רזולוציה
            optimize: אופטימיזציה אוטומטית
            encrypt: הצפנת הפלט
            validate: אימות קבצים
            
        Returns:
            bool: האם ההמרה הצליחה
        """
        try:
            total_files = len(file_paths)
            successful_files = 0
            
            self.logger.info(f"מתחיל המרה של {total_files} קבצים")
            
            # עיבוד הקבצים
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                # הגשת משימות
                for file_path in file_paths:
                    if validate and not self.security_manager.validate_file(file_path):
                        self.logger.warning(f"הקובץ {file_path} נכשל באימות")
                        continue
                        
                    futures.append(
                        executor.submit(
                            self._convert_single_file,
                            file_path,
                            format,
                            quality,
                            dpi,
                            optimize,
                            encrypt
                        )
                    )
                
                # המתנה לתוצאות
                for future in tqdm(futures, desc="מעבד קבצים"):
                    if future.result():
                        successful_files += 1
            
            success_rate = (successful_files / total_files) * 100
            self.logger.info(f"הסתיימה המרה של {successful_files}/{total_files} קבצים ({success_rate:.1f}%)")
            
            return successful_files > 0
            
        except Exception as e:
            self.logger.error(f"שגיאה בהמרת קבצים: {str(e)}")
            return False

    def _convert_single_file(self,
                           file_path: str,
                           format: str,
                           quality: int,
                           dpi: int,
                           optimize: bool,
                           encrypt: bool) -> bool:
        """המרת קובץ בודד
        
        Args:
            file_path: נתיב הקובץ
            format: פורמט התמונות
            quality: איכות התמונות
            dpi: רזולוציה
            optimize: אופטימיזציה אוטומטית
            encrypt: הצפנת הפלט
            
        Returns:
            bool: האם ההמרה הצליחה
        """
        try:
            # ניתוח המסמך
            doc_info = self.document_analyzer.analyze_document(file_path)
            
            # בדיקת מטמון
            cache_key = f"{file_path}:{format}:{quality}:{dpi}:{optimize}"
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data:
                self.logger.info(f"נמצא במטמון: {file_path}")
                return self._save_cached_images(cached_data, doc_info, encrypt)
            
            # המרה לתמונות
            images = self._convert_to_images(doc_info)
            if not images:
                return False
            
            # עיבוד תמונות
            processed_images = []
            for img in images:
                processed = self.image_processor.process_image(
                    img,
                    target_dpi=dpi,
                    target_format=format,
                    quality=quality,
                    optimize=optimize
                )
                processed_images.append(processed)
            
            # שמירת תמונות
            output_paths = self._save_images(
                processed_images,
                doc_info,
                format,
                quality,
                encrypt
            )
            
            # שמירה במטמון
            if output_paths:
                self.cache_manager.set(cache_key, output_paths)
                
            return bool(output_paths)
            
        except Exception as e:
            self.logger.error(f"שגיאה בהמרת הקובץ {file_path}: {str(e)}")
            return False

    def _convert_to_images(self, doc_info: DocumentInfo) -> List:
        """המרת מסמך לתמונות
        
        Args:
            doc_info: מידע על המסמך
            
        Returns:
            List: רשימת תמונות
        """
        # TODO: לממש המרה ספציפית לכל סוג קובץ
        pass

    def _save_images(self,
                    images: List,
                    doc_info: DocumentInfo,
                    format: str,
                    quality: int,
                    encrypt: bool) -> List[str]:
        """שמירת תמונות
        
        Args:
            images: רשימת תמונות
            doc_info: מידע על המסמך
            format: פורמט התמונות
            quality: איכות התמונות
            encrypt: האם להצפין
            
        Returns:
            List[str]: רשימת נתיבי הקבצים שנשמרו
        """
        try:
            output_paths = []
            
            for i, image in enumerate(images, 1):
                # יצירת שם קובץ
                output_name = f"{Path(doc_info.file_path).stem}_{i:03d}.{format.lower()}"
                output_path = self.output_dir / output_name
                
                # שמירת התמונה
                image.save(
                    output_path,
                    format=format.upper(),
                    quality=quality,
                    optimize=True
                )
                
                # הצפנה אם נדרש
                if encrypt:
                    with open(output_path, 'rb') as f:
                        encrypted_data = self.security_manager.encrypt_data(f.read())
                    with open(output_path, 'wb') as f:
                        f.write(encrypted_data)
                
                output_paths.append(str(output_path))
            
            return output_paths
            
        except Exception as e:
            self.logger.error(f"שגיאה בשמירת תמונות: {str(e)}")
            return []

    def _save_cached_images(self,
                          cached_data: List[str],
                          doc_info: DocumentInfo,
                          encrypt: bool) -> bool:
        """שמירת תמונות מהמטמון
        
        Args:
            cached_data: נתיבי תמונות מהמטמון
            doc_info: מידע על המסמך
            encrypt: האם להצפין
            
        Returns:
            bool: האם השמירה הצליחה
        """
        try:
            for cache_path in cached_data:
                # העתקת הקובץ מהמטמון
                with open(cache_path, 'rb') as f:
                    data = f.read()
                    
                # הצפנה אם נדרש
                if encrypt:
                    data = self.security_manager.encrypt_data(data)
                    
                # שמירה בתיקיית הפלט
                output_path = self.output_dir / Path(cache_path).name
                with open(output_path, 'wb') as f:
                    f.write(data)
                    
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בשמירת תמונות מהמטמון: {str(e)}")
            return False

    def _setup_logging(self):
        """הגדרת לוגים"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # הגדרת פורמט
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # לוג ראשי
        main_handler = logging.FileHandler('logs/converter.log', encoding='utf-8')
        main_handler.setFormatter(formatter)
        
        # לוג שגיאות
        error_handler = logging.FileHandler('logs/errors.log', encoding='utf-8')
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # הגדרת לוגר
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)

def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description="ממיר מסמכים חכם לתמונות")
    
    # פרמטרים בסיסיים
    parser.add_argument(
        'files',
        nargs='+',
        help="נתיבי הקבצים להמרה"
    )
    
    # פרמטרי תמונה
    parser.add_argument(
        '--format',
        choices=['png', 'jpg', 'webp'],
        default='png',
        help="פורמט התמונות"
    )
    parser.add_argument(
        '--quality',
        type=int,
        choices=range(1, 101),
        default=95,
        help="איכות התמונות (1-100)"
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help="רזולוציית התמונות"
    )
    
    # פרמטרי עיבוד
    parser.add_argument(
        '--optimize',
        action='store_true',
        help="אופטימיזציה אוטומטית"
    )
    parser.add_argument(
        '--workers',
        type=int,
        help="מספר תהליכים במקביל"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help="גודל אצווה לעיבוד"
    )
    
    # פרמטרי אבטחה
    parser.add_argument(
        '--encrypt',
        action='store_true',
        help="הצפנת הפלט"
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help="אימות קבצים"
    )
    
    # פרמטרי מערכת
    parser.add_argument(
        '--output-dir',
        default='output',
        help="תיקיית פלט"
    )
    parser.add_argument(
        '--cache-dir',
        help="תיקיית מטמון"
    )
    parser.add_argument(
        '--security-dir',
        help="תיקיית אבטחה"
    )
    
    args = parser.parse_args()
    
    # יצירת הממיר
    converter = DocumentConverter(
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        security_dir=args.security_dir,
        max_workers=args.workers,
        batch_size=args.batch_size
    )
    
    # המרת הקבצים
    success = converter.convert_files(
        args.files,
        format=args.format,
        quality=args.quality,
        dpi=args.dpi,
        optimize=args.optimize,
        encrypt=args.encrypt,
        validate=args.validate
    )
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main()) 