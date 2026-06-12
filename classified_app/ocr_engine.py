"""
OCR Engine - Convert PDF/Images to Text
"""

import os
import logging
import tempfile
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import easyocr
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine:
    """Handle OCR processing for various document formats"""
    
    def __init__(self, use_easyocr=True):
        self.use_easyocr = use_easyocr
        if use_easyocr:
            try:
                self.reader = easyocr.Reader(['en', 'te'])  # English and Telugu
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}, falling back to Tesseract")
                self.use_easyocr = False
    
    def process_pdf(self, pdf_path, dpi=300):
        """
        Convert PDF to images and extract text
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion
        
        Returns:
            dict with 'pages' list containing text and image info
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=dpi)
            pages_data = []
            
            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing page {page_num}/{len(images)}")
                
                page_text = self._extract_text_from_image(image)
                
                pages_data.append({
                    'page_number': page_num,
                    'text': page_text,
                    'confidence': self._calculate_confidence(page_text),
                    'image_info': {
                        'width': image.width,
                        'height': image.height,
                    }
                })
            
            logger.info(f"PDF processing completed. Total pages: {len(pages_data)}")
            
            return {
                'status': 'success',
                'total_pages': len(pages_data),
                'pages': pages_data
            }
        
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'pages': []
            }
    
    def process_image(self, image_path):
        """
        Extract text from a single image
        
        Args:
            image_path: Path to image file
        
        Returns:
            dict with extracted text and metadata
        """
        try:
            logger.info(f"Processing image: {image_path}")
            
            image = Image.open(image_path)
            text = self._extract_text_from_image(image)
            
            return {
                'status': 'success',
                'text': text,
                'confidence': self._calculate_confidence(text),
                'image_info': {
                    'width': image.width,
                    'height': image.height,
                    'format': image.format,
                }
            }
        
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'text': ''
            }
    
    def _extract_text_from_image(self, image):
        """Extract text using configured OCR engine"""
        if self.use_easyocr:
            return self._extract_with_easyocr(image)
        else:
            return self._extract_with_tesseract(image)
    
    def _extract_with_easyocr(self, image):
        """Extract text using EasyOCR"""
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Perform OCR
            results = self.reader.readtext(img_array)
            
            # Extract and join text
            text = '\n'.join([result[1] for result in results])
            return text
        
        except Exception as e:
            logger.warning(f"EasyOCR extraction failed: {e}, trying Tesseract")
            return self._extract_with_tesseract(image)
    
    def _extract_with_tesseract(self, image):
        """Extract text using Tesseract OCR"""
        try:
            text = pytesseract.image_to_string(image, lang='eng+tel')
            return text
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return ""
    
    def _calculate_confidence(self, text):
        """
        Calculate confidence score based on text quality
        
        Returns:
            float between 0 and 1
        """
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Simple heuristic: longer text = higher confidence
        text_length = len(text)
        confidence = min(0.95, text_length / 1000)  # Max 0.95
        
        return round(confidence, 2)
    
    def preprocess_image(self, image_path, output_path=None):
        """
        Preprocess image for better OCR results
        
        Args:
            image_path: Input image path
            output_path: Optional output path for preprocessed image
        
        Returns:
            Preprocessed image object
        """
        try:
            image = Image.open(image_path)
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)
            
            if output_path:
                image.save(output_path)
            
            return image
        
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return None
    
    def batch_process_pdf(self, pdf_path, output_dir=None):
        """
        Process PDF and save individual page images
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save page images
        
        Returns:
            dict with processing results
        """
        try:
            if not output_dir:
                output_dir = tempfile.mkdtemp()
            
            os.makedirs(output_dir, exist_ok=True)
            
            images = convert_from_path(pdf_path)
            saved_paths = []
            
            for i, image in enumerate(images, 1):
                output_path = os.path.join(output_dir, f'page_{i:03d}.png')
                image.save(output_path, 'PNG')
                saved_paths.append(output_path)
                logger.info(f"Saved page {i} to {output_path}")
            
            return {
                'status': 'success',
                'total_pages': len(saved_paths),
                'output_dir': output_dir,
                'saved_paths': saved_paths
            }
        
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Initialize OCR Engine
ocr_engine = OCREngine()
