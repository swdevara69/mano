#!/usr/bin/env python3
"""
Quick Image Analysis Wrapper for Guidewire Policy Center Forms

This script provides a simple interface to analyze Guidewire Policy Center
form images and extract field information.

Dependencies: Run setup_ocr_environment.py first

Usage:
    python analyze_guidewire_form.py path/to/image.png
    python analyze_guidewire_form.py image.png --verbose --output results.json
"""

import sys
import json
import argparse
from pathlib import Path
import os

# Add the scripts directory to Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from ocr_field_extractor import ImageFieldExtractor
except ImportError as e:
    print(f"[ERROR] Error importing OCR extractor: {e}")
    print(f"[TIP] Make sure to run 'python setup_ocr_environment.py' first")
    sys.exit(1)


def print_field_analysis(result):
    """Print a formatted analysis of extracted fields."""
    metadata = result.get('metadata', {})
    field_summary = result.get('field_summary', {})
    identified_fields = result.get('identified_fields', [])
    
    print(f"\n[HEADER] GUIDEWIRE POLICY CENTER - IMAGE ANALYSIS")
    print(f"{'='*65}")
    
    # Basic info
    print(f"[SOURCE] Source Image: {os.path.basename(metadata.get('source_image', 'Unknown'))}")
    print(f"[STATS] Image Resolution: {metadata.get('image_size', 'Unknown')}")
    print(f"[ENGINES] OCR Engines: {', '.join(metadata.get('ocr_engines_used', ['None']))}")
    print(f"[BLOCKS] Total Text Blocks: {metadata.get('total_text_blocks', 0)}")
    print(f"[FIELDS] Identified Fields: {metadata.get('identified_fields', 0)}")
    
    if metadata.get('status') == 'error':
        print(f"[ERROR] Error: {metadata.get('error_message', 'Unknown error')}")
        return
    
    if not field_summary:
        print(f"\n[WARNING] No form fields were automatically identified")
        print(f"   This could mean:")
        print(f"   - Image quality is too poor for OCR")
        print(f"   - Text is handwritten or in unusual fonts")
        print(f"   - Image doesn't contain a standard form")
        print(f"   - OCR dependencies are not properly installed")
        return
    
    # Field breakdown by section
    print(f"\n[FIELDS] IDENTIFIED FORM FIELDS:")
    print(f"{'='*65}")
    
    field_count = 0
    total_required = 0
    
    for section_name, fields in field_summary.items():
        print(f"\n[CAT] {section_name}:")
        print(f"{'-' * (len(section_name) + 3)}")
        
        for field in fields:
            field_count += 1
            req_indicator = "[*] Required" if field.get('required') else "    Optional"
            confidence = field.get('confidence', 0)
            
            print(f"  {field_count:2d}. {field.get('label', 'Unknown')} [{field.get('type', 'text').upper()}]")
            print(f"      {req_indicator} | Confidence: {confidence}%")
            
            if field.get('required'):
                total_required += 1
    
    # Summary statistics
    print(f"\n[SUMMARY] FORM ANALYSIS SUMMARY:")
    print(f"{'='*30}")
    print(f"Total Fields Found:     {field_count}")
    print(f"Required Fields:        {total_required}")
    print(f"Optional Fields:        {field_count - total_required}")
    print(f"Form Sections:          {len(field_summary)}")
    
    # Field type distribution
    if identified_fields:
        type_counts = {}
        for field in identified_fields:
            field_type = field.get('metadata', {}).get('type', 'unknown')
            type_counts[field_type] = type_counts.get(field_type, 0) + 1
        
        print(f"\n[TYPES] FIELD TYPES:")
        for field_type, count in sorted(type_counts.items()):
            print(f"   {field_type.capitalize()}: {count}")
    
    # Quality assessment
    print(f"\n[QUALITY] EXTRACTION QUALITY:")
    if identified_fields:
        confidences = [f.get('confidence', 0) for f in identified_fields]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        
        print(f"   Average Confidence: {avg_confidence:.1f}%")
        print(f"   Lowest Confidence:  {min_confidence}%")
        
        if avg_confidence >= 80:
            print(f"   [EXCELLENT] Excellent extraction quality")
        elif avg_confidence >= 60:
            print(f"   [GOOD] Good extraction quality")
        elif avg_confidence >= 40:
            print(f"   [WARNING] Fair extraction quality - consider better image")
        else:
            print(f"   [ERROR] Poor extraction quality - improve image quality")
    
    # Recommendations
    print(f"\n[TIPS] RECOMMENDATIONS:")
    if metadata.get('total_text_blocks', 0) == 0:
        print(f"   - Check image quality and format")
        print(f"   - Ensure image contains clear, printed text")
        print(f"   - Verify OCR dependencies are installed")
    elif metadata.get('identified_fields', 0) < 5:
        print(f"   - Image may not be a standard Guidewire Policy Center form")
        print(f"   - Consider manual field identification for custom forms")
    else:
        print(f"   - Form analysis completed successfully")
        print(f"   - Use results for test data generation or documentation")


def main():
    """Main analysis workflow."""
    parser = argparse.ArgumentParser(
        description='Analyze Guidewire Policy Center form images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python analyze_guidewire_form.py form.png
    python analyze_guidewire_form.py form.png --verbose
    python analyze_guidewire_form.py form.png --output analysis.json
    python analyze_guidewire_form.py form.png --confidence 60 --verbose
        """
    )
    
    parser.add_argument('image_path', help='Path to the form image file')
    parser.add_argument('--output', '-o', help='Save detailed results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed processing logs')
    parser.add_argument('--confidence', '-c', type=int, default=40, help='Minimum OCR confidence (default: 40)')
    parser.add_argument('--quiet', '-q', action='store_true', help='Only show essential output')
    
    args = parser.parse_args()
    
    # Verify image exists
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"[ERROR] Image file not found: {args.image_path}")
        return 1
    
    try:
        # Initialize extractor
        extractor = ImageFieldExtractor(verbose=args.verbose)
        extractor.confidence_threshold = args.confidence
        
        if not args.quiet:
            print(f"[START] Starting analysis of {image_path.name}...")
            print(f"[CONFIG] OCR confidence threshold: {args.confidence}%")
        
        # Process the image
        result = extractor.process_image(image_path, args.output)
        
        if not args.quiet:
            # Print detailed analysis
            print_field_analysis(result)
        else:
            # Just print basic stats
            metadata = result.get('metadata', {})
            print(f"Fields: {metadata.get('identified_fields', 0)}, "
                  f"Text blocks: {metadata.get('total_text_blocks', 0)}, "
                  f"Status: {metadata.get('status', 'success')}")
        
        # Save to JSON if requested
        if args.output:
            print(f"\n[SAVE] Detailed results saved to: {args.output}")
        
        # Return appropriate exit code
        field_count = result.get('metadata', {}).get('identified_fields', 0)
        if field_count > 0:
            return 0  # Success
        elif result.get('metadata', {}).get('status') == 'error':
            return 2  # Error
        else:
            return 1  # No fields found
            
    except KeyboardInterrupt:
        print(f"\n[STOPPED] Analysis interrupted by user")
        return 130
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 3


if __name__ == '__main__':
    sys.exit(main())