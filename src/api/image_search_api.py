#!/usr/bin/env python3
"""
LP 앨범 이미지 검색 API

기능:
1. 이미지 업로드 검색 - 유사한 LP 앨범 찾기
2. 텍스트 검색 - 자연어로 LP 앨범 찾기 (CLIP)
3. 메타데이터 조회 - 앨범 상세 정보
4. 통계 API - 데이터베이스 현황
"""

import os
import sys
import time
import json
import base64
import requests
from pathlib import Path
from typing import List, Optional
from io import BytesIO

import numpy as np
import faiss
from PIL import Image

import torch
from transformers import CLIPProcessor, CLIPModel

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# FastAPI 앱 생성
app = FastAPI(
    title="LP Album Image Search API",
    description="LP 앨범 이미지 검색 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
faiss_index = None
metadata_mapping = None
clip_model = None
clip_processor = None
device = None

# 응답 모델
class SearchResult(BaseModel):
    """검색 결과 아이템"""
    rank: int
    image_id: int
    similarity: float
    distance: float
    genre: str
    filename: str
    image_path: str
    release_id: Optional[int] = None
    title: Optional[str] = None

class SearchResponse(BaseModel):
    """검색 응답"""
    success: bool
    query_time_ms: float
    total_results: int
    results: List[SearchResult]

class StatsResponse(BaseModel):
    """통계 응답"""
    total_images: int
    total_genres: int
    index_type: str
    embedding_dimension: int
    search_speed_ms: float

# 초기화 함수
def load_faiss_index():
    """FAISS 인덱스 로드"""
    global faiss_index
    
    index_path = Path('data/processed/faiss_index/index_flat_l2.faiss')
    if not index_path.exists():
        raise FileNotFoundError(f"FAISS 인덱스를 찾을 수 없습니다: {index_path}")
    
    faiss_index = faiss.read_index(str(index_path))
    print(f"✅ FAISS 인덱스 로드 완료: {faiss_index.ntotal:,}개 벡터")

def load_metadata():
    """메타데이터 로드"""
    global metadata_mapping
    
    metadata_path = Path('data/processed/faiss_index/id_to_metadata_mapping.json')
    if not metadata_path.exists():
        raise FileNotFoundError(f"메타데이터를 찾을 수 없습니다: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata_mapping = json.load(f)
    
    print(f"✅ 메타데이터 로드 완료: {len(metadata_mapping):,}개")

def load_clip_model():
    """CLIP 모델 로드"""
    global clip_model, clip_processor, device
    
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    
    print(f"🤖 CLIP 모델 로드 중... (device: {device})")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model.eval()
    
    print(f"✅ CLIP 모델 로드 완료")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    print("\n🚀 LP Album Image Search API 시작")
    print("=" * 70)
    
    try:
        load_faiss_index()
        load_metadata()
        load_clip_model()
        
        print("=" * 70)
        print("✅ 모든 리소스 로드 완료!")
        print("🌐 API 서버가 준비되었습니다.")
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        raise

# API 엔드포인트

@app.get("/", response_class=HTMLResponse)
async def root():
    """웹 UI 메인 페이지"""
    html_file = Path("templates/image_search.html")
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    return """
    <html>
        <body>
            <h1>LP Album Image Search API</h1>
            <p>API Documentation: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """

@app.get("/api")
async def api_info():
    """API 정보"""
    return {
        "service": "LP Album Image Search API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "web_ui": "GET /",
            "search_image": "POST /search/image",
            "search_image_url": "POST /search/image_url",
            "search_text": "POST /search/text",
            "get_metadata": "GET /metadata/{image_id}",
            "stats": "GET /stats"
        }
    }

@app.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=50, description="반환할 결과 개수")
):
    """
    이미지 업로드로 유사한 LP 앨범 검색
    
    Args:
        file: 업로드된 이미지 파일
        top_k: 반환할 결과 개수 (기본: 10, 최대: 50)
    
    Returns:
        검색 결과 및 메타데이터
    """
    start_time = time.time()
    
    try:
        # 이미지 읽기
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert('RGB')
        
        # CLIP 임베딩 생성
        inputs = clip_processor(images=image, return_tensors="pt").to(device)
        
        with torch.no_grad():
            image_features = clip_model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        query_vector = image_features.cpu().numpy().astype('float32')
        
        # FAISS 검색
        distances, indices = faiss_index.search(query_vector, top_k)
        
        # 결과 포맷팅
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            idx_str = str(idx)
            if idx_str in metadata_mapping:
                meta = metadata_mapping[idx_str]
                
                # 거리를 유사도로 변환 (0~1, 높을수록 유사)
                # L2 거리 → 유사도: similarity = 1 / (1 + distance)
                similarity = 1.0 / (1.0 + float(dist))
                
                results.append(SearchResult(
                    rank=rank,
                    image_id=int(idx),
                    similarity=round(similarity, 4),
                    distance=round(float(dist), 4),
                    genre=meta['genre'],
                    filename=meta['filename'],
                    image_path=meta['path'],
                    release_id=meta.get('release_id'),
                    title=meta.get('title')
                ))
        
        query_time = (time.time() - start_time) * 1000  # ms
        
        return SearchResponse(
            success=True,
            query_time_ms=round(query_time, 2),
            total_results=len(results),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

@app.post("/search/text")
async def search_by_text(
    query: str = Query(..., description="검색할 텍스트"),
    top_k: int = Query(10, ge=1, le=50, description="반환할 결과 개수")
):
    """
    텍스트로 LP 앨범 검색 (CLIP 멀티모달 검색)
    
    Args:
        query: 검색 텍스트 (예: "jazz album", "rock music cover")
        top_k: 반환할 결과 개수
    
    Returns:
        검색 결과 및 메타데이터
    """
    start_time = time.time()
    
    try:
        # CLIP 텍스트 임베딩 생성
        inputs = clip_processor(text=[query], return_tensors="pt", padding=True).to(device)
        
        with torch.no_grad():
            text_features = clip_model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        query_vector = text_features.cpu().numpy().astype('float32')
        
        # FAISS 검색
        distances, indices = faiss_index.search(query_vector, top_k)
        
        # 결과 포맷팅
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            idx_str = str(idx)
            if idx_str in metadata_mapping:
                meta = metadata_mapping[idx_str]
                similarity = 1.0 / (1.0 + float(dist))
                
                results.append(SearchResult(
                    rank=rank,
                    image_id=int(idx),
                    similarity=round(similarity, 4),
                    distance=round(float(dist), 4),
                    genre=meta['genre'],
                    filename=meta['filename'],
                    image_path=meta['path'],
                    release_id=meta.get('release_id'),
                    title=meta.get('title')
                ))
        
        query_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            success=True,
            query_time_ms=round(query_time, 2),
            total_results=len(results),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

@app.post("/search/image_url", response_model=SearchResponse)
async def search_by_image_url(
    image_url: str = Query(..., description="검색할 이미지 URL"),
    top_k: int = Query(10, ge=1, le=50, description="반환할 결과 개수")
):
    """
    이미지 URL로 유사한 LP 앨범 검색
    
    Args:
        image_url: 검색할 이미지의 URL
        top_k: 반환할 결과 개수 (기본: 10, 최대: 50)
    
    Returns:
        검색 결과 및 메타데이터
    """
    start_time = time.time()
    
    try:
        # URL에서 이미지 다운로드
        print(f"🔗 이미지 URL 다운로드 중: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # 이미지 로드
        image = Image.open(BytesIO(response.content)).convert('RGB')
        print(f"✅ 이미지 로드 완료: {image.size}")
        
        # CLIP 임베딩 생성
        inputs = clip_processor(images=image, return_tensors="pt").to(device)
        
        with torch.no_grad():
            image_features = clip_model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        query_vector = image_features.cpu().numpy().astype('float32')
        
        # FAISS 검색
        distances, indices = faiss_index.search(query_vector, top_k)
        
        # 결과 포맷팅
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            idx_str = str(idx)
            if idx_str in metadata_mapping:
                meta = metadata_mapping[idx_str]
                
                # 거리를 유사도로 변환 (0~1, 높을수록 유사)
                similarity = 1.0 / (1.0 + float(dist))
                
                results.append(SearchResult(
                    rank=rank,
                    image_id=int(idx),
                    similarity=round(similarity, 4),
                    distance=round(float(dist), 4),
                    genre=meta['genre'],
                    filename=meta['filename'],
                    image_path=meta['path'],
                    release_id=meta.get('release_id'),
                    title=meta.get('title')
                ))
        
        query_time = (time.time() - start_time) * 1000  # ms
        
        return SearchResponse(
            success=True,
            query_time_ms=round(query_time, 2),
            total_results=len(results),
            results=results
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"이미지 URL 다운로드 실패: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

@app.get("/metadata/{image_id}")
async def get_metadata(image_id: int):
    """
    이미지 ID로 메타데이터 조회
    
    Args:
        image_id: FAISS 인덱스 ID
    
    Returns:
        이미지 메타데이터
    """
    idx_str = str(image_id)
    
    if idx_str not in metadata_mapping:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
    
    return {
        "success": True,
        "image_id": image_id,
        "metadata": metadata_mapping[idx_str]
    }

@app.get("/image/{image_id}")
async def get_image(image_id: int):
    """
    이미지 ID로 실제 이미지 파일 반환
    
    Args:
        image_id: FAISS 인덱스 ID
    
    Returns:
        이미지 파일
    """
    idx_str = str(image_id)
    
    if idx_str not in metadata_mapping:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
    
    image_path = Path(metadata_mapping[idx_str]['path'])
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")
    
    return FileResponse(image_path)

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    데이터베이스 통계 정보
    
    Returns:
        전체 이미지 개수, 장르 수 등 통계
    """
    # 장르 통계
    genres = set(meta['genre'] for meta in metadata_mapping.values())
    
    return StatsResponse(
        total_images=faiss_index.ntotal,
        total_genres=len(genres),
        index_type="IndexFlatL2",
        embedding_dimension=512,
        search_speed_ms=4.53
    )

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "faiss_index_loaded": faiss_index is not None,
        "metadata_loaded": metadata_mapping is not None,
        "clip_model_loaded": clip_model is not None
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🎯 LP Album Image Search API 시작")
    print("=" * 70)
    print("📖 API 문서: http://localhost:8000/docs")
    print("🔍 검색 테스트: http://localhost:8000")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

