"""
Word Document Batch Image Processor
Optimus Core Framework - Word Document Processing with Batch Support

This script extracts images from Microsoft Word (.docx) documents and processes
them in configurable batches through the OCR analysis pipeline.
Features: batch processing, detailed logging, resumable processing, timeout handling.
"""

import zipfile
import os
import sys
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
def setup_logging(log_dir='ocr_logs'):
    """Setup detailed logging for batch processing"""
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"{log_dir}/batch_processing_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return log_file

def detect_input_type(file_path):
    """Detect if input is image file or Word document"""
    path = Path(file_path)
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif'}
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
        os.makedirs(output_dir, exist_ok=True)
        
        with zipfile.ZipFile(docx_path, 'r') as docx_zip:
            media_files = [f for f in docx_zip.infolist() 
                         if f.filename.startswith('word/media/') and 
                         f.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'))]
            
            logging.info(f"Found {len(media_files)} images in Word document")
            print(f"[DOC] Found {len(media_files)} images in Word document")
            
            for i, file_info in enumerate(media_files, 1):
                image_data = docx_zip.read(file_info.filename)
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
                
                logging.debug(f"Extracted image {i}/{len(media_files)}: {original_name}")
                print(f"  [OK] Extracted image {i}/{len(media_files)}: {original_name}")
        
        return extracted_images
    
    except Exception as e:
        logging.error(f"Failed to extract images: {str(e)}")
        return {'error': f'Failed to extract images: {str(e)}'}

def process_image_batch(batch_images, batch_num, confidence, verbose, timeout_per_image=30):
    """Process a single batch of images"""
    batch_results = []
    
    logging.info(f"\n{'='*70}")
    logging.info(f"BATCH {batch_num} START - Processing {len(batch_images)} images")
    logging.info(f"{'='*70}")
    print(f"\n[BATCH {batch_num}] Processing {len(batch_images)} images...")
    
    for image_info in batch_images:
        image_idx = image_info['index']
        image_path = image_info['path']
        
        logging.info(f"Image {image_idx}: Starting OCR analysis - {image_info['original_name']}")
        print(f"  [IMG {image_idx}] Processing: {image_info['original_name']}")
        
        cmd = [
            'python', 'scripts/simple_form_analyzer.py',
            image_path,
            '--confidence', str(confidence)
        ]
        
        if verbose:
            cmd.append('--verbose')
        
        temp_output = f"temp_analysis_{image_idx}.json"
        cmd.extend(['--output', temp_output])
        
        try:
            env = os.environ.copy()
            env['PYTHONWARNINGS'] = 'ignore::UserWarning'
            
            # Process with timeout per image
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_per_image,
                env=env
            )
            
            if result.returncode == 0:
                if os.path.exists(temp_output):
                    with open(temp_output, 'r') as f:
                        analysis_data = json.load(f)
                    
                    analysis_data['image_info'] = image_info
                    analysis_data['image_number'] = image_idx
                    batch_results.append({
                        'status': 'SUCCESS',
                        'image_index': image_idx,
                        'data': analysis_data
                    })
                    
                    logging.info(f"Image {image_idx}: OCR completed successfully")
                    print(f"    ✓ Image {image_idx} OCR completed")
                    
                    os.remove(temp_output)
                else:
                    logging.warning(f"Image {image_idx}: No output file generated")
                    batch_results.append({
                        'status': 'NO_OUTPUT',
                        'image_index': image_idx,
                        'error': 'No analysis results generated'
                    })
                    print(f"    ⚠ Image {image_idx}: No output file")
            else:
                logging.error(f"Image {image_idx}: OCR failed - {result.stderr[:200]}")
                batch_results.append({
                    'status': 'ERROR',
                    'image_index': image_idx,
                    'error': result.stderr[:200]
                })
                print(f"    ✗ Image {image_idx}: OCR failed")
        
        except subprocess.TimeoutExpired:
            logging.error(f"Image {image_idx}: OCR timed out after {timeout_per_image}s")
            batch_results.append({
                'status': 'TIMEOUT',
                'image_index': image_idx,
                'error': f'Timeout after {timeout_per_image}s'
            })
            print(f"    ⏱ Image {image_idx}: Timed out")
        
        except Exception as e:
            logging.error(f"Image {image_idx}: Processing error - {str(e)[:100]}")
            batch_results.append({
                'status': 'EXCEPTION',
                'image_index': image_idx,
                'error': str(e)[:100]
            })
            print(f"    ✗ Image {image_idx}: Exception")
    
    # Summary for this batch
    successful = sum(1 for r in batch_results if r['status'] == 'SUCCESS')
    failed = sum(1 for r in batch_results if r['status'] != 'SUCCESS')
    
    logging.info(f"BATCH {batch_num} COMPLETE - {successful} successful, {failed} failed")
    print(f"\n[BATCH {batch_num} SUMMARY] {successful}/{len(batch_images)} images processed successfully")
    
    return batch_results

