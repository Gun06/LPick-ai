#!/usr/bin/env python3
"""
바운딩 박스 라벨링을 위한 웹 서버
labelImg 스타일의 웹 기반 바운딩 박스 라벨링 도구
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
annotations = {}
progress_file = None

def load_progress():
    """진행상황 로드"""
    global annotations
    
    if progress_file and progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            annotations = data.get('annotations', {})

def save_progress():
    """진행상황 저장"""
    global annotations
    
    progress_data = {
        'annotations': annotations,
        'total_images': len(image_files)
    }
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def image_to_base64(image_path):
    """이미지를 base64로 변환"""
    try:
        with Image.open(image_path) as img:
            # 이미지 크기 조정 (최대 1200x800)
            img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
            
            # RGB로 변환 (RGBA인 경우)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # base64로 인코딩
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"이미지 변환 오류: {e}")
        return None

def get_image_files():
    """이미지 파일 목록 반환"""
    global image_files
    if not image_files:
        for genre_dir in data_dir.iterdir():
            if genre_dir.is_dir():
                for img_file in genre_dir.glob('*.jpeg'):
                    image_files.append(img_file)
    return image_files

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('bbox_labeling.html')

@app.route('/api/bbox_image_list')
def get_image_list():
    """이미지 파일 목록 반환"""
    try:
        image_files = get_image_files()
        file_list = []
        
        for i, img_file in enumerate(image_files):
            file_list.append({
                'index': i,
                'name': img_file.name,
                'path': str(img_file)
            })
        
        return jsonify({
            'success': True,
            'image_files': file_list,
            'total_count': len(image_files)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/bbox_image/<int:index>')
def get_image(index):
    """특정 인덱스의 이미지 반환"""
    try:
        image_files = get_image_files()
        
        if index < 0 or index >= len(image_files):
            return jsonify({
                'success': False,
                'message': '유효하지 않은 이미지 인덱스입니다.'
            })
        
        image_path = image_files[index]
        
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
            'image_index': index
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/bbox_annotations/<path:image_path>')
def get_annotations(image_path):
    """이미지의 어노테이션 반환"""
    try:
        # YOLO 형식 어노테이션 파일 경로
        annotation_file = get_annotation_file_path(image_path)
        
        if annotation_file.exists():
            with open(annotation_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            annotations = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    # YOLO 형식을 상대 좌표로 변환
                    x = x_center - width / 2
                    y = y_center - height / 2
                    
                    # 클래스 ID를 라벨로 변환
                    label = get_label_from_class_id(class_id)
                    
                    annotations.append({
                        'id': len(annotations),
                        'label': label,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })
            
            return jsonify({
                'success': True,
                'annotations': annotations
            })
        else:
            return jsonify({
                'success': True,
                'annotations': []
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/bbox_save_annotations', methods=['POST'])
def save_annotations():
    """어노테이션 저장"""
    try:
        data = request.json
        image_path = data.get('image_path')
        annotations = data.get('annotations', [])
        
        if not image_path:
            return jsonify({
                'success': False,
                'message': '이미지 경로가 필요합니다.'
            })
        
        # 어노테이션 파일 경로
        annotation_file = get_annotation_file_path(image_path)
        annotation_file.parent.mkdir(parents=True, exist_ok=True)
        
        # YOLO 형식으로 저장
        with open(annotation_file, 'w', encoding='utf-8') as f:
            for bbox in annotations:
                # 상대 좌표를 YOLO 형식으로 변환
                x_center = bbox['x'] + bbox['width'] / 2
                y_center = bbox['y'] + bbox['height'] / 2
                width = bbox['width']
                height = bbox['height']
                
                # 라벨을 클래스 ID로 변환
                class_id = get_class_id_from_label(bbox['label'])
                
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        return jsonify({
            'success': True,
            'message': '어노테이션이 저장되었습니다.',
            'annotation_file': str(annotation_file)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

def get_annotation_file_path(image_path):
    """이미지 경로에서 어노테이션 파일 경로 생성"""
    image_path = Path(image_path)
    # data/raw/discogs/... -> data/processed/annotations/...
    relative_path = image_path.relative_to(data_dir)
    annotation_path = output_dir / 'annotations' / relative_path.with_suffix('.txt')
    return annotation_path

def get_label_from_class_id(class_id):
    """클래스 ID를 라벨로 변환"""
    labels = ['front', 'back', 'inner', 'disk']
    if 0 <= class_id < len(labels):
        return labels[class_id]
    return 'unknown'

def get_class_id_from_label(label):
    """라벨을 클래스 ID로 변환"""
    labels = ['front', 'back', 'inner', 'disk']
    try:
        return labels.index(label)
    except ValueError:
        return 0

@app.route('/api/bbox_stats')
def get_stats():
    """통계 정보 반환"""
    try:
        image_files = get_image_files()
        total_images = len(image_files)
        
        # 어노테이션 통계
        annotation_stats = {
            'total_images': total_images,
            'annotated_images': 0,
            'total_annotations': 0,
            'label_counts': {'front': 0, 'back': 0, 'inner': 0, 'disk': 0}
        }
        
        for image_file in image_files:
            annotation_file = get_annotation_file_path(image_file)
            if annotation_file.exists():
                annotation_stats['annotated_images'] += 1
                
                with open(annotation_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        label = get_label_from_class_id(class_id)
                        annotation_stats['total_annotations'] += 1
                        annotation_stats['label_counts'][label] += 1
        
        return jsonify({
            'success': True,
            'stats': annotation_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

def main():
    """메인 함수"""
    global data_dir, output_dir, progress_file
    
    parser = argparse.ArgumentParser(description='바운딩 박스 라벨링 웹 서버')
    parser.add_argument('--data_dir', default='data/raw/discogs', help='원본 이미지 디렉토리')
    parser.add_argument('--output_dir', default='data/processed', help='어노테이션 출력 디렉토리')
    parser.add_argument('--port', type=int, default=5001, help='웹 서버 포트')
    parser.add_argument('--host', default='127.0.0.1', help='웹 서버 호스트')
    
    args = parser.parse_args()
    
    # 디렉토리 설정
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    if not data_dir.exists():
        print(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
        return
    
    # 출력 디렉토리 생성
    (output_dir / 'annotations').mkdir(parents=True, exist_ok=True)
    
    # 진행상황 파일
    progress_file = output_dir / "bbox_labeling_progress.json"
    
    # 진행상황 로드
    load_progress()
    
    # 이미지 파일 목록 생성
    image_files = get_image_files()
    
    print(f"🎯 바운딩 박스 라벨링 도구를 시작합니다!")
    print(f"📁 데이터 디렉토리: {data_dir}")
    print(f"📁 출력 디렉토리: {output_dir}")
    print(f"📊 총 이미지: {len(image_files)}개")
    print(f"🌐 웹 인터페이스: http://{args.host}:{args.port}")
    print("=" * 60)
    print("🎨 라벨링 방법:")
    print("  - 마우스로 드래그하여 바운딩 박스 생성")
    print("  - 1-4 키로 라벨 선택 (1:앞면, 2:뒤면, 3:속지, 4:LP판)")
    print("  - Ctrl+S로 저장")
    print("  - Delete로 선택된 박스 삭제")
    print("=" * 60)
    
    # 웹 서버 시작
    app.run(host=args.host, port=args.port, debug=True)

if __name__ == "__main__":
    main()
