#!/usr/bin/env python3
"""
Simple OpenCV Form Analyzer

A user-friendly wrapper for the OpenCV text extractor optimized for Guidewire forms.
"""

import sys
import json
from pathlib import Path
import argparse

# Import our OpenCV extractor
sys.path.append(str(Path(__file__).parent))
from opencv_text_extractor import OpenCVTextExtractor


class SimpleFormAnalyzer:
    """Simple interface for analyzing forms with OpenCV."""
    
    def __init__(self):
        self.guidewire_field_patterns = [
            'policy number', 'policy effective', 'policy expiration',
            'named insured', 'insured name', 'first name', 'last name',
            'mailing address', 'address', 'city', 'state', 'zip', 'postal',
            'phone', 'telephone', 'email', 'contact',
            'line of business', 'coverage', 'limit', 'deductible',
            'agent', 'producer', 'broker', 'agency',
            'effective date', 'expiration date', 'term',
            'premium', 'payment', 'billing',
            'prior carrier', 'prior insurance', 'lapse',
            'credit score', 'tier', 'rating'
        ]
    
    def analyze_image(self, image_path, confidence=30, verbose=False):
        """Analyze an image and extract form fields."""
        
        print(f"[IMG] ANALYZING IMAGE: {Path(image_path).name}")
        print("=" * 60)
        
        # Initialize extractor
        extractor = OpenCVTextExtractor(image_path, confidence)
        
        # Process image
        if not extractor.load_image():
            return None
        
        if not extractor.preprocess_image():
            return None
        
        if not extractor.extract_text_regions():
            print("[WARNING] Could not extract text with current settings")
            return None
        
        # Analyze structure
        structure = extractor.analyze_form_structure()
        
        # Identify potential Guidewire fields
        guidewire_fields = self.identify_guidewire_fields(structure)
        
        # Generate comprehensive report
        return self.generate_analysis_report(extractor, structure, guidewire_fields)
    
    def identify_guidewire_fields(self, structure):
        """Identify potential Guidewire PolicyCenter fields."""
        identified_fields = []
        
        # Check labels for known patterns
        for label in structure['labels']:
            label_text = label['text'].lower().strip(':*')
            
            for pattern in self.guidewire_field_patterns:
                if pattern in label_text or any(word in label_text for word in pattern.split()):
                    field_info = {
                        'detected_text': label['text'],
                        'field_type': pattern,
                        'confidence': label['confidence'],
                        'position': {'x': label['x'], 'y': label['y']},
                        'category': self.categorize_field(pattern)
                    }
                    identified_fields.append(field_info)
                    break
        
        return identified_fields
    
    def categorize_field(self, field_pattern):
        """Categorize fields into logical groups."""
        categories = {
            'Policy Information': ['policy number', 'policy effective', 'policy expiration', 'effective date', 'expiration date', 'term'],
            'Insured Information': ['named insured', 'insured name', 'first name', 'last name', 'mailing address', 'address', 'city', 'state', 'zip', 'postal', 'phone', 'telephone', 'email', 'contact'],
            'Coverage Details': ['line of business', 'coverage', 'limit', 'deductible'],
            'Agent Information': ['agent', 'producer', 'broker', 'agency'],
            'Financial Information': ['premium', 'payment', 'billing'],
            'Prior Insurance': ['prior carrier', 'prior insurance', 'lapse'],
            'Underwriting': ['credit score', 'tier', 'rating']
        }
        
        for category, patterns in categories.items():
            if field_pattern in patterns:
                return category
        
        return 'Other'
    
    def generate_analysis_report(self, extractor, structure, guidewire_fields):
        """Generate a comprehensive analysis report."""
        
        # Group identified fields by category
        field_categories = {}
        for field in guidewire_fields:
            category = field['category']
            if category not in field_categories:
                field_categories[category] = []
            field_categories[category].append(field)
        
        # Print summary
        print(f"[STATS] EXTRACTION SUMMARY:")
        print(f"   Total text blocks: {len(structure['all_text'])}")
        print(f"   Potential labels: {len(structure['labels'])}")
        print(f"   Guidewire fields identified: {len(guidewire_fields)}")
        print(f"   Field categories: {len(field_categories)}")
        print(f"   OCR Engine: EasyOCR (OpenCV preprocessed)")
        
        # Print identified fields by category
        if guidewire_fields:
            print(f"\n[FIELDS] IDENTIFIED GUIDEWIRE FIELDS:")
            print("=" * 40)
            
            for category, fields in field_categories.items():
                print(f"\n[CAT] {category}:")
                print("-" * len(category))
                
                for i, field in enumerate(fields, 1):
                    print(f"   {i}. {field['detected_text']} -> {field['field_type']}")
                    print(f"      Confidence: {field['confidence']}%")
        
        # Print all extracted text if requested
        print(f"\n[TEXT] ALL EXTRACTED TEXT:")
        print("=" * 30)
        
        for i, block in enumerate(structure['all_text'], 1):
            # Mark identified fields with [*]
            is_identified = any(f['detected_text'] == block['text'] for f in guidewire_fields)
            marker = "[*]" if is_identified else "   "
            print(f"{i:2d}.{marker} \"{block['text']}\" (conf: {block['confidence']}%)")
        
        return {
            'summary': {
                'total_text_blocks': len(structure['all_text']),
                'potential_labels': len(structure['labels']),
                'identified_fields': len(guidewire_fields),
                'field_categories': len(field_categories)
            },
            'guidewire_fields': guidewire_fields,
            'field_categories': field_categories,
            'all_text': structure['all_text'],
            'structure': structure
        }


def main():
    parser = argparse.ArgumentParser(description='Simple OpenCV Form Analyzer for Guidewire forms')
    parser.add_argument('image_path', help='Path to the image file')
    parser.add_argument('--confidence', '-c', type=int, default=30,
                       help='OCR confidence threshold (default: 30)')
    parser.add_argument('--output', '-o', help='Save results to JSON file')
    parser.add_argument('--debug', action='store_true',
                       help='Save debug images showing processing steps')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    
    args = parser.parse_args()
    
    # Check if image exists
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"[ERROR] Image file not found: {image_path}")
        return 1
    
    # Analyze the image
    analyzer = SimpleFormAnalyzer()
    results = analyzer.analyze_image(
        str(image_path), 
        confidence=args.confidence,
        verbose=args.verbose
    )
    
    if results is None:
        print("[ERROR] Analysis failed")
        return 1
    
    # Save debug images if requested
    if args.debug:
        extractor = OpenCVTextExtractor(str(image_path), args.confidence)
        extractor.load_image()
        extractor.preprocess_image()
        extractor.extract_text_regions()
        extractor.save_debug_images()
    
    # Save JSON output if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Results saved to: {output_path}")
    
    print(f"\n[SUCCESS] Analysis completed successfully!")
    
    # Provide recommendations
    print(f"\n[TIPS] RECOMMENDATIONS:")
    if results['summary']['identified_fields'] == 0:
        print("   - No Guidewire fields identified automatically")
        print("   - Try lowering confidence threshold: --confidence 20")
        print("   - Use --debug to see processing steps")
        print("   - Image may need manual preprocessing")
    elif results['summary']['identified_fields'] < 5:
        print("   - Few fields identified, consider:")
        print("   - Lowering confidence threshold")
        print("   - Improving image quality/resolution") 
        print("   - Checking if image contains standard Guidewire form")
    else:
        print("   - Good field identification achieved!")
        print("   - Consider using --output to save results")
        print("   - Results can be used for test data generation")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())