from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from backend.api.v1.router import api_router
from backend.core.config import settings
from backend.utils.logging.setup import logger
from backend.utils.homepage_config import HomepageConfig

# Conditionally import queues based on DEPLOYED_OCR setting
if settings.DEPLOYED_OCR == 'TrOCR':
    from backend.core.ocr_queue import ocr_queue
    forms_queue = None
elif settings.DEPLOYED_OCR == 'Qwen':
    from backend.core.forms_queue import forms_queue
    ocr_queue = None
else:
    # If both or different setting, import both (fallback)
    from backend.core.ocr_queue import ocr_queue
    from backend.core.forms_queue import forms_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop the queue workers"""
    # Startup
    if ocr_queue is not None:
        logger.info("Starting OCR queue worker...")
        await ocr_queue.start_worker()
    
    if forms_queue is not None:
        logger.info("Starting Forms queue worker...")
        await forms_queue.start_worker()
    
    yield
    
    # Shutdown
    if ocr_queue is not None:
        logger.info("Stopping OCR queue worker...")
        await ocr_queue.stop_worker()
    
    if forms_queue is not None:
        logger.info("Stopping Forms queue worker...")
        await forms_queue.stop_worker()


app = FastAPI(
    title=f"OCR API - {settings.DEPLOYED_OCR} Mode", 
    version=settings.VERSION, 
    description=f"API for {'Optical Character Recognition using TrOCR' if settings.DEPLOYED_OCR == 'TrOCR' else 'Form Parsing using Qwen Vision' if settings.DEPLOYED_OCR == 'Qwen' else 'OCR and Form Parsing'} with in-process queues",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS
)

app.include_router(api_router, prefix="/api")


def generate_endpoint_html(endpoints: list, color_map: dict) -> str:
    """Generate HTML for endpoint list."""
    html_parts = []
    for endpoint in endpoints:
        color = color_map.get(endpoint['color'], 'blue')
        html_parts.append(f'''
                    <div class="border-l-4 border-{color}-500 pl-4">
                        <div class="flex items-center justify-between">
                            <span class="text-sm font-mono bg-{color}-100 text-{color}-800 px-2 py-1 rounded">{endpoint['method']}</span>
                            <code class="text-sm text-gray-600">{endpoint['path']}</code>
                        </div>
                        <p class="text-sm text-gray-600 mt-1">{endpoint['description']}</p>
                    </div>''')
    return ''.join(html_parts)


def generate_features_html(features: list) -> str:
    """Generate HTML for features grid with enhanced glassmorphism design."""
    html_parts = []
    
    # Enhanced color schemes for different features
    color_schemes = [
        {
            'bg': 'bg-gradient-to-br from-blue-500/10 to-indigo-500/10',
            'icon_bg': 'bg-gradient-to-br from-blue-500 to-indigo-600',
            'icon_shadow': 'shadow-blue-500/25',
            'text_color': 'text-blue-600',
            'border': 'border-blue-200/30'
        },
        {
            'bg': 'bg-gradient-to-br from-purple-500/10 to-pink-500/10',
            'icon_bg': 'bg-gradient-to-br from-purple-500 to-pink-600',
            'icon_shadow': 'shadow-purple-500/25',
            'text_color': 'text-purple-600',
            'border': 'border-purple-200/30'
        },
        {
            'bg': 'bg-gradient-to-br from-emerald-500/10 to-teal-500/10',
            'icon_bg': 'bg-gradient-to-br from-emerald-500 to-teal-600',
            'icon_shadow': 'shadow-emerald-500/25',
            'text_color': 'text-emerald-600',
            'border': 'border-emerald-200/30'
        }
    ]
    
    for i, feature in enumerate(features):
        color_scheme = color_schemes[i % len(color_schemes)]
        html_parts.append(f'''
            <div class="glass-card feature-card rounded-3xl p-8 hover:bg-white/20 transition-all duration-500 transform hover:-translate-y-2 hover:shadow-2xl group {color_scheme['bg']} {color_scheme['border']} backdrop-blur-xl">
                <div class="flex items-center mb-6">
                    <div class="{color_scheme['icon_bg']} text-white p-4 rounded-2xl shadow-xl {color_scheme['icon_shadow']} group-hover:shadow-2xl transition-all duration-300 group-hover:scale-110 relative">
                        <i class="{feature['icon']} text-2xl"></i>
                        <div class="absolute inset-0 bg-white/20 rounded-2xl animate-pulse-glow"></div>
                    </div>
                </div>
                <h3 class="text-2xl font-bold text-gray-900 mb-4 group-hover:{color_scheme['text_color']} transition-colors duration-300">{feature['name']}</h3>
                <p class="text-gray-600 leading-relaxed group-hover:text-gray-700 transition-colors duration-300">{feature['desc']}</p>
                
                <!-- Decorative element -->
                <div class="absolute top-4 right-4 w-2 h-2 {color_scheme['icon_bg']} rounded-full opacity-60 group-hover:opacity-100 transition-opacity duration-300"></div>
            </div>''')
    return ''.join(html_parts)


@app.get("/", tags=["Health Check"], response_class=HTMLResponse)
async def root(mode: Optional[str] = Query(None, description="Documentation mode: 'TrOCR' or 'Qwen'")):
    """Homepage showing project information and API endpoints"""
    
    # Debug logging
    logger.info(f"Homepage accessed with mode: {mode}, DEPLOYED_OCR: {settings.DEPLOYED_OCR}")
    
    template_path = Path(__file__).parent / "templates" / "homepage.html"
    
    # Get service configuration (with optional mode override)
    config = HomepageConfig.get_service_config(mode)
    base_endpoints = HomepageConfig.get_base_endpoints()
    
    # Debug the config mode
    logger.info(f"Service config mode: {config.get('service_mode')}, mode param: {mode}")
    
    # Enhanced color mapping for modern UI
    color_map = {
        'slate': 'slate', 'emerald': 'emerald', 'amber': 'amber', 
        'violet': 'violet', 'cyan': 'cyan', 'rose': 'rose',
        'blue': 'blue', 'green': 'green', 'orange': 'orange', 
        'purple': 'purple', 'indigo': 'indigo', 'red': 'red'
    }
    
    # Generate HTML components
    features_html = generate_features_html(config['features'])
    base_endpoints_html = generate_endpoint_html(base_endpoints, color_map)
    service_endpoints_html = generate_endpoint_html(config['service_endpoints'], color_map)
    
    # Read and format template
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content.format(
            service_name=config['service_name'],
            service_description=config['service_description'],
            service_tagline=config['service_tagline'],
            service_icon=config['service_icon'],
            service_mode=config['service_mode'],
            primary_color=config['primary_color'],
            accent_color=config['accent_color'],
            version=settings.VERSION,
            deployed_service=settings.DEPLOYED_OCR,
            current_mode=config['service_mode'],  # Use the actual mode from config instead of fallback
            features_html=features_html,
            base_endpoints_html=base_endpoints_html,
            service_endpoints_html=service_endpoints_html,
            curl_example=config['curl_example'],
            python_example=config['python_example']
        ))
        
    except FileNotFoundError:
        logger.warning("Homepage template not found, falling back to JSON response")
        return {"message": "OCR API is running", "deployed_service": settings.DEPLOYED_OCR, "version": settings.VERSION}
