import magic
import hashlib
from pathlib import Path
from typing import Dict, Optional
import logging
from dataclasses import dataclass

@dataclass
class DocumentInfo:
    """מחלקה לאחסון מידע על המסמך"""
    mime_type: str
    file_type: str
    encoding: Optional[str]
    file_hash: str
    size_bytes: int
    page_count: Optional[int] = None
    language: Optional[str] = None
    is_encrypted: bool = False
    metadata: Dict = None

class DocumentAnalyzer:
    """מנתח מסמכים מתקדם עם זיהוי חכם"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.magic_instance = magic.Magic(mime=True)
        self.metadata_extractors = {
            'application/pdf': self._extract_pdf_metadata,
            'application/msword': self._extract_doc_metadata,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_docx_metadata,
            'text/html': self._extract_html_metadata
        }

    def analyze_document(self, file_path: str) -> DocumentInfo:
        """ניתוח מקיף של המסמך
        
        Args:
            file_path: נתיב לקובץ
            
        Returns:
            DocumentInfo: מידע מפורט על המסמך
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"הקובץ {file_path} לא נמצא")

        try:
            # זיהוי סוג הקובץ
            mime_type = self.magic_instance.from_file(str(path))
            
            # חישוב hash של הקובץ
            file_hash = self._calculate_file_hash(path)
            
            # מידע בסיסי
            info = DocumentInfo(
                mime_type=mime_type,
                file_type=path.suffix.lower(),
                encoding=self._detect_encoding(path),
                file_hash=file_hash,
                size_bytes=path.stat().st_size,
                metadata={}
            )
            
            # חילוץ מטא-דאטה ספציפי לסוג הקובץ
            if mime_type in self.metadata_extractors:
                self.metadata_extractors[mime_type](path, info)
            
            return info
            
        except Exception as e:
            self.logger.error(f"שגיאה בניתוח המסמך {file_path}: {str(e)}")
            raise

    def _calculate_file_hash(self, path: Path) -> str:
        """חישוב hash של הקובץ"""
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _detect_encoding(self, path: Path) -> Optional[str]:
        """זיהוי קידוד הקובץ"""
        try:
            import chardet
            with open(path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding']
        except:
            return None

    def _extract_pdf_metadata(self, path: Path, info: DocumentInfo):
        """חילוץ מטא-דאטה מקובץ PDF"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            info.page_count = len(reader.pages)
            info.metadata = reader.metadata
            info.is_encrypted = reader.is_encrypted
        except Exception as e:
            self.logger.warning(f"שגיאה בחילוץ מטא-דאטה מ-PDF: {str(e)}")

    def _extract_docx_metadata(self, path: Path, info: DocumentInfo):
        """חילוץ מטא-דאטה מקובץ DOCX"""
        try:
            from docx import Document
            doc = Document(path)
            info.page_count = len(doc.sections)
            info.metadata = {
                'title': doc.core_properties.title,
                'author': doc.core_properties.author,
                'created': doc.core_properties.created,
                'modified': doc.core_properties.modified
            }
        except Exception as e:
            self.logger.warning(f"שגיאה בחילוץ מטא-דאטה מ-DOCX: {str(e)}")

    def _extract_doc_metadata(self, path: Path, info: DocumentInfo):
        """חילוץ מטא-דאטה מקובץ DOC"""
        try:
            import olefile
            with olefile.OleFileIO(str(path)) as ole:
                info.metadata = ole.get_metadata()
        except Exception as e:
            self.logger.warning(f"שגיאה בחילוץ מטא-דאטה מ-DOC: {str(e)}")

    def _extract_html_metadata(self, path: Path, info: DocumentInfo):
        """חילוץ מטא-דאטה מקובץ HTML"""
        try:
            from bs4 import BeautifulSoup
            with open(path, 'r', encoding=info.encoding or 'utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                info.metadata = {
                    'title': soup.title.string if soup.title else None,
                    'meta_tags': {
                        tag.get('name', tag.get('property')): tag.get('content')
                        for tag in soup.find_all('meta')
                    }
                }
        except Exception as e:
            self.logger.warning(f"שגיאה בחילוץ מטא-דאטה מ-HTML: {str(e)}") 