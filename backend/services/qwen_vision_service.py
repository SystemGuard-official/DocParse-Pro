from transformers import AutoModelForVision2Seq, AutoTokenizer, AutoProcessor
from PIL import Image
import torch
import io
import time
import numpy as np
from backend.schemas import FormParsingResult
from backend.utils.logging.setup import logger
from backend.utils.response_parser import extract_and_parse_json
import gc
from backend.core.config import settings

# Device setup and logging
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Selected device: {device} (CUDA available: {torch.cuda.is_available()})")

# Only proceed if CUDA is available
if not torch.cuda.is_available():
    logger.error("CUDA is not available. Qwen vision service requires GPU for reasonable performance.")
    tokenizer = None
    processor = None
    model = None
else:
    # Clear GPU cache before loading model
    torch.cuda.empty_cache()
    gc.collect()
    logger.info(f"GPU memory before model loading: {torch.cuda.memory_allocated()/1024**3:.2f} GB")

    tokenizer = AutoTokenizer.from_pretrained(settings.QWEN_VL_MODEL, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(settings.QWEN_VL_MODEL, trust_remote_code=True)
    # Load model with memory optimization (GPU only)
    model = AutoModelForVision2Seq.from_pretrained(
        settings.QWEN_VL_MODEL,
        device_map=settings.DEVICE_MAP,
        trust_remote_code=settings.TRUST_REMOTE_CODE,
        torch_dtype=torch.float16,  # Always use float16 for GPU to save memory
        low_cpu_mem_usage=settings.LOW_CPU_MEM_USAGE,  # Reduce CPU memory usage during loading
        load_in_8bit=settings.LOAD_IN_8BIT,  # Set to True if you have bitsandbytes installed for even more memory savings
    )

    model.eval()

    # Log memory usage after model loading
    torch.cuda.empty_cache()
    gc.collect()
    logger.info(f"GPU memory after model loading: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    logger.info(f"GPU memory reserved: {torch.cuda.memory_reserved()/1024**3:.2f} GB")
    logger.info("Model loaded on GPU with memory optimization.")

class QwenFormParser:
    def __init__(self):
        if not torch.cuda.is_available() or model is None:
            logger.warning("QwenFormParser initialized but GPU/model not available")
    
    def _check_gpu_available(self):
        """Check if GPU and model are available for inference"""
        if not torch.cuda.is_available():
            raise RuntimeError("GPU is required for Qwen vision service but CUDA is not available")
        if model is None or tokenizer is None or processor is None:
            raise RuntimeError("Model not loaded. GPU may not have been available during initialization")
    
    def _extract_image_metadata(self, image: Image.Image, image_array: np.ndarray, image_bytes: bytes) -> dict:
        metadata = {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'size_bytes': len(image_bytes),
            'shape': image_array.shape if isinstance(image_array, np.ndarray) else None
        }
        return metadata

    def parse_form_image_comprehensive(self, image_bytes: bytes, llm_prompt: str) -> str:
        # Check if GPU and model are available
        self._check_gpu_available()
        
        # Clear GPU cache before processing
        torch.cuda.empty_cache()
        gc.collect()
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        prompt = f"""
         <|im_start|>user
         
            {llm_prompt}
            
            <|vision_start|><|image_pad|><|vision_end|>
            <|im_end|>
            <|im_start|>assistant
            """
        start_infer = time.time()
        
        try:
            if processor is None:
                raise RuntimeError("Processor is not initialized. Ensure CUDA is available and the model is loaded.")
            inputs = processor(
                text=[prompt],
                images=[image],
                return_tensors="pt",
                padding=True
            )
            # Explicitly move tensors to device
            for k in inputs:
                if isinstance(inputs[k], torch.Tensor):
                    inputs[k] = inputs[k].to(device)
            logger.info(f"Inputs moved to device: {device}")
            
            if model is None:
                raise RuntimeError("Model is not initialized. Ensure CUDA is available and the model is loaded.")
            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    do_sample=True,
                    temperature=0.1,
                    top_p=0.9,
                    repetition_penalty=1.05,
                    eos_token_id=tokenizer.eos_token_id if tokenizer is not None else None,
                    pad_token_id=tokenizer.pad_token_id if tokenizer is not None else None
                )
            
            infer_time = time.time() - start_infer
            logger.info(f"Inference time: {infer_time:.2f} seconds")
            result = tokenizer.decode(output[0], skip_special_tokens=True).strip()
            
            # Clean up tensors immediately
            del inputs, output
            torch.cuda.empty_cache()
            gc.collect()
            
            json_result = extract_and_parse_json(result)
            if json_result is not None:
                return json_result
            logger.warning("Failed to extract valid JSON, returning raw output.")
            return result
            
        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"CUDA out of memory: {e}")
            
            # Clear cache and try to recover
            torch.cuda.empty_cache()
            gc.collect()
            raise RuntimeError(f"CUDA out of memory. Try using a smaller model or reduce batch size. Details: {e}")
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            # Clean up on error
            torch.cuda.empty_cache()
            gc.collect()
            raise

    def parse_form_complete(self, filename: str, image_bytes: bytes, llm_prompt: str) -> FormParsingResult:
        start_time = time.time()
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        data = self.parse_form_image_comprehensive(image_bytes, llm_prompt)
        metadata = self._extract_image_metadata(image, image_array, image_bytes)
        execution_time = time.time() - start_time
        
        return FormParsingResult(
            success=True,
            metadata=metadata,
            filename=filename,
            execution_time=execution_time,
            data=data
        )

def clear_gpu_memory():
    """Clear GPU memory and run garbage collection"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()
        logger.info(f"GPU memory cleared. Current usage: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    else:
        logger.warning("GPU not available for memory clearing")

# Only create parser instance if GPU is available
if torch.cuda.is_available() and model is not None:
    qwen_parser = QwenFormParser()
    logger.info("Qwen vision service initialized successfully with GPU")
else:
    qwen_parser = None
    logger.warning("Qwen vision service not available - GPU required")
