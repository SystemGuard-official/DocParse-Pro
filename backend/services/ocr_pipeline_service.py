import os
import csv
import time
import uuid
from PIL import Image
from typing import List
from pathlib import Path

from backend.schemas import ExtractedText, OcrJobResult
from backend.services.paddle_detection_service import paddle_ocr_service
from backend.services.trocr_service import trocr_model_manager
from backend.utils.image.processing import crop_image
from backend.utils.image.validation import load_image, validate_image_bytes
from backend.services.redis_job_manager import set_job_status
from backend.utils.logging.setup import logger
from backend.core.config import settings


ROOT_DIR = Path(__file__).parent.parent.parent
logger.info(f"ROOT_DIR: {ROOT_DIR}")

TRAIN_DIR = os.path.join(ROOT_DIR, 'trocr_training/images')
CSV_FILE = os.path.join(ROOT_DIR, 'trocr_training/labels.csv')

os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

def save_training_sample(cropped_image: Image.Image, text: str):
    file_id = uuid.uuid4().hex[:10]
    image_filename = f"{file_id}.png"
    image_path = os.path.join(TRAIN_DIR, image_filename)

    cropped_image.save(image_path)

    with open(CSV_FILE, mode="a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([image_filename, text])
        
def full_ocr_logic(filename, image_bytes, job_id) -> OcrJobResult:
    start_time = time.time()
    validate_image_bytes(image_bytes)
    
    # PaddleOCR text detection
    metadata, detections_raw = paddle_ocr_service.detect_text_bbox(image_bytes)
    
    detection_execution_time = time.time() - start_time
    detections: List[ExtractedText] = []
    for idx, detection in enumerate(detections_raw):
        try:
            # based on numeric bbox coordinates, update the progress bar in set_job_status
            set_job_status(job_id, "processing", progress=int(idx / len(detections_raw) * 100))

            crop_img_bytes = crop_image(image_bytes, detection.bbox.dict())
            crop_img = load_image(crop_img_bytes)
            extracted_text = trocr_model_manager.run_ocr(crop_img, 
                                                         trocr_model_manager.get_default_model())
            text = extracted_text if extracted_text else ""
            
            if settings.SAVE_TROCR_TRAINING_DATA:
                save_training_sample(crop_img, text)
                
        except Exception as e:
            logger.error(f"Error processing detection {idx}: {str(e)}")
            text = ""

        detections.append(ExtractedText(
            bbox=detection.bbox,
            width=detection.width,
            height=detection.height,
            text=text
        ))
    total_execution_time = time.time() - start_time
    return OcrJobResult(
        success=True,
        filename=filename,
        metadata=metadata,
        text_detection_duration=detection_execution_time,
        overall_processing_time=total_execution_time,
        message=f"Successfully detected {len(detections)} text regions",
        detections=detections,
        total_detections=len(detections)
    )
