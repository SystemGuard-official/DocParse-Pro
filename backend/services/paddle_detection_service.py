"""
OCR Service for text detection using PaddleOCR
"""
import io
import cv2
import time
import numpy as np
from PIL import Image
from paddleocr import TextDetection
from fastapi import HTTPException

from backend.utils.image.validation import validate_image_bytes
from backend.utils.logging.setup import logger
from backend.schemas import DetectedTextRegion, BoundingBox, TextDetectionResponse


class PaddleOCRHandler:
    """Service class for OCR operations using PaddleOCR"""

    def __init__(self):
        """Initialize PaddleOCR with best configuration for text detection"""
        self.text_detection_model = TextDetection()
    
    def detect_text_bbox(self, image_bytes: bytes):
        
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)

        # Get image size (height and width)
        metadata = self._extract_image_metadata(image, image_array, image_bytes)

        # Ensure image has 3 channels
        if image.mode != "RGB":
            image = image.convert("RGB")
        image_array = np.array(image)
        image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)


        logger.info(f"Image shape after processing: {image_array.shape}")

        results = self.text_detection_model.predict(image_array)
        
        # Extract bounding boxes from results
        bboxes = []
        if results and 'dt_polys' in results[0]:
            bboxes = results[0]['dt_polys']
        
        detections = []
        for bbox in bboxes:
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            width = x_max - x_min
            height = y_max - y_min

            bbox_coords = BoundingBox(
                x1=int(x_min),
                y1=int(y_min),
                x2=int(x_max),
                y2=int(y_max)
            )
            detection = DetectedTextRegion(
                bbox=bbox_coords,
                width=int(width),
                height=int(height),
            )            

            detections.append(detection)

        return metadata, detections

    def _extract_image_metadata(self, image: Image.Image, image_array: np.ndarray, image_bytes: bytes) -> dict:
        """Extract metadata from the image"""
        metadata = {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'size_bytes': len(image_bytes),
            'shape': image_array.shape if isinstance(image_array, np.ndarray) else None
        }
        logger.info(f"Extracted metadata: {metadata}")
        return metadata
    
    def detect_bbox_logic(self, image_bytes: bytes) -> TextDetectionResponse:
        start_time = time.time()
        (image_bytes)
        metadata, detections = self.detect_text_bbox(image_bytes)
        execution_time = time.time() - start_time
        
        return TextDetectionResponse(
            success=True,
            metadata=metadata,
            execution_time=execution_time,
            message=f"Successfully detected {len(detections)} text regions",
            detections=detections,
            total_detections=len(detections)
        )

paddle_ocr_service = PaddleOCRHandler()
