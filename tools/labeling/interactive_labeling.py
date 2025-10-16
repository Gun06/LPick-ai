#!/usr/bin/env python3
"""
인터랙티브 LP 이미지 레이블링 도구
이미지를 하나씩 보면서 직접 레이블링할 수 있는 도구
"""

import os
import sys
import json
import shutil
from pathlib import Path
import random
from PIL import Image
import argparse

def display_image_info(image_path: Path):
    """이미지 정보 표시"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            print(f"📏 이미지 크기: {width}x{height}")
            print(f"🎨 이미지 모드: {img.mode}")
            
            # 이미지 미리보기 (텍스트 기반)
            img.thumbnail((80, 80))
            print("🖼️  이미지 미리보기:")
            print("   (실제 이미지를 보려면 파일을 직접 열어보세요)")
            print(f"   📁 파일 경로: {image_path}")
            
    except Exception as e:
        print(f"❌ 이미지 정보 로드 실패: {e}")

def interactive_labeling(data_dir: str, output_dir: str, start_from: int = 0):
    """인터랙티브 레이블링"""
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    
    # 출력 디렉토리 생성
    labels = ['front', 'back', 'inner', 'disk']
    output_path.mkdir(parents=True, exist_ok=True)
    for label in labels:
        (output_path / label).mkdir(exist_ok=True)
    
    # 진행상황 파일
    progress_file = output_path / "labeling_progress.json"
    labeled_data = {}
    labeled_count = 0
    
    # 이전 진행상황 로드
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            labeled_data = data.get('labeled_data', {})
            labeled_count = data.get('labeled_count', 0)
    
    # 이미지 파일 목록 생성
    image_files = []
    for genre_dir in data_path.iterdir():
        if genre_dir.is_dir():
            for img_file in genre_dir.glob('*.jpeg'):
                image_files.append(img_file)
    
    # 아직 레이블링되지 않은 이미지 찾기
    unlabeled_files = [f for f in image_files if str(f) not in labeled_data]
    
    if not unlabeled_files:
        print("🎉 모든 이미지가 레이블링되었습니다!")
        return
    
    # 시작 위치 설정
    if start_from > 0:
        unlabeled_files = unlabeled_files[start_from:]
    
    total_images = len(unlabeled_files)
    print(f"🎵 LP 이미지 레이블링 도구를 시작합니다!")
    print(f"📊 남은 이미지: {total_images}개")
    print("=" * 60)
    print("🎯 레이블링 방법:")
    print("  - 1: 앞면 (Front Cover)")
    print("  - 2: 뒤면 (Back Cover)")
    print("  - 3: 속지 (Inner Sleeve)")
    print("  - 4: LP판 (Disk)")
    print("  - s: 건너뛰기")
    print("  - q: 종료")
    print("  - p: 이전 이미지로 돌아가기")
    print("=" * 60)
    
    current_index = 0
    previous_images = []  # 이전 이미지들을 저장
    
    while current_index < len(unlabeled_files):
        image_path = unlabeled_files[current_index]
        
        print(f"\n📁 [{current_index + 1}/{total_images}] 현재 파일: {image_path.name}")
        print(f"📂 경로: {image_path}")
        
        # 이미지 정보 표시
        display_image_info(image_path)
        
        # 이미지 열기 옵션 제공
        print(f"\n💡 이미지를 직접 보려면:")
        print(f"   open '{image_path}'")
        print(f"   또는 파일 탐색기에서 해당 경로를 열어보세요.")
        
        while True:
            try:
                choice = input(f"\n선택하세요 (1/2/3/4/s/q/p): ").strip().lower()
                
                if choice == '1':
                    # 앞면 레이블링
                    labeled_count += 1
                    labeled_data[str(image_path)] = 'front'
                    dest_file = output_path / 'front' / f"{labeled_count:06d}_{image_path.name}"
                    shutil.copy2(image_path, dest_file)
                    print(f"✅ 레이블링 완료: {image_path.name} → front")
                    previous_images.append(current_index)
                    current_index += 1
                    break
                    
                elif choice == '2':
                    # 뒤면 레이블링
                    labeled_count += 1
                    labeled_data[str(image_path)] = 'back'
                    dest_file = output_path / 'back' / f"{labeled_count:06d}_{image_path.name}"
                    shutil.copy2(image_path, dest_file)
                    print(f"✅ 레이블링 완료: {image_path.name} → back")
                    previous_images.append(current_index)
                    current_index += 1
                    break
                    
                elif choice == '3':
                    # 속지 레이블링
                    labeled_count += 1
                    labeled_data[str(image_path)] = 'inner'
                    dest_file = output_path / 'inner' / f"{labeled_count:06d}_{image_path.name}"
                    shutil.copy2(image_path, dest_file)
                    print(f"✅ 레이블링 완료: {image_path.name} → inner")
                    previous_images.append(current_index)
                    current_index += 1
                    break
                    
                elif choice == '4':
                    # LP판 레이블링
                    labeled_count += 1
                    labeled_data[str(image_path)] = 'disk'
                    dest_file = output_path / 'disk' / f"{labeled_count:06d}_{image_path.name}"
                    shutil.copy2(image_path, dest_file)
                    print(f"✅ 레이블링 완료: {image_path.name} → disk")
                    previous_images.append(current_index)
                    current_index += 1
                    break
                    
                elif choice == 's':
                    # 건너뛰기
                    labeled_data[str(image_path)] = 'skipped'
                    print(f"⏭️  건너뛰기: {image_path.name}")
                    previous_images.append(current_index)
                    current_index += 1
                    break
                    
                elif choice == 'p':
                    # 이전 이미지로 돌아가기
                    if previous_images:
                        current_index = previous_images.pop()
                        print(f"⬅️  이전 이미지로 돌아갑니다: {unlabeled_files[current_index].name}")
                        break
                    else:
                        print("❌ 이전 이미지가 없습니다.")
                        
                elif choice == 'q':
                    # 종료
                    print("👋 레이블링을 종료합니다.")
                    # 진행상황 저장
                    progress_data = {
                        'labeled_data': labeled_data,
                        'labeled_count': labeled_count,
                        'total_images': len(image_files)
                    }
                    with open(progress_file, 'w', encoding='utf-8') as f:
                        json.dump(progress_data, f, ensure_ascii=False, indent=2)
                    print(f"💾 진행상황이 저장되었습니다. 레이블링된 이미지: {labeled_count}개")
                    return
                    
                else:
                    print("❌ 잘못된 선택입니다. 1, 2, 3, 4, s, q, p 중에서 선택해주세요.")
                    
            except KeyboardInterrupt:
                print("\n\n⏹️  레이블링이 중단되었습니다.")
                # 진행상황 저장
                progress_data = {
                    'labeled_data': labeled_data,
                    'labeled_count': labeled_count,
                    'total_images': len(image_files)
                }
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2)
                print(f"💾 진행상황이 저장되었습니다. 레이블링된 이미지: {labeled_count}개")
                return
        
        # 진행률 표시
        print(f"📊 진행률: {labeled_count}개 레이블링 완료")
    
    print("\n🎉 모든 이미지 레이블링이 완료되었습니다!")
    
    # 최종 진행상황 저장
    progress_data = {
        'labeled_data': labeled_data,
        'labeled_count': labeled_count,
        'total_images': len(image_files)
    }
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
    print(f"💾 최종 진행상황이 저장되었습니다. 레이블링된 이미지: {labeled_count}개")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='인터랙티브 LP 이미지 레이블링 도구')
    parser.add_argument('--data_dir', default='data/raw/discogs', help='원본 이미지 디렉토리')
    parser.add_argument('--output_dir', default='data/processed/labeled', help='레이블링된 이미지 출력 디렉토리')
    parser.add_argument('--start_from', type=int, default=0, help='시작할 이미지 인덱스')
    
    args = parser.parse_args()
    
    # 디렉토리 존재 확인
    if not Path(args.data_dir).exists():
        print(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {args.data_dir}")
        return
    
    print(f"📁 데이터 디렉토리: {args.data_dir}")
    print(f"📁 출력 디렉토리: {args.output_dir}")
    
    if args.start_from > 0:
        print(f"🚀 {args.start_from}번째 이미지부터 시작합니다.")
    
    interactive_labeling(args.data_dir, args.output_dir, args.start_from)

if __name__ == "__main__":
    main()
