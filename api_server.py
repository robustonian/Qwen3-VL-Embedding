import os
import sys
import logging
import traceback
import argparse
import base64
import re
from typing import List, Union, Dict, Any, Optional
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
import requests
from PIL import Image
from io import BytesIO
import uvicorn

sys.path.append(str(Path(__file__).parent))
from src.models.qwen3_vl_embedding import Qwen3VLEmbedder
from src.app.database.sqlite import sqlite_manager
from src.app.routers import documents_router, search_router, collections_router
from src.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "qwen3-vl-embedding"

class EmbeddingRequest(BaseModel):
    input: Union[str, List[Union[str, Dict[str, Any]]]]
    model: str = Field(default=MODEL_NAME)
    encoding_format: str = Field(default="float")
    dimensions: Optional[int] = Field(default=None)
    user: Optional[str] = Field(default=None)

    @validator('model')
    def validate_model(cls, v):
        if v != MODEL_NAME:
            raise ValueError(f"Model '{v}' not supported. Use '{MODEL_NAME}'")
        return v

class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int

class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 1699000000
    owned_by: str = "qwen"

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

class APIServer:
    def __init__(self, model_path: str):
        self.embedder = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.embedder = Qwen3VLEmbedder(
                model_name_or_path=self.model_path,
                max_length=8192,
                num_frames=16,
                fps=1
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _is_url(self, path: str) -> bool:
        return path.startswith(('http://', 'https://'))

    def _is_base64(self, data: str) -> bool:
        return data.startswith('data:image/') or self._is_raw_base64(data)

    def _is_raw_base64(self, data: str) -> bool:
        if len(data) < 100:
            return False
        base64_pattern = re.compile(r'^[A-Za-z0-9+/]+={0,2}$')
        return bool(base64_pattern.match(data[:100]))

    def _decode_base64_image(self, data: str) -> Image.Image:
        if data.startswith('data:image/'):
            header, encoded = data.split(',', 1)
        else:
            encoded = data
        image_bytes = base64.b64decode(encoded)
        return Image.open(BytesIO(image_bytes))

    def _is_absolute_path(self, path: str) -> bool:
        return os.path.isabs(path)

    def _process_image_path(self, image_path: str) -> Union[str, Image.Image]:
        try:
            if self._is_base64(image_path):
                return self._decode_base64_image(image_path)
            elif self._is_url(image_path):
                response = requests.get(image_path, timeout=10)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            elif self._is_absolute_path(image_path):
                if os.path.exists(image_path):
                    return Image.open(image_path)
                else:
                    raise FileNotFoundError(f"Absolute path not found: {image_path}")
            else:
                full_path = os.path.abspath(image_path)
                if os.path.exists(full_path):
                    return Image.open(full_path)
                else:
                    raise FileNotFoundError(f"Relative path not found: {image_path}")
        except Exception as e:
            logger.error(f"Failed to process image path '{image_path}': {e}")
            raise

    def _parse_input_item(self, item: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(item, str):
            if self._is_base64(item) or self._is_url(item) or os.path.exists(item) or os.path.exists(os.path.abspath(item)):
                try:
                    image = self._process_image_path(item)
                    return {"image": image}
                except:
                    return {"text": item}
            else:
                return {"text": item}
        
        elif isinstance(item, dict):
            result = {}
            
            if "text" in item:
                result["text"] = item["text"]
            
            if "image" in item:
                if isinstance(item["image"], str):
                    result["image"] = self._process_image_path(item["image"])
                else:
                    result["image"] = item["image"]
            
            if "instruction" in item:
                result["instruction"] = item["instruction"]
            
            if not result:
                raise ValueError("Invalid input format")
            
            return result
        
        else:
            raise ValueError(f"Unsupported input type: {type(item)}")

    def create_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        try:
            if isinstance(request.input, str):
                inputs = [request.input]
            elif isinstance(request.input, list):
                inputs = request.input
            else:
                raise ValueError("Invalid input format")

            parsed_inputs = []
            for item in inputs:
                parsed_inputs.append(self._parse_input_item(item))

            embeddings = self.embedder.process(parsed_inputs, normalize=True)
            
            embeddings_list = embeddings.cpu().tolist()
            
            data = []
            for i, embedding in enumerate(embeddings_list):
                data.append(EmbeddingData(
                    embedding=embedding,
                    index=i
                ))

            return EmbeddingResponse(
                data=data,
                model=request.model,
                usage={
                    "prompt_tokens": len(inputs),
                    "total_tokens": len(inputs)
                }
            )

        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    # Startup
    logger.info("Initializing database...")
    await sqlite_manager.initialize()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Qwen3-VL Embedding API",
    description="OpenAI-compatible API for Qwen3-VL embeddings with multimodal search",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(collections_router, prefix="/api")

# Serve uploaded files
app.mount("/files", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="files")

# Serve frontend (if exists)
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.responses import FileResponse

    # Serve static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # SPA fallback - serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't serve index.html for API or file routes
        if full_path.startswith(("api/", "v1/", "files/", "health")):
            raise HTTPException(status_code=404)

        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

# Initialize with default path, will be overridden in main
api_server = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": api_server is not None and api_server.embedder is not None}

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    return ModelsResponse(
        data=[ModelInfo(id=MODEL_NAME)]
    )

@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    if api_server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    return api_server.create_embeddings(request)

def parse_args():
    parser = argparse.ArgumentParser(description="Qwen3-VL Embedding API Server")
    parser.add_argument(
        "--model-path",
        type=str,
        default=os.environ.get("MODEL_PATH", "./models/Qwen3-VL-Embedding-2B"),
        help="Path to the model directory (default: ./models/Qwen3-VL-Embedding-2B)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("API_HOST", "0.0.0.0"),
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("API_PORT", "8000")),
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info(f"Starting API server on {args.host}:{args.port}")
    logger.info(f"Model path: {args.model_path}")
    logger.info(f"Log level: {args.log_level}")
    
    # Initialize API server with model path
    api_server = APIServer(args.model_path)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower()
    )
