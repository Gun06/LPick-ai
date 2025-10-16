# 📘 LP 앨범 이미지 검색 시스템 사용자 가이드

## 목차

- [시작하기](#시작하기)
- [웹 UI 사용법](#웹-ui-사용법)
- [API 사용법](#api-사용법)
- [고급 기능](#고급-기능)
- [문제 해결](#문제-해결)

---

## 시작하기

### 1. 시스템 요구사항

**최소 요구사항:**

- Python 3.8 이상
- 8GB RAM
- 10GB 디스크 공간

**권장 요구사항:**

- Python 3.10 이상
- 16GB RAM
- 20GB 디스크 공간
- GPU (선택사항, CPU만으로도 충분)

### 2. 설치

#### 2.1 저장소 클론

```bash
git clone <repository-url>
cd lpick-ai
```

#### 2.2 가상환경 생성

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```cmd
python -m venv venv
venv\Scripts\activate
```

#### 2.3 의존성 설치

```bash
pip install -r requirements.txt
```

**설치되는 주요 패키지:**

- `torch` - PyTorch 딥러닝 프레임워크
- `transformers` - CLIP 모델
- `faiss-cpu` - 벡터 검색 엔진
- `fastapi` - 웹 API 프레임워크
- `uvicorn` - ASGI 서버
- `pillow` - 이미지 처리

### 3. 서버 시작

```bash
python3 scripts/run_search_api.py
```

**출력 예시:**

```
🚀 LP 앨범 이미지 검색 API 시작
======================================================================
🌐 서버 주소: http://localhost:8000
📖 API 문서: http://localhost:8000/docs
🔍 테스트: http://localhost:8000
======================================================================

INFO:     Application startup complete.
✅ 모든 리소스 로드 완료!
🌐 API 서버가 준비되었습니다.
```

### 4. 브라우저 접속

http://localhost:8000 으로 접속하면 웹 UI가 표시됩니다.

---

## 웹 UI 사용법

### 메인 화면

웹 UI는 크게 3가지 영역으로 구성됩니다:

```
┌─────────────────────────────────────┐
│   🎵 LP 앨범 이미지 검색            │
│   86,171개의 LP 앨범에서 찾아보세요 │
├─────────────────────────────────────┤
│  [86,171개] [14 장르] [4.53ms]      │  ← 통계 바
├─────────────────────────────────────┤
│  [🖼️ 이미지 검색] [💬 텍스트 검색]  │  ← 탭
│                                     │
│  드래그 앤 드롭 영역                │  ← 입력 영역
│                                     │
├─────────────────────────────────────┤
│  검색 결과 (그리드)                 │  ← 결과 영역
└─────────────────────────────────────┘
```

### 1. 이미지로 검색하기

#### 방법 1: 드래그 앤 드롭

1. LP 앨범 이미지 파일을 준비합니다
2. 파일을 "드래그 앤 드롭 영역"으로 끌어다 놓습니다
3. 이미지 미리보기가 표시됩니다
4. "유사한 이미지 검색" 버튼을 클릭합니다

#### 방법 2: 파일 선택

1. "드래그 앤 드롭 영역"을 클릭합니다
2. 파일 선택 대화상자에서 이미지를 선택합니다
3. "유사한 이미지 검색" 버튼을 클릭합니다

**지원 형식:**

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)

#### 결과 보기

- **순위**: #1, #2, ... #20 (유사도 순)
- **유사도**: 0-100% 퍼센트로 표시
- **장르**: Jazz, Rock, Classical 등
- **파일명**: 앨범 식별자

**결과 카드 클릭**:

- 클릭 시 원본 이미지가 새 탭에서 열립니다

### 2. 텍스트로 검색하기

#### 사용법

1. "텍스트 검색" 탭을 클릭합니다
2. 검색어를 입력합니다
3. 엔터키를 누르거나 "검색" 버튼을 클릭합니다

#### 검색어 예시

**장르 검색:**

```
jazz album
rock music
classical piano
blues guitar
electronic music
```

**스타일 검색:**

```
vintage album cover
modern design
abstract art
black and white photo
```

**분위기 검색:**

```
dark moody album
bright colorful cover
minimalist design
```

**팁:**

- 영어로 입력하세요 (CLIP 모델이 영어에 최적화됨)
- 구체적일수록 좋은 결과를 얻습니다
- 여러 단어 조합 가능

### 3. 통계 대시보드

화면 상단에 실시간 통계가 표시됩니다:

- **총 이미지 수**: 86,171개
- **장르 수**: 14개
- **검색 속도**: 4.53ms (평균)

---

## API 사용법

### API 문서 접속

http://localhost:8000/docs 에서 대화형 API 문서를 확인할 수 있습니다.

### 1. 헬스 체크

서버가 정상 작동하는지 확인합니다.

```bash
curl http://localhost:8000/health
```

**응답:**

```json
{
  "status": "healthy",
  "faiss_index_loaded": true,
  "metadata_loaded": true,
  "clip_model_loaded": true
}
```

### 2. 시스템 통계

```bash
curl http://localhost:8000/stats
```

**응답:**

```json
{
  "total_images": 86171,
  "total_genres": 14,
  "index_type": "IndexFlatL2",
  "embedding_dimension": 512,
  "search_speed_ms": 4.53,
  "genres": ["Jazz", "Rock", "Classical", ...]
}
```

### 3. 이미지 검색

#### cURL

```bash
curl -X POST http://localhost:8000/search/image \
  -F "file=@/path/to/album.jpg" \
  -F "top_k=10"
```

#### Python

```python
import requests

# 파일 업로드
with open('album.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/search/image',
        files={'file': f},
        params={'top_k': 10}
    )

data = response.json()
print(f"검색 시간: {data['query_time_ms']}ms")
print(f"결과 수: {data['total_results']}개")

for result in data['results']:
    print(f"#{result['rank']}: {result['genre']} - {result['similarity']:.2%}")
```

#### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch("http://localhost:8000/search/image?top_k=10", {
  method: "POST",
  body: formData,
});

const data = await response.json();
console.log("결과:", data.results);
```

**응답 형식:**

```json
{
  "query_time_ms": 15.23,
  "total_results": 10,
  "results": [
    {
      "rank": 1,
      "image_id": 12345,
      "similarity": 0.98,
      "genre": "Jazz",
      "filename": "Miles_Davis_Kind_Of_Blue.jpeg",
      "image_url": "/image/12345"
    },
    ...
  ]
}
```

### 4. 텍스트 검색

#### cURL

```bash
curl -X POST "http://localhost:8000/search/text?query=jazz%20album&top_k=10"
```

#### Python

```python
import requests

response = requests.post(
    'http://localhost:8000/search/text',
    params={
        'query': 'jazz album',
        'top_k': 10
    }
)

data = response.json()
for result in data['results']:
    print(f"{result['rank']}. {result['genre']} - {result['filename']}")
```

#### JavaScript

```javascript
const params = new URLSearchParams({
  query: "jazz album",
  top_k: 10,
});

const response = await fetch(`http://localhost:8000/search/text?${params}`);
const data = await response.json();
```

### 5. 메타데이터 조회

```bash
curl http://localhost:8000/metadata/12345
```

**응답:**

```json
{
  "image_id": 12345,
  "metadata": {
    "genre": "Jazz",
    "filename": "Miles_Davis_Kind_Of_Blue.jpeg",
    "path": "data/raw/discogs/Jazz/Miles_Davis_Kind_Of_Blue.jpeg"
  }
}
```

### 6. 이미지 파일 조회

```bash
# 이미지 파일 다운로드
curl http://localhost:8000/image/12345 -o album.jpg

# 브라우저에서 직접 보기
# http://localhost:8000/image/12345
```

---

## 고급 기능

### 1. 배치 검색

여러 이미지를 한 번에 검색하는 Python 스크립트:

```python
import requests
import os
from pathlib import Path

def batch_search(image_dir, top_k=5):
    """폴더 내 모든 이미지 검색"""
    results = []

    for img_path in Path(image_dir).glob('*.jpg'):
        with open(img_path, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/search/image',
                files={'file': f},
                params={'top_k': top_k}
            )

            if response.status_code == 200:
                data = response.json()
                results.append({
                    'query_image': img_path.name,
                    'matches': data['results']
                })

    return results

# 사용
results = batch_search('my_albums/', top_k=5)
for result in results:
    print(f"\n쿼리: {result['query_image']}")
    for match in result['matches']:
        print(f"  - {match['genre']}: {match['similarity']:.2%}")
```

### 2. 유사 앨범 찾기

특정 앨범과 유사한 앨범들을 찾는 함수:

```python
def find_similar_albums(image_id, top_k=10):
    """이미지 ID로 유사 앨범 찾기"""
    # 1. 메타데이터 조회
    meta_response = requests.get(
        f'http://localhost:8000/metadata/{image_id}'
    )
    metadata = meta_response.json()
    image_path = metadata['metadata']['path']

    # 2. 이미지로 검색
    with open(image_path, 'rb') as f:
        search_response = requests.post(
            'http://localhost:8000/search/image',
            files={'file': f},
            params={'top_k': top_k + 1}  # 자기 자신 제외
        )

    results = search_response.json()['results']
    return results[1:]  # 첫 번째 결과(자기 자신) 제외

# 사용
similar = find_similar_albums(12345, top_k=5)
```

### 3. 장르별 검색

특정 장르 내에서만 검색:

```python
def search_within_genre(query_image, target_genre, top_k=20):
    """특정 장르 내에서만 검색"""
    # 1. 일반 검색 (많은 결과 요청)
    with open(query_image, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/search/image',
            files={'file': f},
            params={'top_k': 100}  # 많이 가져오기
        )

    # 2. 장르 필터링
    all_results = response.json()['results']
    genre_results = [
        r for r in all_results
        if r['genre'] == target_genre
    ]

    return genre_results[:top_k]

# 사용
jazz_albums = search_within_genre('my_album.jpg', 'Jazz', top_k=10)
```

### 4. 검색 결과 저장

```python
import json

def save_search_results(query_image, output_file):
    """검색 결과를 JSON 파일로 저장"""
    with open(query_image, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/search/image',
            files={'file': f},
            params={'top_k': 20}
        )

    data = response.json()

    # JSON 저장
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"결과 저장: {output_file}")

# 사용
save_search_results('album.jpg', 'search_results.json')
```

---

## 문제 해결

### 서버가 시작되지 않음

**증상:**

```
ModuleNotFoundError: No module named 'fastapi'
```

**해결:**

```bash
# 가상환경이 활성화되어 있는지 확인
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 의존성 재설치
pip install -r requirements.txt
```

---

**증상:**

```
OSError: [Errno 48] Address already in use
```

**해결:**

```bash
# 포트 8000을 사용 중인 프로세스 종료
lsof -ti:8000 | xargs kill -9

# 또는 다른 포트 사용
uvicorn src.api.image_search_api:app --host 0.0.0.0 --port 8001
```

### 검색이 느림

**원인:**

- CPU가 느린 경우
- 메모리 부족

**해결:**

1. **GPU 사용 (가능한 경우):**

```python
# src/api/image_search_api.py 수정
device = "cuda" if torch.cuda.is_available() else "cpu"
```

2. **Top-K 줄이기:**

```python
# 검색할 결과 수를 줄임
response = requests.post(..., params={'top_k': 5})
```

3. **메모리 최적화:**

```bash
# FAISS 인덱스를 메모리에 유지
# (현재는 이미 메모리에 로드됨)
```

### 검색 결과가 이상함

**원인:**

- 업로드한 이미지가 LP 앨범이 아님
- 이미지 품질이 낮음

**해결:**

1. **이미지 품질 확인:**

   - 최소 200x200 픽셀 권장
   - JPEG 또는 PNG 형식
   - 선명한 이미지

2. **텍스트 검색 사용:**
   - 더 구체적인 설명 사용
   - 영어로 검색

### 웹 UI가 표시되지 않음

**증상:**
브라우저에서 "연결할 수 없음" 오류

**해결:**

1. **서버 실행 확인:**

```bash
curl http://localhost:8000/health
```

2. **방화벽 확인:**

- 포트 8000이 열려있는지 확인

3. **브라우저 캐시 삭제:**

- Ctrl+Shift+R (강력 새로고침)

### 메모리 부족 오류

**증상:**

```
RuntimeError: [enforce fail at alloc_cpu.cpp:64] DefaultCPUAllocator: can't allocate memory
```

**해결:**

1. **다른 프로그램 종료**

2. **배치 크기 줄이기:**

```python
# scripts/generate_embeddings.py 수정
batch_size = 16  # 32에서 줄임
```

3. **시스템 메모리 확인:**

```bash
# macOS/Linux
free -h

# Windows
wmic OS get FreePhysicalMemory
```

---

## 성능 튜닝

### 1. GPU 사용

GPU가 있다면 성능을 크게 향상시킬 수 있습니다:

```python
# src/api/image_search_api.py
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
```

**성능 향상:**

- 임베딩 생성: 5-10배 빠름
- 검색 응답: 50% 단축

### 2. 배치 처리

여러 이미지를 한 번에 처리:

```python
# 배치로 임베딩 생성
images = [load_image(path) for path in image_paths]
inputs = processor(images=images, return_tensors="pt")
embeddings = model.get_image_features(**inputs)
```

### 3. 캐싱

자주 검색되는 쿼리를 캐싱:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def search_text_cached(query: str, top_k: int):
    return search_text(query, top_k)
```

---

## 추가 리소스

- **API 문서**: http://localhost:8000/docs
- **프로젝트 README**: [README.md](../README.md)
- **CLIP 모델 문서**: https://github.com/openai/CLIP
- **FAISS 문서**: https://github.com/facebookresearch/faiss

---

**마지막 업데이트**: 2024-10-16  
**버전**: 1.0.0
