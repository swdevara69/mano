#!/usr/bin/env python3
"""
OCR Image Field Extractor for Guidewire Policy Center Forms

This script provides comprehensive OCR processing and field extraction
specifically designed for insurance form analysis.

Dependencies:
    pip install opencv-python pillow pytesseract easyocr numpy

Usage:
    python ocr_field_extractor.py --input image.png --output fields.json
    python ocr_field_extractor.py --input image.png --verbose
"""

import cv2
import numpy as np
from PIL import Image
import json
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import re

# Try importing OCR libraries with fallbacks
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("Warning: easyocr not available")


class ImageFieldExtractor:
    """Advanced OCR-based field extraction for insurance forms."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.extracted_fields = []
        self.confidence_threshold = 30
        
        # Initialize EasyOCR reader if available
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en'])
            except Exception as e:
                if verbose:
                    print(f"EasyOCR initialization failed: {e}")
        
        # Guidewire field patterns
        self.insurance_field_patterns = {
            'policy_number': [
                r'policy\s*number', r'policy\s*no\.?', r'policy\s*#',
                r'pol\s*no\.?', r'policy\s*id'
            ],
            'effective_date': [
                r'effective\s*date', r'start\s*date', r'policy\s*effective',
                r'coverage\s*starts?', r'begins?'
            ],
            'expiration_date': [
                r'expiration\s*date', r'expires?', r'end\s*date',
                r'policy\s*expires?', r'coverage\s*ends?'
            ],
            'named_insured': [
                r'named\s*insured', r'insured\s*name', r'policyholder',
                r'customer\s*name', r'applicant\s*name'
            ],
            'coverage_amount': [
                r'coverage\s*amount', r'limit', r'coverage\s*limit',
                r'policy\s*limit', r'insured\s*amount'
            ],
            'deductible': [
                r'deductible', r'deduct\.?', r'ded\.?'
            ],
            'premium': [
                r'premium', r'cost', r'price', r'annual\s*premium',
                r'total\s*premium'
            ],
            'agent_code': [
                r'agent\s*code', r'agent\s*id', r'agent\s*number',
                r'producer\s*code'
            ],
            'agent_name': [
                r'agent\s*name', r'agent', r'producer\s*name',
                r'broker\s*name'
            ],
            'risk_state': [
                r'state', r'risk\s*state', r'location\s*state',
                r'coverage\s*state'
            ],
            'payment_plan': [
                r'payment\s*plan', r'payment\s*method', r'billing',
                r'premium\s*payment'
            ],
            'line_of_business': [
                r'line\s*of\s*business', r'lob', r'coverage\s*type',
                r'product\s*line', r'insurance\s*type'
            ],
            'prior_carrier': [
                r'prior\s*carrier', r'previous\s*insurer', r'current\s*carrier',
                r'existing\s*coverage'
            ]
        }
    
    def log(self, message):
        """Print verbose logging messages."""
        if self.verbose:
            print(f"[OCR] {message}")
    
    def load_and_preprocess_image(self, image_path):
        """Load image and apply preprocessing for optimal OCR."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        self.log(f"Loading image: {image_path}")
        
        # Load with PIL first for format compatibility
        pil_image = Image.open(image_path)
        self.log(f"Image loaded: {pil_image.size} pixels, {pil_image.mode} mode")
        
        # Convert to OpenCV format
        if pil_image.mode == 'RGBA':
            # Handle transparency by creating white background
            background = Image.new('RGB', pil_image.size, (255, 255, 255))
            background.paste(pil_image, mask=pil_image.split()[-1])
            pil_image = background
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to OpenCV
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Preprocessing pipeline
        self.log("Applying image preprocessing...")
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Optional: Morphological operations to clean up text
        kernel = np.ones((1,1), np.uint8)
        processed = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
        
        self.log("Image preprocessing completed")
        return processed, opencv_image
    
    def extract_text_pytesseract(self, image):
        """Extract text using Tesseract OCR."""
        if not PYTESSERACT_AVAILABLE:
            return []
        
        self.log("Running Tesseract OCR...")
        
        try:
            # Configuration for better form recognition
            config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:()*\-/\$%&+= '
            
            # Extract data with bounding boxes
            data = pytesseract.image_to_data(
                image, 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            text_blocks = []
            for i, text in enumerate(data['text']):
                if text.strip() and data['conf'][i] > self.confidence_threshold:
                    text_blocks.append({
                        'text': text.strip(),
                        'confidence': data['conf'][i],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        },
                        'engine': 'tesseract'
                    })
            
            self.log(f"Tesseract extracted {len(text_blocks)} text blocks")
            return text_blocks
            
        except Exception as e:
            self.log(f"Tesseract OCR failed: {e}")
            return []
    
    def extract_text_easyocr(self, image):
        """Extract text using EasyOCR."""
        if not EASYOCR_AVAILABLE or not self.easyocr_reader:
            return []
        
        self.log("Running EasyOCR...")
        
        try:
            # EasyOCR expects image as numpy array
            results = self.easyocr_reader.readtext(image)
            
            text_blocks = []
            for bbox, text, confidence in results:
                if confidence > (self.confidence_threshold / 100.0):  # EasyOCR uses 0-1 scale
                    # Convert bbox to standard format
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    text_blocks.append({
                        'text': text.strip(),
                        'confidence': int(confidence * 100),
                        'bbox': {
                            'x': int(min(x_coords)),
                            'y': int(min(y_coords)),
                            'width': int(max(x_coords) - min(x_coords)),
                            'height': int(max(y_coords) - min(y_coords))
                        },
                        'engine': 'easyocr'
                    })
            
            self.log(f"EasyOCR extracted {len(text_blocks)} text blocks")
            return text_blocks
            
        except Exception as e:
            self.log(f"EasyOCR failed: {e}")
            return []
    
    def combine_ocr_results(self, tesseract_results, easyocr_results):
        """Combine and deduplicate OCR results from multiple engines."""
        combined = tesseract_results + easyocr_results
        
        if not combined:
            return []
        
        # Sort by y-coordinate, then x-coordinate for logical reading order
        combined.sort(key=lambda x: (x['bbox']['y'], x['bbox']['x']))
        
        self.log(f"Combined OCR results: {len(combined)} total text blocks")
        return combined
    
    def identify_field_labels(self, text_blocks):
        """Identify potential field labels from extracted text."""
        labels = []
        values = []
        
        for block in text_blocks:
            text = block['text'].lower().strip()
            
            # Check if this looks like a field label
            is_label = (
                text.endswith(':') or 
                text.endswith('*') or
                any(pattern in text for patterns in self.insurance_field_patterns.values() for pattern in patterns)
            )
            
            if is_label:
                labels.append(block)
            else:
                values.append(block)
        
        self.log(f"Identified {len(labels)} potential labels, {len(values)} values")
        return labels, values
    
    def match_fields_to_patterns(self, labels):
        """Match detected labels to known insurance field patterns."""
        matched_fields = []
        
        for label in labels:
            label_text = label['text'].lower().strip()
            label_text = re.sub(r'[:\*\s]+$', '', label_text)  # Remove trailing punctuation
            
            best_match = None
            best_score = 0
            
            for field_id, patterns in self.insurance_field_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, label_text):
                        score = len(re.search(pattern, label_text).group(0))
                        if score > best_score:
                            best_match = field_id
                            best_score = score
            
            if best_match:
                field_info = self.get_field_metadata(best_match)
                matched_fields.append({
                    'field_id': best_match,
                    'detected_label': label['text'],
                    'clean_label': label_text,
                    'confidence': label['confidence'],
                    'bbox': label['bbox'],
                    'metadata': field_info
                })
                self.log(f"Matched '{label_text}' -> {best_match}")
        
        return matched_fields
    
    def get_field_metadata(self, field_id):
        """Get metadata for identified field types."""
        metadata = {
            'policy_number': {
                'type': 'text',
                'required': True,
                'validation': 'alphanumeric',
                'format': 'PC12345678901',
                'section': 'Policy Information'
            },
            'effective_date': {
                'type': 'date',
                'required': True,
                'validation': 'future_date',
                'format': 'MM/DD/YYYY',
                'section': 'Policy Information'
            },
            'expiration_date': {
                'type': 'date',
                'required': True,
                'validation': 'after_effective',
                'format': 'MM/DD/YYYY',
                'section': 'Policy Information'
            },
            'named_insured': {
                'type': 'text',
                'required': True,
                'validation': 'name_format',
                'format': 'Full legal name',
                'section': 'Insured Information'
            },
            'coverage_amount': {
                'type': 'currency',
                'required': True,
                'validation': 'amount_range',
                'format': '$100,000 - $50,000,000',
                'section': 'Coverage Details'
            },
            'deductible': {
                'type': 'select',
                'required': True,
                'validation': 'predefined_values',
                'format': '$250, $500, $1000, $2500, $5000, $10000',
                'section': 'Coverage Details'
            },
            'premium': {
                'type': 'currency',
                'required': False,
                'validation': 'calculated',
                'format': 'Auto-calculated',
                'section': 'Coverage Details'
            },
            'agent_code': {
                'type': 'text',
                'required': True,
                'validation': 'agent_lookup',
                'format': 'XX#########',
                'section': 'Agent Information'
            },
            'agent_name': {
                'type': 'text',
                'required': True,
                'validation': 'name_format',
                'format': 'Full agent name',
                'section': 'Agent Information'
            },
            'risk_state': {
                'type': 'select',
                'required': True,
                'validation': 'us_state',
                'format': 'CA, TX, NY, etc.',
                'section': 'Risk Information'
            },
            'payment_plan': {
                'type': 'select',
                'required': True,
                'validation': 'plan_options',
                'format': 'Full Pay, Monthly, etc.',
                'section': 'Payment Information'
            },
            'line_of_business': {
                'type': 'select',
                'required': True,
                'validation': 'lob_options',
                'format': 'Auto, Property, GL, etc.',
                'section': 'Coverage Details'
            },
            'prior_carrier': {
                'type': 'text',
                'required': False,
                'validation': 'carrier_name',
                'format': 'Insurance company name',
                'section': 'Prior Insurance'
            }
        }
        
        return metadata.get(field_id, {
            'type': 'text',
            'required': False,
            'validation': 'none',
            'format': 'Unknown format',
            'section': 'Unknown'
        })
    
    def process_image(self, image_path, output_path=None):
        """Main processing workflow for image field extraction."""
        try:
            # Load and preprocess
            processed_image, original_image = self.load_and_preprocess_image(image_path)
            
            # Extract text with multiple OCR engines
            tesseract_results = self.extract_text_pytesseract(processed_image)
            easyocr_results = self.extract_text_easyocr(processed_image)
            
            # Combine results
            all_text_blocks = self.combine_ocr_results(tesseract_results, easyocr_results)
            
            if not all_text_blocks:
                self.log("No text extracted from image")
                return self.create_empty_result(image_path)
            
            # Identify labels and values
            labels, values = self.identify_field_labels(all_text_blocks)
            
            # Match to insurance field patterns
            matched_fields = self.match_fields_to_patterns(labels)
            
            # Create comprehensive result
            result = {
                'metadata': {
                    'source_image': str(image_path),
                    'extraction_date': datetime.now().isoformat(),
                    'ocr_engines_used': [],
                    'total_text_blocks': len(all_text_blocks),
                    'identified_fields': len(matched_fields)
                },
                'extracted_text': all_text_blocks,
                'identified_fields': matched_fields,
                'field_summary': self.create_field_summary(matched_fields)
            }
            
            # Track which engines were used
            if tesseract_results:
                result['metadata']['ocr_engines_used'].append('tesseract')
            if easyocr_results:
                result['metadata']['ocr_engines_used'].append('easyocr')
            
            # Save result if output path provided
            if output_path:
                self.save_result(result, output_path)
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            self.log(error_msg)
            return self.create_error_result(image_path, error_msg)
    
    def create_field_summary(self, matched_fields):
        """Create a summary of identified fields by section."""
        summary = {}
        
        for field in matched_fields:
            section = field['metadata'].get('section', 'Unknown')
            if section not in summary:
                summary[section] = []
            
            summary[section].append({
                'field_id': field['field_id'],
                'label': field['detected_label'],
                'type': field['metadata'].get('type', 'unknown'),
                'required': field['metadata'].get('required', False),
                'confidence': field['confidence']
            })
        
        return summary
    
    def create_empty_result(self, image_path):
        """Create result structure when no text is extracted."""
        return {
            'metadata': {
                'source_image': str(image_path),
                'extraction_date': datetime.now().isoformat(),
                'ocr_engines_used': [],
                'total_text_blocks': 0,
                'identified_fields': 0,
                'status': 'no_text_extracted'
            },
            'extracted_text': [],
            'identified_fields': [],
            'field_summary': {}
        }
    
    def create_error_result(self, image_path, error_message):
        """Create result structure for error cases."""
        return {
            'metadata': {
                'source_image': str(image_path),
                'extraction_date': datetime.now().isoformat(),
                'ocr_engines_used': [],
                'total_text_blocks': 0,
                'identified_fields': 0,
                'status': 'error',
                'error_message': error_message
            },
            'extracted_text': [],
            'identified_fields': [],
            'field_summary': {}
        }
    
    def save_result(self, result, output_path):
        """Save extraction result to JSON file."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.log(f"Results saved to: {output_path}")
            
        except Exception as e:
            self.log(f"Error saving results: {e}")


def main():
    """Command-line interface for the OCR field extractor."""
    parser = argparse.ArgumentParser(
        description='Extract form fields from images using OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python ocr_field_extractor.py --input form.png
    python ocr_field_extractor.py --input form.png --output fields.json --verbose
    python ocr_field_extractor.py --input form.png --confidence 50
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='Path to input image file')
    parser.add_argument('--output', '-o',
                       help='Path for output JSON file (optional)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--confidence', '-c', type=int, default=30,
                       help='Minimum OCR confidence threshold (default: 30)')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = ImageFieldExtractor(verbose=args.verbose)
    extractor.confidence_threshold = args.confidence
    
    # Process image
    result = extractor.process_image(args.input, args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"OCR FIELD EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Source Image: {result['metadata']['source_image']}")
    print(f"OCR Engines: {', '.join(result['metadata']['ocr_engines_used']) or 'None available'}")
    print(f"Total Text Blocks: {result['metadata']['total_text_blocks']}")
    print(f"Identified Fields: {result['metadata']['identified_fields']}")
    
    if result['field_summary']:
        print(f"\nFieldes by Section:")
        for section, fields in result['field_summary'].items():
            print(f"\n  [CAT] {section}:")
            for field in fields:
                req = "*" if field['required'] else " "
                print(f"    {req} {field['label']} [{field['type'].upper()}] (conf: {field['confidence']}%)")
    
    # Return appropriate exit code
    if result['metadata'].get('status') == 'error':
        sys.exit(1)
    elif result['metadata']['identified_fields'] == 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()