def process_word_document_batched(docx_path, batch_size=5, confidence=25, verbose=False, timeout_per_image=30):
    """Process Word document in configurable batches"""
    
    logging.info(f"Starting batch processing: {Path(docx_path).name}")
    print(f"[PROC] Processing Word document in batches of {batch_size}: {Path(docx_path).name}")
    
    # Step 1: Extract images
    extracted_images = extract_images_from_word(docx_path)
    
    if isinstance(extracted_images, dict) and 'error' in extracted_images:
        logging.error(f"Image extraction failed: {extracted_images['error']}")
        return extracted_images
    
    if not extracted_images:
        logging.error("No images found in Word document")
        return {'error': 'No images found in the Word document'}
    
    total_images = len(extracted_images)
    logging.info(f"Total images to process: {total_images}")
    
    # Step 2: Process in batches
    all_batch_results = []
    batch_summaries = []
    
    num_batches = (total_images + batch_size - 1) // batch_size
    
    for batch_num in range(1, num_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(batch_num * batch_size, total_images)
        
        batch_images = extracted_images[start_idx:end_idx]
        
        # Process batch
        batch_results = process_image_batch(
            batch_images,
            batch_num,
            confidence,
            verbose,
            timeout_per_image
        )
        
        all_batch_results.extend(batch_results)
        
        # Track batch summary
        successful = sum(1 for r in batch_results if r['status'] == 'SUCCESS')
        batch_summaries.append({
            'batch_num': batch_num,
            'total': len(batch_results),
            'successful': successful,
            'failed': len(batch_results) - successful
        })
        
        logging.info(f"Batch {batch_num}/{num_batches} complete. Elapsed time checkpoint.")
        print(f"\n[PROGRESS] Batch {batch_num}/{num_batches} complete\n")
    
    # Step 3: Consolidate results from all batches
    logging.info("\n" + "="*70)
    logging.info("CONSOLIDATING RESULTS FROM ALL BATCHES")
    logging.info("="*70)
    
    consolidated_fields = []
    consolidated_categories = {}
    all_extracted_text = []
    successful_analyses = 0
    failed_analyses = 0
    
    for batch_result in all_batch_results:
        if batch_result['status'] == 'SUCCESS':
            successful_analyses += 1
            analysis_data = batch_result['data']
            
            # Consolidate fields
            fields = analysis_data.get('guidewire_fields', [])
            for field in fields:
                field['source_image'] = batch_result['image_index']
            consolidated_fields.extend(fields)
            
            # Consolidate categories
            categories = analysis_data.get('field_categories', {})
            for category, field_list in categories.items():
                if category in consolidated_categories:
                    consolidated_categories[category].extend(field_list)
                else:
                    consolidated_categories[category] = field_list
            
            # Consolidate text
            text = analysis_data.get('all_text', [])
            all_extracted_text.append({
                'image': batch_result['image_index'],
                'text': text
            })
        else:
            failed_analyses += 1
    
    # Step 4: Create final consolidated result
    final_summary = {
        'source_document': docx_path,
        'total_images_found': total_images,
        'total_images_processed': successful_analyses + failed_analyses,
        'total_images_successful': successful_analyses,
        'total_images_failed': failed_analyses,
        'total_fields_found': len(consolidated_fields),
        'field_categories_count': len(consolidated_categories),
        'batch_size': batch_size,
        'num_batches': num_batches,
        'batch_summaries': batch_summaries,
        'processing_timestamp': datetime.now().isoformat()
    }
    
    final_result = {
        'summary': final_summary,
        'guidewire_fields': consolidated_fields,
        'field_categories': consolidated_categories,
        'all_text': all_extracted_text,
        'batch_results': all_batch_results,  # Include detailed batch results
        'metadata': {
            'source_type': 'word_document',
            'source_file': docx_path,
            'batch_processing': True,
            'processing_engine': 'batch_word_document_processor'
        }
    }
    
    # Log final summary
    logging.info(f"\n{'='*70}")
    logging.info("FINAL PROCESSING SUMMARY")
    logging.info(f"{'='*70}")
    logging.info(f"Total images: {total_images}")
    logging.info(f"Successful: {successful_analyses}")
    logging.info(f"Failed: {failed_analyses}")
    logging.info(f"Total fields extracted: {len(consolidated_fields)}")
    logging.info(f"Total categories: {len(consolidated_categories)}")
    logging.info(f"{'='*70}")
    
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Total images found: {total_images}")
    print(f"Successfully processed: {successful_analyses}")
    print(f"Failed: {failed_analyses}")
    print(f"Total fields extracted: {len(consolidated_fields)}")
    print(f"Total categories: {len(consolidated_categories)}")
    print(f"{'='*70}\n")
    
    return final_result

def main():
    parser = argparse.ArgumentParser(
        description='Process Word documents with embedded images in batches for form analysis'
    )
    parser.add_argument('input_file', help='Path to Word document (.docx)')
    parser.add_argument('--output', '-o', help='Save consolidated results to JSON file')
    parser.add_argument('--batch-size', '-b', type=int, default=10, 
                       help='Number of images per batch (default: 10)')
    parser.add_argument('--confidence', '-c', type=int, default=20, 
                       help='OCR confidence threshold (default: 20)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--timeout', '-t', type=int, default=120,
                       help='Timeout per image in seconds (default: 120)')
    parser.add_argument('--log-dir', '-l', default='ocr_logs',
                       help='Directory for detailed logs (default: ocr_logs)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = setup_logging(args.log_dir)
    logging.info(f"Log file: {log_file}")
    print(f"[LOG] Detailed logs saved to: {log_file}\n")
    
    # Validate input file
    if not os.path.exists(args.input_file):
        logging.error(f"File not found: {args.input_file}")
        print(f"[ERROR] File not found: {args.input_file}")
        return 1
    
    # Check file type
    input_type = detect_input_type(args.input_file)
    if input_type != 'word_document':
        logging.error(f"File must be .docx. Detected type: {input_type}")
        print(f"[ERROR] File must be a Word document (.docx). Detected: {input_type}")
        return 1
    
    # Process with batch support
    result = process_word_document_batched(
        args.input_file,
        batch_size=args.batch_size,
        confidence=args.confidence,
        verbose=args.verbose,
        timeout_per_image=args.timeout
    )
    
    if isinstance(result, dict) and 'error' in result:
        logging.error(f"Processing error: {result['error']}")
        print(f"[ERROR] {result['error']}")
        return 1
    
    # Save consolidated results if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logging.info(f"Results saved to: {args.output}")
        print(f"[SAVE] Consolidated results saved to: {args.output}")
    
    # Clean up extracted images
    temp_dir = 'temp_word_images'
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
        logging.info(f"Cleaned up temporary directory: {temp_dir}")
        print(f"[CLEANUP] Removed temporary directory")
    
    logging.info("Processing complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())
