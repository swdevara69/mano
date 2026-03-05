"""
Word Document Image Extractor and Processor
Optimus Core Framework - Word Document Processing

This script extracts images from Microsoft Word (.docx) documents and processes
them through the OCR analysis pipeline for form field extraction.
"""

import zipfile
import os
import sys
import argparse
from pathlib import Path
import json

def detect_input_type(file_path):
    """Detect if input is image file or Word document"""
    path = Path(file_path)
    
    # Image file extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif'}
    
    # Word document extensions
    doc_extensions = {'.docx'}
    
    if path.suffix.lower() in image_extensions:
        return 'image'
    elif path.suffix.lower() in doc_extensions:
        return 'word_document'
    else:
        return 'unknown'

def extract_images_from_word(docx_path, output_dir='temp_word_images'):
    """Extract all images from a Word document"""
    extracted_images = []
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Word documents are ZIP files internally
        with zipfile.ZipFile(docx_path, 'r') as docx_zip:
            # Look for image files in the media folder
            media_files = [f for f in docx_zip.infolist() 
                         if f.filename.startswith('word/media/') and 
                         f.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'))]
            
            print(f"[DOC] Found {len(media_files)} images in Word document")
            
            for i, file_info in enumerate(media_files, 1):
                # Extract image to temp directory
                image_data = docx_zip.read(file_info.filename)
                
                # Create temp filename with index to maintain order
                original_name = Path(file_info.filename).name
                image_filename = f"{output_dir}/image_{i:02d}_{original_name}"
                
                with open(image_filename, 'wb') as img_file:
                    img_file.write(image_data)
                
                extracted_images.append({
                    'path': image_filename,
                    'original_name': file_info.filename,
                    'size': file_info.file_size,
                    'index': i
                })
                
                print(f"  [OK] Extracted image {i}/{len(media_files)}: {original_name}")
        
        return extracted_images
    
    except Exception as e:
        return {'error': f'Failed to extract images from Word document: {str(e)}'}

def process_word_document(docx_path, output_file=None, verbose=False, confidence=25, max_images=5):
    """Complete workflow for processing Word documents with multiple images"""
    
    print(f"[PROC] Processing Word document: {Path(docx_path).name}")
    
    # Step 1: Extract images
    extracted_images = extract_images_from_word(docx_path)
    
    if isinstance(extracted_images, dict) and 'error' in extracted_images:
        return extracted_images
    
    if not extracted_images:
        return {'error': 'No images found in the Word document'}
    
    # Import the existing OCR analysis function
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Try to import from the existing simple_form_analyzer
        import subprocess
        import json
        
        # Step 2: Process each image with OCR
        all_analysis_results = []
        consolidated_fields = []
        consolidated_categories = {}
        all_extracted_text = []
        
        # Limit images for efficiency (process first max_images only)
        images_to_process = extracted_images[:max_images] if len(extracted_images) > max_images else extracted_images
        
        if len(extracted_images) > max_images:
            print(f"\n💡 Found {len(extracted_images)} images. Processing first {max_images} for speed.")
            print(f"   Use --max-images {len(extracted_images)} to process all images.")
        
        for image_info in images_to_process:
            print(f"\n[IMG] Processing image {image_info['index']}/{len(images_to_process)}: {image_info['original_name']}")
            
            # Run the simple_form_analyzer script on each extracted image
            cmd = [
                'python', 'scripts/simple_form_analyzer.py', 
                image_info['path'], 
                '--confidence', str(confidence)
            ]
            
            if verbose:
                cmd.append('--verbose')
            
            # Create temp output file for this image
            temp_output = f"temp_analysis_{image_info['index']}.json"
            cmd.extend(['--output', temp_output])
            
            try:
                # Suppress warnings
                env = os.environ.copy()
                env['PYTHONWARNINGS'] = 'ignore::UserWarning'
                
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      env=env)  # No timeout - let it complete
                
                if result.returncode == 0:
                    # Load analysis results
                    if os.path.exists(temp_output):
                        with open(temp_output, 'r') as f:
                            analysis_data = json.load(f)
                        
                        # Add image metadata
                        analysis_data['image_info'] = image_info
                        analysis_data['image_number'] = image_info['index']
                        all_analysis_results.append(analysis_data)
                        
                        # Clean up temp file
                        os.remove(temp_output)
                        
                        print(f"  [OK] OCR analysis completed for image {image_info['index']}")
                    else:
                        print(f"  [WARN] No analysis results generated for image {image_info['index']}")
                else:
                    print(f"  [ERROR] OCR analysis failed for image {image_info['index']}: {result.stderr}")
            
            except subprocess.TimeoutExpired:
                print(f"  [TIMEOUT] OCR analysis unexpectedly timed out for image {image_info['index']} - skipping")
                continue  # Skip to next image quickly
            except Exception as e:
                print(f"  [ERROR] Error processing image {image_info['index']}: {str(e)[:50]}... - skipping")
                continue  # Skip to next image quickly
        
        # Step 3: Consolidate results from all images
        total_fields = 0
        
        for result in all_analysis_results:
            # Consolidate fields
            fields = result.get('guidewire_fields', [])
            for field in fields:
                field['source_image'] = result['image_number']
                field['source_name'] = result['image_info']['original_name']
            consolidated_fields.extend(fields)
            total_fields += len(fields)
            
            # Consolidate categories
            categories = result.get('field_categories', {})
            for category, field_list in categories.items():
                if category in consolidated_categories:
                    consolidated_categories[category].extend(field_list)
                else:
                    consolidated_categories[category] = field_list
            
            # Consolidate text
            text = result.get('all_text', [])
            all_extracted_text.append({
                'image': result['image_number'],
                'text': text
            })
        
        # Step 4: Create consolidated summary
        consolidated_summary = {
            'source_document': docx_path,
            'total_images_found': len(extracted_images),
            'total_images_processed': len(all_analysis_results),
            'total_fields_found': total_fields,
            'field_categories_count': len(consolidated_categories),
            'processing_notes': f"Processed {len(images_to_process)} of {len(extracted_images)} images",
            'individual_results': all_analysis_results
        }
        
        final_result = {
            'summary': consolidated_summary,
            'guidewire_fields': consolidated_fields,
            'field_categories': consolidated_categories,
            'all_text': all_extracted_text,
            'metadata': {
                'source_type': 'word_document',
                'source_file': docx_path,
                'images_processed': len(all_analysis_results),
                'processing_engine': 'word_document_processor'
            }
        }
        
        # Save consolidated results if output file specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
            print(f"\n[SAVE] Consolidated results saved to: {output_file}")
        
        # Clean up extracted images
        for image_info in extracted_images:
            try:
                os.remove(image_info['path'])
            except:
                pass
        
        # Remove temp directory if empty
        try:
            os.rmdir('temp_word_images')
        except:
            pass
        
        print(f"\n[SUCCESS] Word document processing completed!")
        print(f"   [STATS] Processed {len(all_analysis_results)} images")
        print(f"   [RESULTS] Found {total_fields} total fields")
        print(f"   [CATS] Identified {len(consolidated_categories)} field categories")
        
        return final_result
    
    except ImportError as e:
        return {'error': f'Required OCR modules not available: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error during Word document processing: {str(e)}'}

