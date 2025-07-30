from abc import ABC, abstractmethod
import time
from typing import List

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from fastapi import Query, HTTPException

from backend.utils.logging.setup import logger
from backend.schemas import TrOcrExtractionResponse
from backend.utils.image.validation import load_image, validate_image_bytes
from backend.core.config import settings


class OCRModelManager(ABC):
    """Abstract base class for OCR model management"""
    
    @abstractmethod
    def get_model(self, model_name: str) -> dict:
        """Get model and processor by name"""
        pass

    @abstractmethod
    def get_default_model(self) -> dict:
        """Get default model and processor"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass


class TrOCRManager(OCRModelManager):
    """Handles model loading and access"""
    def __init__(self):
        self.available_models = settings.TROCR_MODELS
        self.models = {
            name: self._load_model(path)
            for name, path in self.available_models.items()
        }

    def _load_model(self, model_name: str):
        logger.info(f"Loading model: {model_name}")
        processor = TrOCRProcessor.from_pretrained(model_name, use_fast=False)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        
        return {"processor": processor, "model": model, "device": device}

    def get_model(self, model_name: str):
        if model_name not in self.models:
            raise ValueError(f"Unsupported model: {model_name}")
        return self.models[model_name]

    def get_default_model(self):
        return self.get_model(settings.DEFAULT_TROCR_MODEL)

    def get_available_models(self) -> List[str]:
        """Get list of available TrOCR models"""
        return list(self.available_models.keys())
    
    def get_model_and_processor(self, model_name: str = Query(...)) -> dict:
        try:
            return trocr_model_manager.get_model(model_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def generate_response(self, filename: str, 
                          model_name: str, 
                          extracted_text: str, 
                          execution_time: float, 
                          image_bytes: bytes):
        
        return TrOcrExtractionResponse(
            success=True,
            message="OCR processing completed successfully.",
            model=model_name,
            filename=filename,
            file_size_kb=round(len(image_bytes) / 1024, 2),
            execution_time=round(execution_time, 3),
            extracted_text=extracted_text
        )
    
    def run_ocr(self, image: Image.Image, model_data: dict) -> str:
        try:
            processor = model_data["processor"]
            model = model_data["model"]
            device = model_data["device"]
            
            logger.info(f"Model loaded on device: {device}")
            
            pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values)
            
            return processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        except Exception:
            logger.exception("OCR generation failed")
            raise HTTPException(status_code=500, detail="Failed to generate OCR output.")
        
    
    def run_ocr_on_file(self, image_bytes: bytes, 
                        filename: str, 
                        model_data: dict) -> TrOcrExtractionResponse:
        start_time = time.time()
        validate_image_bytes(image_bytes)
        image = load_image(image_bytes)
        text = self.run_ocr(image, model_data)
        elapsed_time = time.time() - start_time
        return self.generate_response(filename, model_data["model"].name_or_path, text, elapsed_time, image_bytes)


    def run_ocr_default(self, 
                        image_bytes: bytes, 
                        filename: str) -> TrOcrExtractionResponse:
        
        start_time = time.time()
        validate_image_bytes(image_bytes)
        image = load_image(image_bytes)
        model_data = trocr_model_manager.get_default_model()
        text = self.run_ocr(image, model_data)
        elapsed_time = time.time() - start_time
        return self.generate_response(filename, model_data["model"].name_or_path, text, elapsed_time, image_bytes)

trocr_model_manager = TrOCRManager()
