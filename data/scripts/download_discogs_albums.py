#!/usr/bin/env python3
# data/scripts/download_discogs_albums.py

import os
import argparse
import time
import logging
import csv
import re
from dotenv import load_dotenv
import requests

# 1) .env 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '..', '..', '.env')
load_dotenv(ENV_PATH)

# 2) 기본 폴더 구조 정의 (장르별 분리할 상위 경로)
RAW_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'raw')
CSV_DIR = os.path.join(RAW_DIR, 'csv')
LOG_DIR = os.path.join(RAW_DIR, 'logs')
for d in (RAW_DIR, CSV_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)

# 3) 환경변수 로드
KEY    = os.getenv('DISCOGS_CONSUMER_KEY')
SECRET = os.getenv('DISCOGS_CONSUMER_SECRET')
UA     = 'LpickAI/0.1'

# 4) 유틸: 안전한 파일명 생성

def sanitize_title(title: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', '', title)
    return safe.strip().replace(' ', '_') or 'untitled'

# 5) 이미지 다운로드 함수

def download_image(url: str, dest: str):
    headers = {'User-Agent': UA, 'Referer': 'https://www.discogs.com/'}
    r = requests.get(url, headers=headers, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

# 6) 메인 실행부
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Discogs 장르 기반 커버 아트 다운로드")
    parser.add_argument('--genre', required=True,
                        help="검색할 장르 이름 (예: Rock)")
    parser.add_argument('--max-images', type=int, default=0,
                        help="다운로드할 최대 이미지 개수 (0=무제한)")
    parser.add_argument('--max-pages', type=int, default=0,
                        help="검색할 최대 페이지 수 (0=무제한)")
    parser.add_argument('--dest', default=None,
                        help="이미지 저장 폴더 (기본: data/raw/discogs/<genre>)")
    args = parser.parse_args()

    # 장르별 폴더 경로 설정
    genre = args.genre.strip().replace(' ', '_')
    image_dir = args.dest or os.path.join(RAW_DIR, 'discogs', genre)
    os.makedirs(image_dir, exist_ok=True)

    csv_path = os.path.join(CSV_DIR, f'discogs_{genre}.csv')
    log_path = os.path.join(LOG_DIR, f'download_{genre}.log')

    # 7) 로깅 설정 (장르별 파일)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to {log_path}")
    logger.info(f"CSV: {csv_path}")
    logger.info(f"Images: {image_dir}")

    # 8) CSV append 설정
    header_needed = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    mode = 'a' if os.path.exists(csv_path) else 'w'
    with open(csv_path, mode, newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        if header_needed:
            csv_writer.writerow([
                'genre', 'artists', 'title', 'release_id', 'released',
                'year', 'country', 'genres', 'styles', 'image_url', 'image_file'
            ])

        seen_urls = set()
        total_images = 0
        counters = {}
        page = 1

        # 9) 페이징 순회
        while True:
            params = {
                'genre':    genre,
                'type':     'release',
                'per_page': 100,
                'page':     page,
                'key':      KEY,
                'secret':   SECRET
            }
            logger.info(f"Searching genre '{genre}' page {page}")
            resp = requests.get('https://api.discogs.com/database/search',
                                 params=params,
                                 headers={'User-Agent': UA})
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results', [])
            if not results:
                logger.info("No more results, exiting pages loop.")
                break

            for result in results:
                rid = result.get('id')
                # 릴리즈 상세 조회 시 404 예외 처리
                try:
                    rel_resp = requests.get(f'https://api.discogs.com/releases/{rid}',
                                             headers={'User-Agent': UA})
                    rel_resp.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if rel_resp.status_code == 404:
                        logger.warning(f"Release ID {rid} not found (404), skipping.")
                        continue
                    else:
                        logger.error(f"Error fetching release {rid}: {e}")
                        continue

                rel = rel_resp.json()

                title = rel.get('title', '')
                released = rel.get('released', '')
                year = rel.get('year', '')
                country = rel.get('country', '')
                artists = ';'.join([a.get('name', '') for a in rel.get('artists', [])])
                genres = ';'.join(rel.get('genres', []))
                styles = ';'.join(rel.get('styles', []))
                images = rel.get('images', [])

                base_name = sanitize_title(title or str(rid))
                # 릴리즈별 카운터 초기화
                if base_name not in counters:
                    counters[base_name] = 0

                for img in images:
                    url = img.get('uri')
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    total_images += 1
                    if args.max_images and total_images > args.max_images:
                        logger.info(f"Reached max_images={args.max_images}, stopping.")
                        raise SystemExit

                    # 릴리즈별 인덱스
                    counters[base_name] += 1
                    idx = counters[base_name]

                    ext = os.path.splitext(url)[1]
                    fname = f"{base_name}_{idx:04d}{ext}"
                    out = os.path.join(image_dir, fname)
                    try:
                        download_image(url, out)
                        logger.info(f"Downloaded image: {fname}")
                    except Exception as e:
                        logger.error(f"Error downloading {url}: {e}")
                        continue

                    csv_writer.writerow([
                        genre, artists, title, rid, released,
                        year, country, genres, styles, url, fname
                    ])
                    csvfile.flush()
                    time.sleep(1)

            # 페이지 루프 제어
            total_pages = data.get('pagination', {}).get('pages', 0)
            if args.max_pages and page >= args.max_pages:
                logger.info(f"Reached max_pages={args.max_pages}, stopping pages.")
                break
            if page >= total_pages:
                logger.info("Final page reached, exiting pages loop.")
                break
            page += 1
            time.sleep(1)

    logger.info("All tasks completed.")
