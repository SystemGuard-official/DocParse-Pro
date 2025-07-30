"""
Test script for Qwen Vision Service using polling API.
This script submits form parsing jobs and polls for results with 30-second intervals.
"""

import requests
import os
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
PARSE_ENDPOINT = f"{BASE_URL}/parse"
STATUS_ENDPOINT = f"{BASE_URL}/parse/status"
POLL_INTERVAL = 30  # seconds
MAX_POLL_ATTEMPTS = 10  # Maximum number of polling attempts (5 minutes total)
RESULTS_DIR = "data/qwen_test_results"
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

# Default test images directory
DEFAULT_IMAGE_DIR = "../data/images/set1"


def ensure_results_directory():
    """Create results directory if it doesn't exist"""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"✅ Created results directory: {RESULTS_DIR}")


def get_test_images(image_dir: str) -> list:
    """Get list of test images from directory and all subdirectories recursively"""
    if not os.path.exists(image_dir):
        print(f"❌ Image directory not found: {image_dir}")
        return []
    
    images = []
    
    # Walk through directory tree recursively
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                full_path = os.path.join(root, file)
                images.append(full_path)
                # Show relative path for cleaner output
                rel_path = os.path.relpath(full_path, image_dir)
                print(f"🖼️  Found: {rel_path}")
    
    print(f"📁 Found {len(images)} images total in {image_dir} (including subdirectories)")
    return images


def submit_form_parse_job(image_path: str) -> Optional[Dict[str, Any]]:
    """Submit a form parsing job and return the job submission response"""
    try:
        with open(image_path, 'rb') as img_file:
            files = {
                'file': (os.path.basename(image_path), img_file, 'image/png')
            }
            data = {
                'llm_prompt': '''IMAGE TO JSON - Extract ALL information from this form image and return ONLY a valid JSON object.
            - Do NOT return any commentary, description, example, or explanation—ONLY the JSON object.
            - The output MUST be a single, complete JSON object, only the assistance response no user prompt.
            - Include every field or element you can identify, preserving structure, grouping, and relationships.
            - Represent checkboxes/radios/dropdowns/tables/signatures/printed/handwritten/special elements/sections/empty/incomplete fields/validation/fine print as appropriate JSON keys/values.
            - Mark unclear or questionable values as "[UNCLEAR]".
            - If a field is empty, use null.
            - For lists, use JSON arrays.
            - For tables, use list of list to avoid duplicate,
            - For booleans (checkboxes, radios), use true/false.
            - For dates, use ISO format if possible.
            - For confidence, use a separate key per section: "confidence": 0.0 to 1.0.'''
            }
            
            print(f"🚀 Submitting job for: {os.path.basename(image_path)}")
            response = requests.post(
                PARSE_ENDPOINT,
                files=files,
                data=data,
                headers={"accept": "application/json"}
            )
            
            if response.status_code == 200:
                job_data = response.json()
                print(f"✅ Job submitted successfully. Job ID: {job_data.get('job_id')}")
                return job_data
            else:
                print(f"❌ Job submission failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Exception during job submission: {e}")
        return None


def poll_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Poll job status until completion or timeout"""
    print(f"🔄 Starting to poll job: {job_id}")
    
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        try:
            print(f"⏳ Polling attempt {attempt}/{MAX_POLL_ATTEMPTS} for job {job_id}")
            
            response = requests.get(
                f"{STATUS_ENDPOINT}/{job_id}",
                headers={"accept": "application/json"}
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                
                print(f"📊 Job {job_id} status: {status}")
                
                if status in ['completed', 'error']:
                    return status_data
                elif status in ['pending', 'processing']:
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


def save_result(image_name: str, job_id: str, result_data: Dict[str, Any]):
    """Save the result to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{image_name}_{job_id}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    # Add metadata to the result
    result_with_metadata = {
        "test_metadata": {
            "image_name": image_name,
            "job_id": job_id,
            "timestamp": timestamp,
            "test_script": "test_qwen_vision_polling.py"
        },
        "api_response": result_data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_with_metadata, f, ensure_ascii=False, indent=2)
        print(f"💾 Result saved to: {filepath}")
    except Exception as e:
        print(f"❌ Failed to save result: {e}")


