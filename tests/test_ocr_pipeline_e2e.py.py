"""
End-to-End OCR Pipeline Test Script

This script provides comprehensive testing for the OCR pipeline service with:
- Text detection and recognition
- Job submission and polling
- Image annotation with detected text
- Batch processing capabilities
- Result visualization and saving

Usage:
    python e2e_ocr_pipeline.py --image-dir path/to/images --draw-text --draw-boxes
    python e2e_ocr_pipeline.py --single-image path/to/image.png
    python e2e_ocr_pipeline.py --help
"""

import requests
import os
import time
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import io
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import sys

# ==================== CONFIGURATION ====================

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEXT_DETECT_ENDPOINT = f"{BASE_URL}/ocr"
OCR_GET_JOB_RESULT = f"{BASE_URL}/ocr/status"

# Polling Configuration
POLL_INTERVAL = 30  # seconds
MAX_POLL_ATTEMPTS = 10  # Maximum polling attempts (5 minutes total)

# Font Configuration
FONT_PATHS = [
    "arial.ttf", 
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/System/Library/Fonts/Arial.ttf",  # macOS
    "C:/Windows/Fonts/arial.ttf"  # Windows
]
DEFAULT_FONT_SIZE = 14
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 300

# File Extensions
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

# Output Configuration
RESULTS_DIR = "data/ocr_test_results"
OUTPUT_SUFFIX = "_detected"

# ==================== UTILITY FUNCTIONS ====================

def ensure_results_directory():
    """Create results directory if it doesn't exist"""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"✅ Created results directory: {RESULTS_DIR}")


def get_test_images(image_dir: str) -> List[str]:
    """Get list of test images from directory"""
    if not os.path.exists(image_dir):
        print(f"❌ Image directory not found: {image_dir}")
        return []
    
    images = [
        os.path.join(image_dir, f)
        for f in os.listdir(image_dir)
        if f.lower().endswith(IMAGE_EXTENSIONS) and OUTPUT_SUFFIX not in f
    ]
    
    print(f"📁 Found {len(images)} images in {image_dir}")
    return images


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON from {file_path}: {e}")
        return {}


def save_json(data: Dict[str, Any], file_path: str):
    """Save data to JSON file with error handling"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved JSON data to: {file_path}")
    except Exception as e:
        print(f"❌ Failed to save JSON to {file_path}: {e}")


def save_result_with_metadata(image_name: str, job_id: str, result_data: Dict[str, Any]):
    """Save OCR result with test metadata"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ocr_{image_name}_{job_id}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    # Add metadata to the result
    result_with_metadata = {
        "test_metadata": {
            "image_name": image_name,
            "job_id": job_id,
            "timestamp": timestamp,
            "test_script": "e2e_ocr_pipeline.py",
            "api_base_url": BASE_URL
        },
        "ocr_result": result_data
    }
    
    save_json(result_with_metadata, filepath)
# ==================== FONT HANDLING ====================

def get_available_font(font_size: int = DEFAULT_FONT_SIZE) -> ImageFont.FreeTypeFont:
    """Get the first available font from the font paths"""
    for font_path in FONT_PATHS:
        try:
            return ImageFont.truetype(font_path, font_size)
        except (IOError, OSError):
            continue
    
    # Fallback to default font
    try:
        return ImageFont.load_default()
    except Exception:
        print("⚠️  Using basic default font")
        return ImageFont.load_default()


def fit_text_to_box(text: str, bbox_width: int, bbox_height: int, 
                   min_font_size: int = MIN_FONT_SIZE, 
                   max_font_size: int = MAX_FONT_SIZE) -> Optional[ImageFont.FreeTypeFont]:
    """
    Find the largest font size that fits the text within the given bounding box
    
    Args:
        text: Text to fit
        bbox_width: Width of the bounding box
        bbox_height: Height of the bounding box
        min_font_size: Minimum font size to try
        max_font_size: Maximum font size to try
        
    Returns:
        Font object that fits the text, or None if no font fits
    """
    if not text or bbox_width <= 0 or bbox_height <= 0:
        return None
    
    best_font = None
    lo, hi = min_font_size, max_font_size
    
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            font = get_available_font(mid)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if text_width <= bbox_width and text_height <= bbox_height:
                best_font = font
                lo = mid + 1
            else:
                hi = mid - 1
        except Exception as e:
            print(f"⚠️  Font fitting error at size {mid}: {e}")
            hi = mid - 1
    
    return best_font if best_font else get_available_font(min_font_size)

