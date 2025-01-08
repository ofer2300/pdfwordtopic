import os
import sys
import urllib.request
import zipfile
import subprocess
from pathlib import Path

def setup_poppler():
    """התקנת והגדרת Poppler באופן אוטומטי"""
    poppler_path = Path("C:/poppler")
    
    # הורדת Poppler אם לא קיים
    if not poppler_path.exists():
        print("מוריד Poppler...")
        poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
        zip_path = "poppler.zip"
        
        # הורדת הקובץ
        urllib.request.urlretrieve(poppler_url, zip_path)
        
        # חילוץ הקובץ
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("C:/")
        
        # מחיקת קובץ ה-ZIP
        os.remove(zip_path)
    
    # הוספת Poppler ל-PATH
    bin_path = str(poppler_path / "bin")
    if bin_path not in os.environ['PATH']:
        os.environ['PATH'] = bin_path + os.pathsep + os.environ['PATH']
        
        # עדכון PATH במערכת
        subprocess.run(['setx', 'PATH', f"%PATH%;{bin_path}"], capture_output=True)

def install_requirements():
    """התקנת חבילות Python הנדרשות"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    """פונקציית התקנה ראשית"""
    print("מתחיל התקנה אוטומטית...")
    
    # התקנת Poppler
    setup_poppler()
    
    # התקנת חבילות Python
    install_requirements()
    
    print("\nההתקנה הושלמה בהצלחה!")
    print("כעת ניתן להריץ את התוכנה עם הפקודה:")
    print("python document_converter.py [path-to-file]")

if __name__ == "__main__":
    main() 