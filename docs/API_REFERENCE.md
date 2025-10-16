# 📡 LP 앨범 이미지 검색 API 레퍼런스

## 개요

LP 앨범 이미지 검색 API는 86,171개의 LP 앨범 이미지에서 유사한 이미지를 찾거나 텍스트로 검색할 수 있는 REST API입니다.

**기본 URL**: `http://localhost:8000`

**버전**: 1.0.0

---

## 목차

- [인증](#인증)
- [응답 형식](#응답-형식)
- [엔드포인트](#엔드포인트)
  - [GET /](#get-)
  - [GET /api](#get-api)
  - [GET /health](#get-health)
  - [GET /stats](#get-stats)
  - [POST /search/image](#post-searchimage)
  - [POST /search/text](#post-searchtext)
  - [GET /metadata/{image_id}](#get-metadataimage_id)
  - [GET /image/{image_id}](#get-imageimage_id)
- [오류 코드](#오류-코드)
- [사용 예시](#사용-예시)

---

## 인증

현재 버전은 인증이 필요하지 않습니다. 로컬 환경에서 사용할 수 있습니다.

---

## 응답 형식

모든 API 응답은 JSON 형식입니다.

### 성공 응답

```json
{
  "data": { ... },
  "status": "success"
}
```

### 오류 응답

```json
{
  "detail": "오류 메시지"
}
```

---

## 엔드포인트

### GET /

**설명**: 웹 UI를 반환합니다.

**응답**: HTML 페이지

**예시**:

```bash
curl http://localhost:8000/
```

---

### GET /api

**설명**: API 정보를 반환합니다.

**응답**:

```json
{
  "name": "LP Album Image Search API",
  "version": "1.0.0",
  "description": "Search through 86,171 LP album images using CLIP and FAISS",
  "endpoints": {
    "search_image": "/search/image",
    "search_text": "/search/text",
    "stats": "/stats",
    "health": "/health"
  }
}
```

**예시**:

```bash
curl http://localhost:8000/api
```

---

### GET /health

**설명**: 서버 상태를 확인합니다.

**응답**:

```json
{
  "status": "healthy",
  "faiss_index_loaded": true,
  "metadata_loaded": true,
  "clip_model_loaded": true
}
```

**상태 코드**:

- `200 OK`: 정상
- `503 Service Unavailable`: 서비스 이용 불가

**예시**:

```bash
curl http://localhost:8000/health
```

---

### GET /stats

**설명**: 시스템 통계를 반환합니다.

**응답**:

```json
{
  "total_images": 86171,
  "total_genres": 14,
  "index_type": "IndexFlatL2",
  "embedding_dimension": 512,
  "search_speed_ms": 4.53,
  "genres": [
    "Jazz",
    "Rock",
    "Classical",
    "Blues",
    "Electronic",
    "Pop",
    "Folk",
    "Stage&Screen",
    "Funk / Soul",
    "Latin",
    "Reggae",
    "Hip Hop",
    "Children's",
    "Non-Music"
  ]
}
```

**예시**:

```bash
curl http://localhost:8000/stats
```

---

### POST /search/image

**설명**: 이미지로 유사한 LP 앨범을 검색합니다.

**요청**:

**Content-Type**: `multipart/form-data`

**파라미터**:
| 이름 | 타입 | 필수 | 기본값 | 설명 |
| ------ | ------- | ---- | ------ | --------------------- |
| file | file | O | - | 검색할 이미지 파일 |
| top_k | integer | X | 10 | 반환할 결과 개수(1-100) |

**응답**:

```json
{
  "query_time_ms": 15.23,
  "total_results": 10,
  "results": [
    {
      "rank": 1,
      "image_id": 12345,
      "similarity": 0.9856,
      "genre": "Jazz",
      "filename": "Miles_Davis_Kind_Of_Blue.jpeg",
      "image_url": "/image/12345"
    },
    ...
  ]
}
```

**필드 설명**:

- `query_time_ms`: 검색 소요 시간 (밀리초)
- `total_results`: 반환된 결과 개수
- `results`: 검색 결과 배열
  - `rank`: 순위 (1부터 시작)
  - `image_id`: 이미지 고유 ID
  - `similarity`: 유사도 (0.0 ~ 1.0)
  - `genre`: 음악 장르
  - `filename`: 파일명
  - `image_url`: 이미지 조회 URL

**상태 코드**:

- `200 OK`: 성공
- `400 Bad Request`: 파일이 없거나 형식이 잘못됨
- `500 Internal Server Error`: 서버 오류

**예시**:

```bash
# cURL
curl -X POST http://localhost:8000/search/image \
  -F "file=@album.jpg" \
  -F "top_k=5"

# Python
import requests

with open('album.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/search/image',
        files={'file': f},
        params={'top_k': 5}
    )
    print(response.json())

# JavaScript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/search/image?top_k=5', {
    method: 'POST',
    body: formData
});
const data = await response.json();
```

---

### POST /search/text

**설명**: 텍스트로 LP 앨범을 검색합니다.

**요청**:

**파라미터**:
| 이름 | 타입 | 필수 | 기본값 | 설명 |
| ------ | ------- | ---- | ------ | --------------------- |
| query | string | O | - | 검색 쿼리 |
| top_k | integer | X | 10 | 반환할 결과 개수(1-100) |

**응답**:

```json
{
  "query": "jazz album",
  "query_time_ms": 12.45,
  "total_results": 10,
  "results": [
    {
      "rank": 1,
      "image_id": 23456,
      "similarity": 0.8234,
      "genre": "Jazz",
      "filename": "John_Coltrane_Blue_Train.jpeg",
      "image_url": "/image/23456"
    },
    ...
  ]
}
```

**상태 코드**:

- `200 OK`: 성공
- `400 Bad Request`: 쿼리가 비어있음
- `500 Internal Server Error`: 서버 오류

**예시**:

```bash
# cURL
curl -X POST "http://localhost:8000/search/text?query=jazz%20album&top_k=5"

# Python
import requests

response = requests.post(
    'http://localhost:8000/search/text',
    params={
        'query': 'jazz album',
        'top_k': 5
    }
)
print(response.json())

# JavaScript
const params = new URLSearchParams({
    query: 'jazz album',
    top_k: 5
});

const response = await fetch(`http://localhost:8000/search/text?${params}`, {
    method: 'POST'
});
const data = await response.json();
```

**검색 팁**:

- 영어로 입력하세요
- 구체적인 설명이 더 좋은 결과를 만듭니다
- 예시:
  - `"jazz album"` ✓
  - `"vintage rock music cover"` ✓
  - `"blue note records style"` ✓
  - `"abstract minimalist design"` ✓

---

### GET /metadata/{image_id}

**설명**: 이미지 메타데이터를 조회합니다.

**경로 파라미터**:
| 이름 | 타입 | 필수 | 설명 |
| --------- | ------- | ---- | -------------- |
| image_id | integer | O | 이미지 고유 ID |

**응답**:

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

**상태 코드**:

- `200 OK`: 성공
- `404 Not Found`: 이미지를 찾을 수 없음
- `500 Internal Server Error`: 서버 오류

**예시**:

```bash
# cURL
curl http://localhost:8000/metadata/12345

# Python
import requests

response = requests.get('http://localhost:8000/metadata/12345')
metadata = response.json()
print(f"장르: {metadata['metadata']['genre']}")

# JavaScript
const response = await fetch('http://localhost:8000/metadata/12345');
const data = await response.json();
```

---

### GET /image/{image_id}

**설명**: 이미지 파일을 반환합니다.

**경로 파라미터**:
| 이름 | 타입 | 필수 | 설명 |
| --------- | ------- | ---- | -------------- |
| image_id | integer | O | 이미지 고유 ID |

**응답**: JPEG 이미지 파일

**Content-Type**: `image/jpeg`

**상태 코드**:

- `200 OK`: 성공
- `404 Not Found`: 이미지를 찾을 수 없음
- `500 Internal Server Error`: 서버 오류

**예시**:

```bash
# cURL (다운로드)
curl http://localhost:8000/image/12345 -o album.jpg

# 브라우저에서 보기
http://localhost:8000/image/12345

# Python (Pillow로 로드)
import requests
from PIL import Image
from io import BytesIO

response = requests.get('http://localhost:8000/image/12345')
image = Image.open(BytesIO(response.content))
image.show()

# JavaScript (이미지 태그)
const img = document.createElement('img');
img.src = 'http://localhost:8000/image/12345';
document.body.appendChild(img);
```

---

## 오류 코드

| 상태 코드 | 설명                  | 원인                           |
| --------- | --------------------- | ------------------------------ |
| 200       | OK                    | 성공                           |
| 400       | Bad Request           | 잘못된 요청 (파라미터 오류)    |
| 404       | Not Found             | 리소스를 찾을 수 없음          |
| 500       | Internal Server Error | 서버 내부 오류                 |
| 503       | Service Unavailable   | 서비스 이용 불가 (모델 미로드) |

### 오류 응답 예시

```json
{
  "detail": "Image not found with id: 99999"
}
```

---

## 사용 예시

### 1. 완전한 검색 워크플로우

```python
import requests

# 1. 서버 상태 확인
health = requests.get('http://localhost:8000/health').json()
if health['status'] != 'healthy':
    print("서버가 준비되지 않았습니다")
    exit()

# 2. 통계 조회
stats = requests.get('http://localhost:8000/stats').json()
print(f"검색 가능한 이미지: {stats['total_images']}개")

# 3. 이미지로 검색
with open('my_album.jpg', 'rb') as f:
    search_result = requests.post(
        'http://localhost:8000/search/image',
        files={'file': f},
        params={'top_k': 5}
    ).json()

print(f"검색 시간: {search_result['query_time_ms']}ms")

# 4. 결과 처리
for result in search_result['results']:
    # 메타데이터 조회
    metadata = requests.get(
        f"http://localhost:8000/metadata/{result['image_id']}"
    ).json()

    print(f"#{result['rank']}: {metadata['metadata']['filename']}")
    print(f"  장르: {result['genre']}")
    print(f"  유사도: {result['similarity']:.2%}")
```

### 2. 텍스트 검색 및 이미지 다운로드

```python
import requests
from pathlib import Path

# 1. 텍스트로 검색
response = requests.post(
    'http://localhost:8000/search/text',
    params={'query': 'jazz album', 'top_k': 10}
)
results = response.json()['results']

# 2. Top-5 이미지 다운로드
output_dir = Path('downloaded_albums')
output_dir.mkdir(exist_ok=True)

for result in results[:5]:
    image_id = result['image_id']
    filename = result['filename']

    # 이미지 다운로드
    img_response = requests.get(f'http://localhost:8000/image/{image_id}')

    # 저장
    output_path = output_dir / filename
    with open(output_path, 'wb') as f:
        f.write(img_response.content)

    print(f"다운로드: {filename}")
```

### 3. 장르별 검색

```python
import requests

def search_by_genre(genre, limit=20):
    """특정 장르의 앨범 찾기"""
    # 장르 이름으로 텍스트 검색
    response = requests.post(
        'http://localhost:8000/search/text',
        params={'query': f'{genre} album', 'top_k': 50}
    )

    results = response.json()['results']

    # 정확히 일치하는 장르만 필터링
    genre_results = [r for r in results if r['genre'] == genre]

    return genre_results[:limit]

# 사용
jazz_albums = search_by_genre('Jazz', limit=10)
for album in jazz_albums:
    print(f"{album['filename']} - {album['similarity']:.2%}")
```

### 4. 배치 검색

```python
import requests
from pathlib import Path
import time

def batch_search(image_dir, output_file, top_k=5):
    """여러 이미지를 한 번에 검색"""
    results = []

    for img_path in Path(image_dir).glob('*.jpg'):
        print(f"검색 중: {img_path.name}")

        with open(img_path, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/search/image',
                files={'file': f},
                params={'top_k': top_k}
            )

        if response.status_code == 200:
            data = response.json()
            results.append({
                'query': img_path.name,
                'time_ms': data['query_time_ms'],
                'matches': data['results']
            })

        time.sleep(0.1)  # 서버 부하 방지

    # JSON 저장
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"결과 저장: {output_file}")
    return results

# 사용
results = batch_search('my_albums/', 'batch_results.json', top_k=5)
```

### 5. 비동기 검색 (빠른 처리)

```python
import asyncio
import aiohttp
from pathlib import Path

async def search_image_async(session, image_path, top_k=5):
    """비동기 이미지 검색"""
    with open(image_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=image_path.name)

        async with session.post(
            f'http://localhost:8000/search/image?top_k={top_k}',
            data=data
        ) as response:
            return await response.json()

async def batch_search_async(image_dir, top_k=5):
    """여러 이미지를 비동기로 검색"""
    image_paths = list(Path(image_dir).glob('*.jpg'))

    async with aiohttp.ClientSession() as session:
        tasks = [
            search_image_async(session, path, top_k)
            for path in image_paths
        ]
        results = await asyncio.gather(*tasks)

    return results

# 사용
results = asyncio.run(batch_search_async('my_albums/', top_k=5))
```

---

## 성능 최적화

### 1. Top-K 조정

검색 속도는 `top_k` 값에 거의 영향을 받지 않습니다 (FAISS의 효율성 덕분):

```python
# top_k=10이든 top_k=100이든 속도 차이가 거의 없음
response = requests.post(..., params={'top_k': 100})
```

### 2. 이미지 크기 최적화

업로드 전에 이미지 크기를 줄이면 네트워크 시간을 절약할 수 있습니다:

```python
from PIL import Image
from io import BytesIO

def resize_image(image_path, max_size=(800, 800)):
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer

# 사용
resized = resize_image('large_album.jpg')
response = requests.post(
    'http://localhost:8000/search/image',
    files={'file': ('album.jpg', resized, 'image/jpeg')}
)
```

### 3. 연결 재사용

`requests.Session`으로 연결을 재사용:

```python
import requests

session = requests.Session()

# 여러 요청에 같은 세션 사용
for image_path in image_paths:
    with open(image_path, 'rb') as f:
        response = session.post(
            'http://localhost:8000/search/image',
            files={'file': f}
        )
```

---

## 제한 사항

| 항목           | 제한                       |
| -------------- | -------------------------- |
| 최대 파일 크기 | 10MB (FastAPI 기본값)      |
| Top-K 범위     | 1-100                      |
| 동시 요청      | 제한 없음 (리소스 허용 시) |
| 지원 형식      | JPEG, PNG, GIF, BMP        |

---

## 변경 이력

### v1.0.0 (2024-10-16)

- 초기 릴리스
- 이미지 검색 기능
- 텍스트 검색 기능
- 86,171개 LP 앨범 데이터베이스
- CLIP + FAISS 기반 검색

---

## 지원 및 문의

- **API 문서**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (대체 문서)
- **GitHub Issues**: [프로젝트 저장소]

---

**작성일**: 2024-10-16  
**버전**: 1.0.0