def main():
    parser = argparse.ArgumentParser(description='Process Word documents with embedded images for form analysis')
    parser.add_argument('input_file', help='Path to Word document (.docx)')
    parser.add_argument('--output', '-o', help='Save results to JSON file')
    parser.add_argument('--confidence', '-c', type=int, default=25, help='OCR confidence threshold (default: 25)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--max-images', '-m', type=int, default=5, help='Maximum number of images to process for speed (default: 5)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"[ERROR] Error: File not found: {args.input_file}")
        return 1
    
    # Check file type
    input_type = detect_input_type(args.input_file)
    if input_type != 'word_document':
        print(f"[ERROR] Error: File must be a Word document (.docx). Detected type: {input_type}")
        return 1
    
    # Process the document
    max_images = getattr(args, 'max_images', 5)  # Handle both old and new argument names
    result = process_word_document(args.input_file, args.output, args.verbose, args.confidence, max_images)
    
    if isinstance(result, dict) and 'error' in result:
        print(f"[ERROR] Error: {result['error']}")
        return 1
    
    # Display summary
    summary = result.get('summary', {})
    print(f"\n[SUMMARY] PROCESSING SUMMARY:")
    print(f"   Document: {Path(summary.get('source_document', '')).name}")
    print(f"   Images processed: {summary.get('total_images_processed', 0)}")
    print(f"   Total fields found: {summary.get('total_fields_found', 0)}")
    print(f"   Categories identified: {summary.get('field_categories_count', 0)}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())