def test_single_image(image_path: str) -> bool:
    """Test a single image through the complete pipeline"""
    image_name = os.path.basename(image_path)
    print(f"\n{'='*60}")
    print(f"🖼️  Testing image: {image_name}")
    print(f"{'='*60}")
    
    # Submit job
    job_response = submit_form_parse_job(image_path)
    if not job_response:
        print(f"❌ Failed to submit job for {image_name}")
        return False
    
    job_id = job_response.get('job_id')
    if not job_id:
        print(f"❌ No job ID received for {image_name}")
        return False
    
    # Poll for results
    result = poll_job_status(job_id)
    if not result:
        print(f"❌ Failed to get result for job {job_id}")
        return False
    
    # Save result
    save_result(image_name, job_id, result)
    
    # Print summary
    status = result.get('status')
    if status == 'completed':
        print(f"✅ Successfully processed {image_name}")
        if 'result' in result and result['result']:
            execution_time = result['result'].get('execution_time', 'N/A')
            print(f"⏱️  Execution time: {execution_time}s")
    elif status == 'error':
        print(f"❌ Processing failed for {image_name}")
        error_msg = result.get('message', 'Unknown error')
        print(f"💬 Error: {error_msg}")
    else:
        print(f"⚠️  Unexpected status for {image_name}: {status}")
    
    return status == 'completed'


def run_test_suite(image_dir: str = None):
    """Run the complete test suite"""
    print("🧪 Starting Qwen Vision Service Polling Test")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"⏰ Poll interval: {POLL_INTERVAL} seconds")
    print(f"🔄 Max poll attempts: {MAX_POLL_ATTEMPTS}")
    
    # Setup
    ensure_results_directory()
    
    # Get test images
    test_dir = image_dir or DEFAULT_IMAGE_DIR
    images = get_test_images(test_dir)
    
    if not images:
        print("❌ No test images found. Exiting.")
        return
    
    # Run tests
    total_images = len(images)
    successful_tests = 0
    failed_tests = 0
    
    start_time = time.time()
    
    for i, image_path in enumerate(images, 1):
        print(f"\n🏃 Running test {i}/{total_images}")
        
        success = test_single_image(image_path)
        if success:
            successful_tests += 1
        else:
            failed_tests += 1
        
        # Add delay between tests to avoid overwhelming the server
        if i < total_images:
            print(f"⏸️  Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"📊 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful tests: {successful_tests}/{total_images}")
    print(f"❌ Failed tests: {failed_tests}/{total_images}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"💾 Results saved in: {RESULTS_DIR}")
    
    if successful_tests == total_images:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed_tests} test(s) failed")


def main():
    """Main entry point"""
    import argparse
    
    # Declare global variables at the start of the function
    global BASE_URL, PARSE_ENDPOINT, STATUS_ENDPOINT
    
    parser = argparse.ArgumentParser(description="Test Qwen Vision Service with polling")
    parser.add_argument(
        "--image-dir", 
        type=str, 
        help=f"Directory containing test images (default: {DEFAULT_IMAGE_DIR})"
    )
    parser.add_argument(
        "--single-image", 
        type=str, 
        help="Test a single image file"
    )
    parser.add_argument(
        "--base-url", 
        type=str, 
        default=BASE_URL,
        help=f"Base URL for the API (default: {BASE_URL})"
    )
    
    args = parser.parse_args()
    
    # Update global configuration
    if args.base_url:
        BASE_URL = args.base_url
        PARSE_ENDPOINT = f"{BASE_URL}/parse"
        STATUS_ENDPOINT = f"{BASE_URL}/parse/status"
    
    if args.single_image:
        # Test single image
        if os.path.exists(args.single_image):
            ensure_results_directory()
            test_single_image(args.single_image)
        else:
            print(f"❌ Image file not found: {args.single_image}")
    else:
        # Run full test suite
        run_test_suite(args.image_dir)


if __name__ == "__main__":
    main()