# ==================== API INTERACTION ====================

def submit_ocr_job(image_path: str) -> Optional[Dict[str, Any]]:
    """Submit an OCR job and return the job submission response"""
    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': (os.path.basename(image_path), img_file, 'image/png')}
            
            print(f"🚀 Submitting OCR job for: {os.path.basename(image_path)}")
            response = requests.post(
                TEXT_DETECT_ENDPOINT,
                files=files,
                headers={"accept": "application/json"}
            )
            
            if response.status_code == 200:
                job_data = response.json()
                print(f"✅ OCR job submitted successfully. Job ID: {job_data.get('job_id')}")
                return job_data
            else:
                print(f"❌ OCR job submission failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Exception during OCR job submission: {e}")
        return None


def poll_ocr_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Poll OCR job status until completion or timeout"""
    print(f"🔄 Starting to poll OCR job: {job_id}")
    
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        try:
            print(f"⏳ Polling attempt {attempt}/{MAX_POLL_ATTEMPTS} for job {job_id}")
            
            response = requests.get(
                f"{OCR_GET_JOB_RESULT}/{job_id}",
                headers={"accept": "application/json"}
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 'Unknown')
                
                print(f"📊 Job {job_id} status: {status} (progress: {progress})")
                
                if status == "completed":
                    print(f"✅ Job {job_id} completed successfully")
                    return status_data
                elif status == "error":
                    print(f"❌ Job {job_id} failed with error")
                    return status_data
                elif status in ["pending", "processing"]:
                    if attempt < MAX_POLL_ATTEMPTS:
                        print(f"⏰ Waiting {POLL_INTERVAL} seconds before next poll...")
                        time.sleep(POLL_INTERVAL)
                    else:
                        print(f"⏰ Maximum polling attempts reached for job {job_id}")
                        return status_data
                else:
                    print(f"❓ Unknown status: {status}")
                    return status_data
            else:
                print(f"❌ Status check failed: {response.status_code} - {response.text}")
                if attempt < MAX_POLL_ATTEMPTS:
                    print(f"⏰ Waiting {POLL_INTERVAL} seconds before retry...")
                    time.sleep(POLL_INTERVAL)
                else:
                    return None
                    
        except Exception as e:
            print(f"❌ Exception during status polling: {e}")
            if attempt < MAX_POLL_ATTEMPTS:
                print(f"⏰ Waiting {POLL_INTERVAL} seconds before retry...")
                time.sleep(POLL_INTERVAL)
            else:
                return None
    
    return None

# ==================== IMAGE ANNOTATION ====================

def annotate_image_with_boxes(
    input_image: Image.Image, 
    detections: List[Dict[str, Any]], 
    output_path: str,
    draw_rectangle: bool = False, 
    draw_text: bool = False, 
    draw_conf: bool = False
) -> bool:
    """
    Annotate image with detected text boxes and content
    
    Args:
        input_image: PIL Image object to annotate
        detections: List of detection results with bbox and text
        output_path: Path to save the annotated image
        draw_rectangle: Whether to draw bounding boxes
        draw_text: Whether to draw extracted text
        draw_conf: Whether to draw confidence scores
        
    Returns:
        True if annotation successful, False otherwise
    """
    try:
        draw = ImageDraw.Draw(input_image)
        annotation_count = 0

        for det in detections:
            bbox = det.get('bbox', {})
            text = det.get('text', '')
            conf = det.get('confidence', 0.0)

            x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
            width = det.get('width', x2 - x1)
            height = det.get('height', y2 - y1)

            # Draw bounding rectangle
            if draw_rectangle:
                draw.rectangle([(x1, y1), (x2, y2)], outline="blue", width=2)

            # Draw extracted text
            if draw_text and text:
                font = fit_text_to_box(text, width, height)
                if font:
                    # Center text inside the box
                    try:
                        text_width = font.getlength(text)
                        bbox_text = draw.textbbox((0, 0), text, font=font)
                        text_height = bbox_text[3] - bbox_text[1]
                        text_x = x1 + (width - text_width) / 2
                        text_y = y1 + (height - text_height) / 2
                        
                        draw.text((text_x, text_y), text, fill="black", font=font)
                    except Exception as e:
                        print(f"⚠️  Text drawing error: {e}")
                        # Fallback to simple text placement
                        draw.text((x1 + 2, y1 + 2), text, fill="black")

            # Draw confidence score
            if draw_conf and conf is not None:
                conf_font = get_available_font(12)
                draw.text((x1 + 2, y1 + 2), f"{conf:.2f}", fill="red", font=conf_font)
            
            annotation_count += 1

        input_image.save(output_path)
        print(f"✅ Annotated image saved to {output_path} ({annotation_count} detections)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to annotate image: {e}")
        return False

# ==================== MAIN PIPELINE FUNCTIONS ====================

def process_single_image(
    image_path: str,
    draw_original: bool = False,
    draw_rectangle: bool = True,
    draw_text: bool = True,
    draw_conf: bool = False,
    save_results: bool = True
) -> bool:
    """
    Process a single image through the complete OCR pipeline
    
    Args:
        image_path: Path to the input image
        draw_original: Use original image as canvas (vs white background)
        draw_rectangle: Draw bounding boxes around detected text
        draw_text: Draw extracted text within boxes
        draw_conf: Draw confidence scores
        save_results: Save JSON results and annotated images
        
    Returns:
        True if processing successful, False otherwise
    """
    image_name = os.path.basename(image_path)
    print(f"\n{'='*60}")
    print(f"🖼️  Processing image: {image_name}")
    print(f"{'='*60}")
    
    # Step 1: Submit OCR job
    job_response = submit_ocr_job(image_path)
    if not job_response:
        print(f"❌ Failed to submit OCR job for {image_name}")
        return False
    
    job_id = job_response.get('job_id')
    if not job_id:
        print(f"❌ No job ID received for {image_name}")
        return False
    
    # Step 2: Poll for results
    job_result = poll_ocr_job_status(job_id)
    if not job_result:
        print(f"❌ Failed to get OCR job result for {image_name}")
        return False
    
    # Step 3: Process results
    status = job_result.get('status')
    if status != 'completed':
        print(f"❌ OCR job not completed. Status: {status}")
        if status == 'error':
            error_msg = job_result.get('message', 'Unknown error')
            print(f"💬 Error: {error_msg}")
        return False
    
    # Extract detection results
    ocr_result = job_result.get('result', {})
    if not ocr_result or not ocr_result.get('success'):
        print(f"❌ OCR processing failed for {image_name}")
        return False
    
    detections = ocr_result.get('detections', [])
    metadata = ocr_result.get('metadata', {})
    
    if not detections:
        print(f"⚠️  No text detected in {image_name}")
        return True
    
    print(f"📝 Found {len(detections)} text detections")
    
    # Step 4: Create annotated image
    try:
        original_img = Image.open(image_path).convert("RGB")
        img_width = metadata.get('width', original_img.width)
        img_height = metadata.get('height', original_img.height)
        
        if draw_original:
            canvas_img = original_img.copy()
        else:
            canvas_img = Image.new("RGB", (img_width, img_height), color="white")
        
        # Generate output paths
        base_name = os.path.splitext(image_path)[0]
        output_img_path = f"{base_name}{OUTPUT_SUFFIX}.png"
        
        # Annotate image
        success = annotate_image_with_boxes(
            canvas_img, detections, output_img_path,
            draw_rectangle=draw_rectangle,
            draw_text=draw_text,
            draw_conf=draw_conf
        )
        
        if not success:
            print(f"❌ Failed to annotate image {image_name}")
            return False
        
        # Step 5: Save results
        if save_results:
            ensure_results_directory()
            save_result_with_metadata(image_name, job_id, job_result)
            
            # Also save raw response
            response_filename = f"{base_name}_response.json"
            save_json(job_result, response_filename)
        
        # Step 6: Print summary
        execution_time = ocr_result.get('execution_time', 'N/A')
        print(f"⏱️  Execution time: {execution_time}s")
        print(f"📊 Detection summary: {len(detections)} text regions found")
        
        # Show sample detections
        for i, det in enumerate(detections[:3]):
            text = det.get('text', '')[:50]
            conf = det.get('confidence', 0)
            print(f"   {i+1}. \"{text}...\" (confidence: {conf:.2f})")
        
        if len(detections) > 3:
            print(f"   ... and {len(detections) - 3} more detections")
        
        print(f"✅ Successfully processed {image_name}")
        return True
        
    except Exception as e:
        print(f"❌ Exception during image processing: {e}")
        return False

def run_batch_processing(
    image_dir: str,
    draw_original: bool = False,
    draw_rectangle: bool = True,
    draw_text: bool = True,
    draw_conf: bool = False,
    max_workers: int = 3
) -> Tuple[int, int]:
    """
    Process multiple images in batch with concurrent processing
    
    Args:
        image_dir: Directory containing images to process
        draw_original: Use original image as canvas
        draw_rectangle: Draw bounding boxes
        draw_text: Draw extracted text
        draw_conf: Draw confidence scores
        max_workers: Maximum number of concurrent workers
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    print("🧪 Starting OCR Pipeline Batch Test")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"⏰ Poll interval: {POLL_INTERVAL} seconds")
    print(f"🔄 Max poll attempts: {MAX_POLL_ATTEMPTS}")
    print(f"👥 Max workers: {max_workers}")
    
    # Setup
    ensure_results_directory()
    
    # Get test images
    images = get_test_images(image_dir)
    if not images:
        print("❌ No test images found. Exiting.")
        return 0, 0
    
    total_images = len(images)
    successful_tests = 0
    failed_tests = 0
    
    start_time = time.time()
    
    if max_workers == 1:
        # Sequential processing
        for i, image_path in enumerate(images, 1):
            print(f"\n🏃 Processing image {i}/{total_images}")
            success = process_single_image(
                image_path,
                draw_original=draw_original,
                draw_rectangle=draw_rectangle,
                draw_text=draw_text,
                draw_conf=draw_conf
            )
            
            if success:
                successful_tests += 1
            else:
                failed_tests += 1
            
            # Add delay between tests to avoid overwhelming the server
            if i < total_images:
                print(f"⏸️  Waiting 5 seconds before next test...")
                time.sleep(5)
    else:
        # Concurrent processing
        print(f"🚀 Starting concurrent processing with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_image = {
                executor.submit(
                    process_single_image,
                    image_path,
                    draw_original,
                    draw_rectangle,
                    draw_text,
                    draw_conf
                ): image_path for image_path in images
            }
            
            # Collect results
            for future in as_completed(future_to_image):
                image_path = future_to_image[future]
                try:
                    success = future.result()
                    if success:
                        successful_tests += 1
                    else:
                        failed_tests += 1
                except Exception as e:
                    print(f"❌ Exception processing {os.path.basename(image_path)}: {e}")
                    failed_tests += 1
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful tests: {successful_tests}/{total_images}")
    print(f"❌ Failed tests: {failed_tests}/{total_images}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"⚡ Average time per image: {total_time/total_images:.2f} seconds")
    print(f"💾 Results saved in: {RESULTS_DIR}")
    
    if successful_tests == total_images:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed_tests} test(s) failed")
    
    return successful_tests, failed_tests


