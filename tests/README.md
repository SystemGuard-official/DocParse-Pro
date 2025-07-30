# OCR Pipeline Test Documentation

This directory contains comprehensive test scripts for the OCR pipeline service with text detection, recognition, job polling, and result visualization capabilities.

## Files Overview

### `test_ocr_pipeline_e2e.py` - End-to-End OCR Pipeline Test

The main comprehensive test script for OCR pipeline testing with:

- **Text detection and recognition** via OCR API
- **Job submission and polling** with 30-second intervals
- **Image annotation** with detected text and bounding boxes
- **Batch processing** with concurrent execution support
- **Result visualization** and comprehensive logging

### `test_qwen_form_parsing.py` - Qwen Vision Service Test

Specialized test script for Qwen vision form parsing service with:

- **Form parsing** via Qwen vision API
- **Polling with 30-second intervals**
- **Result persistence** to JSON files
- **Error handling** and detailed logging

## Usage Examples

### OCR Pipeline Testing

#### Basic Usage - Single Image
```bash
# Test a single image with text and bounding boxes
python tests/test_ocr_pipeline_e2e.py --single-image path/to/image.png --draw-text --draw-boxes

# Test with confidence scores
python tests/test_ocr_pipeline_e2e.py --single-image path/to/image.png --draw-text --draw-boxes --draw-conf

# Use original image as background
python tests/test_ocr_pipeline_e2e.py --single-image path/to/image.png --draw-text --draw-original
```

#### Batch Processing
```bash
# Test all images in a directory
python tests/test_ocr_pipeline_e2e.py --image-dir data/images/set1 --draw-text --draw-boxes

# Concurrent batch processing (faster)
python tests/test_ocr_pipeline_e2e.py --image-dir data/images/set1 --draw-text --draw-boxes --concurrent --max-workers 5

# Custom API endpoint
python tests/test_ocr_pipeline_e2e.py --image-dir data/images --base-url http://10.1.0.19:8000/api/v1 --draw-text
```

### Qwen Vision Testing

#### Basic Usage
```bash
# Test all images in default directory
python tests/test_qwen_form_parsing.py

# Test specific directory | batch processing
python tests/test_qwen_form_parsing.py --image-dir data/images/set2

# Test single image
python tests/test_qwen_form_parsing.py --single-image path/to/form.png

# Custom API endpoint
python tests/test_qwen_form_parsing.py --base-url http://10.1.0.19:8000/api/v1
```
