#!/usr/bin/env python3
"""
OpenCV-Based Text Extraction for Guidewire Forms

This script uses OpenCV for advanced image preprocessing and text extraction
specifically optimized for form analysis.
"""

import cv2
import numpy as np
from PIL import Image
import json
import argparse
import sys
from pathlib import Path

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    print("[WARNING] EasyOCR not available - please install: pip install easyocr")
    EASYOCR_AVAILABLE = False


class OpenCVTextExtractor:
    """Advanced OpenCV-based text extractor for form images."""
    
    def __init__(self, image_path, confidence_threshold=30):
        self.image_path = Path(image_path)
        self.confidence_threshold = confidence_threshold
        self.original_image = None
        self.processed_image = None
        self.text_blocks = []
        
        # Initialize EasyOCR if available
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                print("[INIT] Initializing EasyOCR...")
                self.easyocr_reader = easyocr.Reader(['en'], verbose=False)
                print("   [READY] EasyOCR ready")
            except Exception as e:
                print(f"   [WARNING] EasyOCR initialization failed: {e}")
                self.easyocr_reader = None
        
    def load_image(self):
        """Load and validate the input image."""
        try:
            if not self.image_path.exists():
                raise FileNotFoundError(f"Image file not found: {self.image_path}")
            
            # Load with OpenCV directly
            self.original_image = cv2.imread(str(self.image_path))
            if self.original_image is None:
                raise ValueError("Could not load image with OpenCV")
            
            print(f"[LOADED] Image loaded: {self.original_image.shape[:2][::-1]} pixels")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error loading image: {e}")
            return False
    
    def preprocess_image(self):
        """Advanced preprocessing optimized for form text extraction."""
        print("[PROC] Applying advanced OpenCV preprocessing...")
        
        # Convert to grayscale
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        
        # Apply multiple preprocessing techniques
        
        # 1. Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)
        
        # 2. Noise reduction
        denoised = cv2.medianBlur(contrast_enhanced, 3)
        
        # 3. Morphological operations to enhance text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        morphed = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        
        # 4. Thresholding to get clean binary image
        # Try adaptive threshold first
        adaptive_thresh = cv2.adaptiveThreshold(
            morphed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Also try Otsu's threshold
        _, otsu_thresh = cv2.threshold(
            morphed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        # Use the one that gives better contrast
        adaptive_mean = np.mean(adaptive_thresh)
        otsu_mean = np.mean(otsu_thresh)
        
        if abs(adaptive_mean - 127) < abs(otsu_mean - 127):
            self.processed_image = adaptive_thresh
            threshold_type = "adaptive"
        else:
            self.processed_image = otsu_thresh
            threshold_type = "otsu"
        
        print(f"   [APPLIED] Applied {threshold_type} thresholding")
        print(f"   [SUCCESS] Image preprocessed successfully")
        
        return True
    
    def extract_text_regions(self):
        """Extract text using EasyOCR with OpenCV preprocessing."""
        print("[EXTRACT] Extracting text with EasyOCR...")
        
        if not EASYOCR_AVAILABLE or self.easyocr_reader is None:
            print("[ERROR] EasyOCR is not available for text extraction")
            print("   Please install EasyOCR: pip install easyocr")
            return False
        
        # Extract text using EasyOCR only
        extractions = self._extract_with_easyocr()
        
        if not extractions:
            print("[ERROR] No text could be extracted")
            return False
        
        # Remove duplicates and sort by position
        self.text_blocks = self._remove_duplicates(extractions)
        print(f"   [FOUND] Final total: {len(self.text_blocks)} unique text blocks")
        
        return len(self.text_blocks) > 0
    
    def _extract_with_easyocr(self):
        """Extract text using EasyOCR with multiple preprocessing approaches."""
        print("   [EXTRACT] Running EasyOCR extraction...")
        
        all_extractions = []
        
        try:
            # Method 1: Use the preprocessed image directly
            if len(self.processed_image.shape) == 2:  # Grayscale
                ocr_image = cv2.cvtColor(self.processed_image, cv2.COLOR_GRAY2RGB)
            else:
                ocr_image = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
            
            results = self.easyocr_reader.readtext(ocr_image)
            extractions = self._process_easyocr_results(results, "preprocessed")
            all_extractions.extend(extractions)
            
            # Method 2: Use original image for comparison
            if self.original_image is not None:
                orig_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                results_orig = self.easyocr_reader.readtext(orig_rgb)
                extractions_orig = self._process_easyocr_results(results_orig, "original")
                all_extractions.extend(extractions_orig)
            
            print(f"     [FOUND] EasyOCR found {len(all_extractions)} total text blocks")
            
        except Exception as e:
            print(f"     [WARNING] EasyOCR extraction failed: {e}")
        
        return all_extractions
    
    def _process_easyocr_results(self, results, method_name):
        """Process EasyOCR results into standardized format."""
        extractions = []
        
        for (bbox, text, confidence) in results:
            if text.strip() and confidence * 100 >= self.confidence_threshold:
                # Calculate bounding box from EasyOCR format
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x = int(min(x_coords))
                y = int(min(y_coords))
                w = int(max(x_coords) - min(x_coords))
                h = int(max(y_coords) - min(y_coords))
                
                block = {
                    'text': text.strip(),
                    'confidence': int(confidence * 100),
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'method': f'easyocr_{method_name}'
                }
                extractions.append(block)
        
        return extractions
    
    def _remove_duplicates(self, blocks):
        """Remove duplicate text blocks based on position and content."""
        if not blocks:
            return []
        
        unique_blocks = []
        
        for block in blocks:
            is_duplicate = False
            
            for existing in unique_blocks:
                # Check if blocks are in similar position (within 20 pixels)
                pos_similar = (
                    abs(block['x'] - existing['x']) < 20 and
                    abs(block['y'] - existing['y']) < 20
                )
                
                # Check if text is similar
                text_similar = (
                    block['text'].lower() == existing['text'].lower() or
                    block['text'].lower() in existing['text'].lower() or
                    existing['text'].lower() in block['text'].lower()
                )
                
                if pos_similar and text_similar:
                    # Keep the one with higher confidence
                    if block['confidence'] > existing['confidence']:
                        unique_blocks.remove(existing)
                        unique_blocks.append(block)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_blocks.append(block)
        
        return sorted(unique_blocks, key=lambda x: (x['y'], x['x']))
    
    def analyze_form_structure(self):
        """Analyze the extracted text to identify form structure."""
        print("[ANALYZE] Analyzing form structure...")
        
        labels = []
        values = []
        buttons = []
        
        for block in self.text_blocks:
            text = block['text'].lower()
            
            # Identify labels (often end with colon or have specific patterns)
            if (text.endswith(':') or text.endswith('*') or 
                any(word in text for word in ['name', 'number', 'date', 'address', 'phone', 'email', 'state', 'zip', 'policy', 'effective', 'coverage', 'premium', 'agent'])):
                labels.append(block)
            
            # Identify buttons and actions
            elif any(word in text for word in ['submit', 'save', 'cancel', 'continue', 'next', 'previous', 'quote', 'bind', 'calculate']):
                buttons.append(block)
            
            # Everything else could be values or regular text
            else:
                values.append(block)
        
        print(f"   [FOUND] Identified {len(labels)} potential labels")
        print(f"   [FOUND] Identified {len(values)} potential values") 
        print(f"   [FOUND] Identified {len(buttons)} potential buttons")
        
        return {
            'labels': labels,
            'values': values,
            'buttons': buttons,
            'all_text': self.text_blocks
        }
    
    def save_debug_images(self, output_dir="debug_images"):
        """Save intermediate processing images for debugging."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        if self.original_image is not None:
            cv2.imwrite(str(output_path / "1_original.png"), self.original_image)
        
        if self.processed_image is not None:
            cv2.imwrite(str(output_path / "2_processed.png"), self.processed_image)
        
        # Create annotated image with detected text regions
        if self.text_blocks and self.original_image is not None:
            annotated = self.original_image.copy()
            
            for i, block in enumerate(self.text_blocks):
                x, y, w, h = block['x'], block['y'], block['w'], block['h']
                
                # Draw rectangle around text
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Add confidence score
                cv2.putText(annotated, f"{block['confidence']}%", 
                           (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imwrite(str(output_path / "3_annotated.png"), annotated)
        
        print(f"[DEBUG] Debug images saved to: {output_path}")
    
    def generate_report(self, structure):
        """Generate a comprehensive text extraction report."""
        report = {
            'metadata': {
                'source_image': str(self.image_path),
                'image_size': self.original_image.shape[:2][::-1] if self.original_image is not None else None,
                'total_text_blocks': len(self.text_blocks),
                'confidence_threshold': self.confidence_threshold,
                'labels_found': len(structure['labels']),
                'values_found': len(structure['values']),
                'buttons_found': len(structure['buttons'])
            },
            'extracted_text': structure['all_text'],
            'form_structure': {
                'potential_labels': structure['labels'],
                'potential_values': structure['values'],
                'potential_buttons': structure['buttons']
            }
        }
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Extract text from form images using OpenCV')
    parser.add_argument('input_image', help='Path to input image')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--confidence', '-c', type=int, default=30, 
                       help='OCR confidence threshold (default: 30)')
    parser.add_argument('--debug', action='store_true', 
                       help='Save debug images showing intermediate processing')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    print("[OPENCV] OPENCV TEXT EXTRACTION")
    print("=" * 50)
    
    # Initialize extractor
    extractor = OpenCVTextExtractor(args.input_image, args.confidence)
    
    # Load image
    if not extractor.load_image():
        sys.exit(1)
    
    # Preprocess image
    if not extractor.preprocess_image():
        print("[ERROR] Image preprocessing failed")
        sys.exit(1)
    
    # Extract text
    if not extractor.extract_text_regions():
        print("[ERROR] No text could be extracted")
        sys.exit(1)
    
    # Analyze structure
    structure = extractor.analyze_form_structure()
    
    # Generate report
    report = extractor.generate_report(structure)
    
    # Save debug images if requested
    if args.debug:
        extractor.save_debug_images()
    
    # Print results
    print(f"\n[RESULTS] EXTRACTION RESULTS")
    print("=" * 30)
    print(f"Total text blocks found: {len(extractor.text_blocks)}")
    print(f"Potential labels: {len(structure['labels'])}")
    print(f"Potential values: {len(structure['values'])}")
    print(f"Potential buttons: {len(structure['buttons'])}")
    
    if args.verbose:
        print(f"\n[TEXT] ALL EXTRACTED TEXT:")
        print("-" * 40)
        for i, block in enumerate(extractor.text_blocks, 1):
            print(f"{i:2d}. \"{block['text']}\" (conf: {block['confidence']}%, method: {block['method']})")
        
        if structure['labels']:
            print(f"\n[LABELS] POTENTIAL LABELS:")
            print("-" * 20)
            for i, label in enumerate(structure['labels'], 1):
                print(f"{i:2d}. \"{label['text']}\" (conf: {label['confidence']}%)")
    
    # Save JSON output if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Results saved to: {output_path}")
    
    print(f"\n[SUCCESS] Text extraction completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())