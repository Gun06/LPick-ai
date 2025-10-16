#!/usr/bin/env python3
"""
웹 기반 LP 이미지 레이블링 도구
브라우저에서 이미지를 보면서 레이블링할 수 있는 웹 인터페이스
"""

import os
import json
import shutil
from pathlib import Path
import random
from PIL import Image
import argparse
from flask import Flask, render_template, request, jsonify, send_file
import base64
from io import BytesIO

app = Flask(__name__)

# 전역 변수
data_dir = None
output_dir = None
image_files = []
current_index = 0
labeled_data = {}
labeled_count = 0
progress_file = None

def load_progress():
    """진행상황 로드"""
    global labeled_data, labeled_count
    
    if progress_file and progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            labeled_data = data.get('labeled_data', {})
            labeled_count = data.get('labeled_count', 0)

def save_progress():
    """진행상황 저장"""
    global labeled_data, labeled_count
    
    progress_data = {
        'labeled_data': labeled_data,
        'labeled_count': labeled_count,
        'total_images': len(image_files)
    }
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def get_unlabeled_files():
    """아직 레이블링되지 않은 이미지 목록 반환"""
    return [f for f in image_files if str(f) not in labeled_data]

def image_to_base64(image_path):
    """이미지를 base64로 변환"""
    try:
        with Image.open(image_path) as img:
            # 이미지 크기 조정 (최대 800x600)
            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            # RGB로 변환 (RGBA인 경우)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # base64로 인코딩
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"이미지 변환 오류: {e}")
        return None

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('labeling.html')

@app.route('/api/current_image')
def get_current_image():
    """현재 이미지 정보 반환"""
    global current_index
    
    unlabeled_files = get_unlabeled_files()
    
    if not unlabeled_files or current_index >= len(unlabeled_files):
        return jsonify({
            'success': False,
            'message': '더 이상 레이블링할 이미지가 없습니다.',
            'finished': True
        })
    
    image_path = unlabeled_files[current_index]
    
    # 이미지 정보
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            image_info = {
                'width': width,
                'height': height,
                'mode': img.mode
            }
    except Exception as e:
        image_info = {'error': str(e)}
    
    # base64 이미지
    image_base64 = image_to_base64(image_path)
    
    return jsonify({
        'success': True,
        'image_path': str(image_path),
        'image_name': image_path.name,
        'image_info': image_info,
        'image_base64': image_base64,
        'current_index': current_index + 1,
        'total_unlabeled': len(unlabeled_files),
        'total_labeled': labeled_count
    })

@app.route('/api/label_image', methods=['POST'])
def label_image():
    """이미지 레이블링"""
    global current_index, labeled_count
    
    data = request.json
    label = data.get('label')
    
    if not label:
        return jsonify({'success': False, 'message': '레이블이 필요합니다.'})
    
    unlabeled_files = get_unlabeled_files()
    
    if not unlabeled_files or current_index >= len(unlabeled_files):
        return jsonify({'success': False, 'message': '유효하지 않은 이미지입니다.'})
    
    image_path = unlabeled_files[current_index]
    
    # 레이블링
    labeled_count += 1
    labeled_data[str(image_path)] = label
    
    # 이미지 복사
    dest_file = output_dir / label / f"{labeled_count:06d}_{image_path.name}"
    shutil.copy2(image_path, dest_file)
    
    # 진행상황 저장
    save_progress()
    
    # 다음 이미지로 이동
    current_index += 1
    
    return jsonify({
        'success': True,
        'message': f'레이블링 완료: {image_path.name} → {label}',
        'labeled_count': labeled_count
    })

@app.route('/api/skip_image', methods=['POST'])
def skip_image():
    """이미지 건너뛰기"""
    global current_index
    
    unlabeled_files = get_unlabeled_files()
    
    if not unlabeled_files or current_index >= len(unlabeled_files):
        return jsonify({'success': False, 'message': '유효하지 않은 이미지입니다.'})
    
    image_path = unlabeled_files[current_index]
    labeled_data[str(image_path)] = 'skipped'
    
    # 진행상황 저장
    save_progress()
    
    # 다음 이미지로 이동
    current_index += 1
    
    return jsonify({
        'success': True,
        'message': f'건너뛰기: {image_path.name}'
    })

@app.route('/api/previous_image', methods=['POST'])
def previous_image():
    """이전 이미지로 이동"""
    global current_index
    
    if current_index > 0:
        current_index -= 1
        return jsonify({'success': True, 'message': '이전 이미지로 이동했습니다.'})
    else:
        return jsonify({'success': False, 'message': '첫 번째 이미지입니다.'})

@app.route('/api/stats')
def get_stats():
    """통계 정보 반환"""
    unlabeled_files = get_unlabeled_files()
    
    # 레이블별 통계
    label_stats = {}
    for label in ['front', 'back', 'inner', 'disk']:
        label_stats[label] = sum(1 for v in labeled_data.values() if v == label)
    
    return jsonify({
        'total_images': len(image_files),
        'labeled_images': labeled_count,
        'unlabeled_images': len(unlabeled_files),
        'skipped_images': sum(1 for v in labeled_data.values() if v == 'skipped'),
        'label_stats': label_stats
    })

def main():
    """메인 함수"""
    global data_dir, output_dir, image_files, progress_file
    
    parser = argparse.ArgumentParser(description='웹 기반 LP 이미지 레이블링 도구')
    parser.add_argument('--data_dir', default='data/raw/discogs', help='원본 이미지 디렉토리')
    parser.add_argument('--output_dir', default='data/processed/labeled', help='레이블링된 이미지 출력 디렉토리')
    parser.add_argument('--port', type=int, default=5000, help='웹 서버 포트')
    parser.add_argument('--host', default='127.0.0.1', help='웹 서버 호스트')
    
    args = parser.parse_args()
    
    # 디렉토리 설정
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    if not data_dir.exists():
        print(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
        return
    
    # 출력 디렉토리 생성
    labels = ['front', 'back', 'inner', 'disk']
    output_dir.mkdir(parents=True, exist_ok=True)
    for label in labels:
        (output_dir / label).mkdir(exist_ok=True)
    
    # 이미지 파일 목록 생성
    image_files = []
    for genre_dir in data_dir.iterdir():
        if genre_dir.is_dir():
            for img_file in genre_dir.glob('*.jpeg'):
                image_files.append(img_file)
    
    # 진행상황 파일
    progress_file = output_dir / "labeling_progress.json"
    
    # 진행상황 로드
    load_progress()
    
    print(f"🎵 웹 기반 LP 이미지 레이블링 도구를 시작합니다!")
    print(f"📁 데이터 디렉토리: {data_dir}")
    print(f"📁 출력 디렉토리: {output_dir}")
    print(f"📊 총 이미지: {len(image_files)}개")
    print(f"📊 이미 레이블링된 이미지: {labeled_count}개")
    print(f"🌐 웹 인터페이스: http://{args.host}:{args.port}")
    print("=" * 60)
    
    # 웹 서버 시작
    app.run(host=args.host, port=args.port, debug=True)

if __name__ == "__main__":
    main()