# ==================== COMMAND LINE INTERFACE ====================

def main():
    """Main entry point with command line argument parsing"""
    global BASE_URL, TEXT_DETECT_ENDPOINT, OCR_GET_JOB_RESULT
    
    parser = argparse.ArgumentParser(
        description="End-to-End OCR Pipeline Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all images in a directory with text and boxes
  python e2e_ocr_pipeline.py --image-dir data/images/set1 --draw-text --draw-boxes
  
  # Test a single image
  python e2e_ocr_pipeline.py --single-image path/to/image.png --draw-text
  
  # Batch test with custom API endpoint
  python e2e_ocr_pipeline.py --image-dir data/images --base-url http://10.1.0.19:8000/api/v1
  
  # Concurrent processing
  python e2e_ocr_pipeline.py --image-dir data/images --concurrent --max-workers 5
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--image-dir", 
        type=str,
        help="Directory containing test images"
    )
    input_group.add_argument(
        "--single-image", 
        type=str,
        help="Test a single image file"
    )
    
    # Annotation options
    parser.add_argument(
        "--draw-text",
        action="store_true",
        help="Draw extracted text within bounding boxes"
    )
    parser.add_argument(
        "--draw-boxes",
        action="store_true", 
        help="Draw bounding boxes around detected text"
    )
    parser.add_argument(
        "--draw-conf",
        action="store_true",
        help="Draw confidence scores"
    )
    parser.add_argument(
        "--draw-original",
        action="store_true",
        help="Use original image as background (instead of white)"
    )
    
    # Processing options
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Use concurrent processing for batch operations"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum number of concurrent workers (default: 3)"
    )
    
    # API configuration
    parser.add_argument(
        "--base-url",
        type=str,
        default=BASE_URL,
        help=f"Base URL for the API (default: {BASE_URL})"
    )
    
    args = parser.parse_args()
    
    # Update global configuration
    if args.base_url != BASE_URL:
        BASE_URL = args.base_url
        TEXT_DETECT_ENDPOINT = f"{BASE_URL}/ocr"
        OCR_GET_JOB_RESULT = f"{BASE_URL}/ocr/status"
        print(f"🌐 Using custom API endpoint: {BASE_URL}")
    
    # Process based on arguments
    if args.single_image:
        # Test single image
        if os.path.exists(args.single_image):
            ensure_results_directory()
            success = process_single_image(
                args.single_image,
                draw_original=args.draw_original,
                draw_rectangle=args.draw_boxes,
                draw_text=args.draw_text,
                draw_conf=args.draw_conf
            )
            
            if success:
                print("🎉 Single image test completed successfully!")
                sys.exit(0)
            else:
                print("❌ Single image test failed!")
                sys.exit(1)
        else:
            print(f"❌ Image file not found: {args.single_image}")
            sys.exit(1)
    
    elif args.image_dir:
        # Batch processing
        if not os.path.exists(args.image_dir):
            print(f"❌ Image directory not found: {args.image_dir}")
            sys.exit(1)
        
        max_workers = 1 if not args.concurrent else args.max_workers
        
        successful, failed = run_batch_processing(
            args.image_dir,
            draw_original=args.draw_original,
            draw_rectangle=args.draw_boxes,
            draw_text=args.draw_text,
            draw_conf=args.draw_conf,
            max_workers=max_workers
        )
        
        if failed == 0:
            print("🎉 All batch tests completed successfully!")
            sys.exit(0)
        else:
            print(f"⚠️  Batch testing completed with {failed} failures")
            sys.exit(1)


# ==================== LEGACY COMPATIBILITY ====================

def process_and_annotate(input_img_path, draw_original=False, draw_rectangle=False, draw_text=False, draw_conf=False):
    """
    Legacy function for backward compatibility
    Wrapper around the new process_single_image function
    """
    print("⚠️  Using legacy function. Consider migrating to process_single_image()")
    return process_single_image(
        input_img_path,
        draw_original=draw_original,
        draw_rectangle=draw_rectangle,
        draw_text=draw_text,
        draw_conf=draw_conf
    )


if __name__ == "__main__":
    main()
