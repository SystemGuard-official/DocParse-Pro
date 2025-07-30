# Schemas Module

This module contains all Pydantic models organized by functional domains for better maintainability and clarity.

## File Organization

### 📁 `__init__.py`
Main exports module that exposes all schemas for easy importing throughout the application.

### 📁 `core.py`
**Core Data Models** - Fundamental building blocks used across services:
- `BoundingBox` - Coordinate structure for text regions
- `DetectedTextRegion` - Text detection with bounding box
- `ExtractedText` - Text extraction with content

### 📁 `common.py` 
**Common Response Models** - Standardized responses across all services:
- `ApiErrorResponse` - Standardized error responses

### 📁 `ocr_responses.py`
**OCR Service Responses** - Response models for OCR processing endpoints:
- `TextDetectionResponse` - Text detection results
- `TrOcrExtractionResponse` - TrOCR extraction results  
- `OcrJobResult` - Complete OCR job results

### 📁 `ocr_jobs.py`
**OCR Job Management** - Job lifecycle management schemas:
- `OcrJobSubmissionResponse` - Job submission responses
- `OcrJobStatusResponse` - Job status queries
- `OcrJobListResponse` - Job listing responses

### 📁 `form_parsing.py`
**Form Parsing Service** - Form processing related schemas:
- `FormParsingResult` - Form parsing results
- `FormParsingJobSubmissionResponse` - Form job submissions
- `FormParsingJobStatusResponse` - Form job status
