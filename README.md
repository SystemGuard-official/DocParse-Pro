# OCR & Form Parsing API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![GPU](https://img.shields.io/badge/CUDA-Supported-green?style=flat&logo=nvidia)](https://developer.nvidia.com/cuda-zone)

OCR and form parsing API with queue-based processing, supporting both TrOCR and Qwen Vision models for optimal document processing workflows.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU with CUDA support (recommended)
- 8GB+ available GPU memory

### Deployment

**Step 1: Create Required Directories**
```bash
# Create training data directory (required for mounted volume)
mkdir /home/trocr_training
sudo chown -R 1000:1000 /home/trocr_training
```

**Step 2: Deploy Services**
```bash
# GPU deployment (recommended)
bash deploy.sh gpu

# CPU deployment (fallback)
bash deploy.sh cpu
```

The API will be available at `http://localhost:8000`

> **Note**: The `/home/trocr_training` directory will store training examples for improving TrOCR models.

## 📋 API Overview

### Current Configuration: Qwen Vision Mode

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/` | GET | API documentation and health status |
| `/api/v1/parse` | POST | Submit form parsing job |
| `/api/v1/parse/priority` | POST | Submit high-priority parsing job |
| `/api/v1/parse/status/{job_id}` | GET | Check job status and retrieve results |
| `/api/v1/parse/queue/status` | GET | Monitor queue performance |
| `/api/v1/parse/health` | GET | Worker health diagnostics |
| `/api/v1/parse/gpu/status` | GET | GPU resource monitoring |

### Alternative Configuration: TrOCR Mode

When `DEPLOYED_OCR=TrOCR` is configured:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/` | GET | Available TrOCR models list |
| `/api/v1/` | POST | Submit OCR job to queue |
| `/api/v1/priority` | POST | Submit high-priority OCR job |
| `/api/v1/status/{job_id}` | GET | Check OCR job status and results |
| `/api/v1/queue/status` | GET | Monitor OCR queue performance |
| `/api/v1/health` | GET | OCR worker health diagnostics |

### Request Example

**Form Parsing (Qwen Vision Mode):**
```bash
curl -X POST "http://localhost:8000/api/v1/parse" \
  -F "file=@document.png" \
  -F "llm_prompt=Extract all form fields as JSON"
```

**OCR Processing (TrOCR Mode):**
```bash
curl -X POST "http://localhost:8000/api/v1/" \
  -F "file=@document.png"
```

### Response Example

**Job Submission Response:**
```json
{
  "success": true,
  "job_id": "uuid-string",
  "message": "Form parse job submitted. Poll for status using job_id."
}
```

**Job Status Response:**
```json
{
  "success": true,
  "status": "completed",
  "message": "Job completed successfully",
  "result": {
    "success": true,
    "filename": "document.png",
    "execution_time": 102.5,
    "data": { /* extracted content */ }
  }
}
```

## 🏗️ Architecture

### Queue-Based Processing
- **Asynchronous job processing** with unique job IDs
- **Priority queue support** for urgent documents
- **GPU resource management** with automatic memory optimization
- **Redis-backed job status** tracking

### Supported Models
- **Qwen Vision**: Advanced form parsing and document understanding
- **TrOCR**: Traditional OCR for text extraction
- **PaddleOCR**: Text detection and bounding box identification

## 🔧 Configuration

### Switching Between Modes

The API supports two operational modes, configured via config file.

**Qwen Vision Mode (Current Default):**
```bash
DEPLOYED_OCR=Qwen          # Enables form parsing endpoints
QWEN_VL_MODEL=Qwen/Qwen2.5-VL-3B-Instruct
```

**TrOCR Mode:**
```bash
DEPLOYED_OCR=TrOCR         # Enables OCR processing endpoints
DEFAULT_TROCR_MODEL=trocr-large-stage1
```


### GPU Requirements

| Model | GPU Memory | Recommended |
|-------|------------|-------------|
| Qwen Vision | 8GB+ | 16GB+ |
| TrOCR | 4GB+ | 8GB+ |

## 📊 Monitoring & Operations

### Health Checks

```bash
# Overall API health
curl http://localhost:8000/health

# Worker-specific health
curl http://localhost:8000/api/v1/parse/health

# GPU resource status
curl http://localhost:8000/api/v1/parse/gpu/status
```

### Queue Monitoring

```bash
# Current queue status
curl http://localhost:8000/api/v1/parse/queue/status
```

### Docker Management

```bash
# View running containers
docker ps

# View logs
docker logs ocr-service

# Stop services
docker-compose down
```

## 🔒 Production Considerations

### Security
- File validation and size limits
- Input sanitization
- Error handling and logging

### Performance
- Single-worker configuration for memory stability
- GPU memory management and cleanup
- Background job processing

### Scalability
- Redis-based job persistence
- Horizontal scaling support via multiple instances
- Load balancing ready

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r backend/requirements/requirements-gpu.txt

# Run development server
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

## 📈 Performance Metrics

- **Processing Time**: ~100 seconds per document (Qwen Vision)
- **Memory Usage**: ~7GB GPU memory baseline
- **Throughput**: Sequential processing with queue management
- **Uptime**: Enterprise-grade reliability with health monitoring

## 🆘 Support

### Common Issues

1. **CUDA Out of Memory**: Ensure 8GB+ GPU memory available
2. **Job Timeouts**: Check GPU resource allocation
3. **Queue Backlog**: Monitor worker health and GPU status

### Troubleshooting

```bash
# Check container logs
docker logs -f ocr-service

# Monitor GPU usage
nvidia-smi

# Redis connection test
docker exec redis redis-cli ping
```

---

**Built with FastAPI • Docker • CUDA • Redis**
