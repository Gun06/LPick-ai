#!/usr/bin/env python3
# data/scripts/download_cover_art_archive.py

import os
import time
import requests
import csv
import re
import logging

# 1) 폴더 구조 설정: data/raw 아래에 cover_art, csv, logs 분리
RAW_DIR   = os.path.join("data", "raw")
COVER_DIR = os.path.join(RAW_DIR, "cover_art")
CSV_DIR   = os.path.join(RAW_DIR, "csv")
LOG_DIR   = os.path.join(RAW_DIR, "logs")
for d in (COVER_DIR, CSV_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)

# 파일 경로 설정
LOG_PATH = os.path.join(LOG_DIR, "download_cover_art.log")
CSV_PATH = os.path.join(CSV_DIR, "cover_art.csv")

# 2) 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 3) 파일명 안전 처리
def sanitize_filename(name: str) -> str:
    """특수문자 제거 & 공백을 언더바 변환"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip().replace(" ", "_")

# 4) Identifier 리스트 조회
def fetch_identifiers(page: int = 1, rows: int = 50):
    params = {
        'q': 'collection:coverartarchive',
        'fl[]': 'identifier',
        'rows': rows,
        'page': page,
        'output': 'json'
    }
    resp = requests.get('https://archive.org/advancedsearch.php', params=params)
    resp.raise_for_status()
    return [d['identifier'] for d in resp.json()['response']['docs']]

# 5) Metadata 및 이미지 파일 리스트 추출
def fetch_metadata(identifier: str):
    """Metadata API로 제목과 이미지 파일 리스트(JPG, JPEG, PNG) 가져오기"""
    resp = requests.get(f'https://archive.org/metadata/{identifier}')
    resp.raise_for_status()
    data = resp.json()
    title = data.get('metadata', {}).get('title', identifier)
    files = [
        f['name'] for f in data.get('files', [])
        if f['name'].lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
    return title, files

# 6) 이미지 다운로드 및 CSV 기록
def download_and_log(identifier: str, filename: str, title: str, writer):
    safe = sanitize_filename(title)
    ext  = os.path.splitext(filename)[1]
    dest = os.path.join(COVER_DIR, f"{safe}{ext}")

    if os.path.exists(dest):
        logger.info(f"SKIP: {os.path.basename(dest)} (already exists)")
        return

    url = f'https://archive.org/download/{identifier}/{filename}'
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        logger.info(f"OK:   {os.path.basename(dest)}")
        writer.writerow([identifier, title, url, os.path.basename(dest)])
    else:
        logger.error(f"FAIL: {os.path.basename(dest)} → HTTP {r.status_code}")

# 7) 메인: PNG 파일 우선, 없으면 마지막 이미지 선택
def main(pages=3, rows=50):
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['identifier', 'title', 'url', 'saved_as'])

        for page in range(1, pages+1):
            ids = fetch_identifiers(page=page, rows=rows)
            logger.info(f"[Page {page}] Identifiers found: {len(ids)}")

            for ident in ids:
                title, files = fetch_metadata(ident)
                if not files:
                    logger.warning(f"SKIP: {ident} has no images")
                else:
                    # PNG 파일 우선 추출
                    pngs = [f for f in files if f.lower().endswith('.png')]
                    if pngs:
                        chosen = pngs[-1]
                    else:
                        chosen = files[-1]
                    logger.info(f"Selecting file for {ident}: {chosen}")
                    download_and_log(ident, chosen, title, writer)
                time.sleep(0.1)
            time.sleep(1)

if __name__ == '__main__':
    main(pages=3, rows=50)