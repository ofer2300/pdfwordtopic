from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from typing import Tuple, Optional, Dict
import cv2
from dataclasses import dataclass
import logging

@dataclass
class ImageQuality:
    """מחלקה לאחסון מדדי איכות תמונה"""
    sharpness: float
    brightness: float
    contrast: float
    noise_level: float
    dpi: int
    size: Tuple[int, int]
    format: str
    color_depth: int

class ImageProcessor:
    """מעבד תמונות מתקדם עם אופטימיזציה אוטומטית"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.quality_thresholds = {
            'sharpness': 0.5,
            'brightness': 0.4,
            'contrast': 0.4,
            'noise': 0.3
        }

    def process_image(self, 
                     image: Image.Image,
                     target_dpi: int = 300,
                     target_format: str = 'PNG',
                     quality: int = 95,
                     optimize: bool = True) -> Image.Image:
        """עיבוד מתקדם של תמונה
        
        Args:
            image: תמונת המקור
            target_dpi: רזולוציה רצויה
            target_format: פורמט רצוי
            quality: איכות התמונה (1-100)
            optimize: האם לבצע אופטימיזציה אוטומטית
            
        Returns:
            Image.Image: התמונה המעובדת
        """
        try:
            # המרה ל-RGB אם צריך
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # בדיקת איכות התמונה
            quality_metrics = self._analyze_quality(image)
            
            if optimize:
                # שיפור חדות
                if quality_metrics.sharpness < self.quality_thresholds['sharpness']:
                    image = self._enhance_sharpness(image)
                
                # שיפור בהירות
                if quality_metrics.brightness < self.quality_thresholds['brightness']:
                    image = self._enhance_brightness(image)
                
                # שיפור ניגודיות
                if quality_metrics.contrast < self.quality_thresholds['contrast']:
                    image = self._enhance_contrast(image)
                
                # הפחתת רעש
                if quality_metrics.noise_level > self.quality_thresholds['noise']:
                    image = self._reduce_noise(image)
            
            # התאמת רזולוציה
            image = self._adjust_dpi(image, target_dpi)
            
            return image
            
        except Exception as e:
            self.logger.error(f"שגיאה בעיבוד התמונה: {str(e)}")
            raise

    def _analyze_quality(self, image: Image.Image) -> ImageQuality:
        """ניתוח איכות התמונה"""
        # המרה למערך numpy
        img_array = np.array(image)
        
        # חישוב חדות
        laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
        sharpness = min(1.0, laplacian_var / 500)
        
        # חישוב בהירות
        brightness = np.mean(img_array) / 255
        
        # חישוב ניגודיות
        contrast = np.std(img_array) / 128
        
        # חישוב רמת רעש
        noise = self._estimate_noise(img_array)
        
        return ImageQuality(
            sharpness=sharpness,
            brightness=brightness,
            contrast=contrast,
            noise_level=noise,
            dpi=image.info.get('dpi', (72, 72))[0],
            size=image.size,
            format=image.format or 'UNKNOWN',
            color_depth=image.mode
        )

    def _enhance_sharpness(self, image: Image.Image) -> Image.Image:
        """שיפור חדות התמונה"""
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(1.5)

    def _enhance_brightness(self, image: Image.Image) -> Image.Image:
        """שיפור בהירות התמונה"""
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.2)

    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """שיפור ניגודיות התמונה"""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.3)

    def _reduce_noise(self, image: Image.Image) -> Image.Image:
        """הפחתת רעש בתמונה"""
        return image.filter(ImageFilter.MedianFilter(size=3))

    def _adjust_dpi(self, image: Image.Image, target_dpi: int) -> Image.Image:
        """התאמת רזולוציית התמונה"""
        if 'dpi' in image.info:
            current_dpi = image.info['dpi'][0]
            if current_dpi != target_dpi:
                scale = target_dpi / current_dpi
                new_size = tuple(int(dim * scale) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        image.info['dpi'] = (target_dpi, target_dpi)
        return image

    def _estimate_noise(self, img_array: np.ndarray) -> float:
        """הערכת רמת הרעש בתמונה"""
        # שימוש בפילטר מדיאני להערכת רעש
        median_filtered = cv2.medianBlur(img_array, 3)
        noise = np.mean(np.abs(img_array - median_filtered)) / 255
        return noise 