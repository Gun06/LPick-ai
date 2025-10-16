#!/usr/bin/env python3
"""
간단한 LP 이미지 레이블링 도구 (tkinter 없이)
LP의 앞면(front), 뒤면(back), 속지(inner)를 구분하여 레이블링하는 CLI 도구
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import random
from PIL import Image
import argparse

class SimpleLPLabelingTool:
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.labels = ['front', 'back', 'inner', 'disk']
        self.current_label = None
        self.labeled_count = 0
        self.total_images = 0
        self.labeled_data = {}
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for label in self.labels:
            (self.output_dir / label).mkdir(exist_ok=True)
        
        # 레이블링 진행상황 파일
        self.progress_file = self.output_dir / "labeling_progress.json"
        self.load_progress()
    
    def load_progress(self):
        """이전 레이블링 진행상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.labeled_data = data.get('labeled_data', {})
                self.labeled_count = data.get('labeled_count', 0)
        
        # 이미지 파일 목록 생성
        self.image_files = []
        for genre_dir in self.data_dir.iterdir():
            if genre_dir.is_dir():
                for img_file in genre_dir.glob('*.jpeg'):
                    self.image_files.append(img_file)
        
        self.total_images = len(self.image_files)
        print(f"총 {self.total_images}개의 이미지 파일을 찾았습니다.")
    
    def show_image_info(self, image_path: Path):
        """이미지 정보 표시"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                print(f"이미지 크기: {width}x{height}")
                print(f"이미지 모드: {img.mode}")
        except Exception as e:
            print(f"이미지 정보 로드 실패: {e}")
    
    def label_image(self, image_path: Path, label: str):
        """이미지에 레이블 할당"""
        self.current_label = label
        self.labeled_data[str(image_path)] = label
        self.labeled_count += 1
        
        # 이미지를 해당 레이블 폴더로 복사
        dest_dir = self.output_dir / label
        dest_file = dest_dir / f"{self.labeled_count:06d}_{image_path.name}"
        shutil.copy2(image_path, dest_file)
        
        print(f"✅ 레이블링 완료: {image_path.name} → {label}")
        self.update_progress()
    
    def skip_image(self, image_path: Path):
        """현재 이미지 건너뛰기"""
        self.labeled_data[str(image_path)] = 'skipped'
        print(f"⏭️  건너뛰기: {image_path.name}")
        self.update_progress()
    
    def update_progress(self):
        """진행률 업데이트"""
        progress_text = f"진행률: {self.labeled_count}/{self.total_images}"
        print(f"📊 {progress_text}")
    
    def save_progress(self):
        """진행상황 저장"""
        progress_data = {
            'labeled_data': self.labeled_data,
            'labeled_count': self.labeled_count,
            'total_images': self.total_images
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 진행상황이 저장되었습니다. 레이블링된 이미지: {self.labeled_count}개")
    
    def run_interactive(self):
        """인터랙티브 모드 실행"""
        print("🎵 LP 이미지 레이블링 도구를 시작합니다!")
        print("=" * 60)
        print("🎯 레이블링 방법:")
        print("  - 1: 앞면 (Front Cover)")
        print("  - 2: 뒤면 (Back Cover)")
        print("  - 3: 속지 (Inner Sleeve)")
        print("  - 4: LP판 (Disk)")
        print("  - s: 건너뛰기")
        print("  - q: 종료")
        print("=" * 60)
        
        # 아직 레이블링되지 않은 이미지 찾기
        unlabeled_files = [f for f in self.image_files if str(f) not in self.labeled_data]
        
        if not unlabeled_files:
            print("🎉 모든 이미지가 레이블링되었습니다!")
            return
        
        # 랜덤하게 이미지 선택
        random.shuffle(unlabeled_files)
        
        for image_path in unlabeled_files:
            print(f"\n📁 현재 파일: {image_path.name}")
            print(f"📂 경로: {image_path}")
            
            # 이미지 정보 표시
            self.show_image_info(image_path)
            
            while True:
                try:
                    choice = input("\n선택하세요 (1/2/3/4/s/q): ").strip().lower()
                    
                    if choice == '1':
                        self.label_image(image_path, 'front')
                        break
                    elif choice == '2':
                        self.label_image(image_path, 'back')
                        break
                    elif choice == '3':
                        self.label_image(image_path, 'inner')
                        break
                    elif choice == '4':
                        self.label_image(image_path, 'disk')
                        break
                    elif choice == 's':
                        self.skip_image(image_path)
                        break
                    elif choice == 'q':
                        print("👋 레이블링을 종료합니다.")
                        self.save_progress()
                        return
                    else:
                        print("❌ 잘못된 선택입니다. 1, 2, 3, 4, s, q 중에서 선택해주세요.")
                        
                except KeyboardInterrupt:
                    print("\n\n⏹️  레이블링이 중단되었습니다.")
                    self.save_progress()
                    return
        
        print("\n🎉 모든 이미지 레이블링이 완료되었습니다!")
        self.save_progress()
    
    def run_batch(self, label: str, count: int = None):
        """배치 모드 실행"""
        unlabeled_files = [f for f in self.image_files if str(f) not in self.labeled_data]
        
        if not unlabeled_files:
            print("🎉 모든 이미지가 레이블링되었습니다!")
            return
        
        if count:
            unlabeled_files = unlabeled_files[:count]
        
        print(f"🔄 {label} 레이블로 {len(unlabeled_files)}개 이미지를 배치 처리합니다...")
        
        for i, image_path in enumerate(unlabeled_files, 1):
            print(f"[{i}/{len(unlabeled_files)}] 처리 중: {image_path.name}")
            self.label_image(image_path, label)
        
        print(f"✅ 배치 처리 완료: {len(unlabeled_files)}개 이미지")
        self.save_progress()

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='LP 이미지 레이블링 도구')
    parser.add_argument('--data_dir', default='data/raw/discogs', help='원본 이미지 디렉토리')
    parser.add_argument('--output_dir', default='data/processed/labeled', help='레이블링된 이미지 출력 디렉토리')
    parser.add_argument('--mode', choices=['interactive', 'batch'], default='interactive', help='실행 모드')
    parser.add_argument('--label', choices=['front', 'back', 'inner', 'disk'], help='배치 모드에서 사용할 레이블')
    parser.add_argument('--count', type=int, help='배치 모드에서 처리할 이미지 수')
    
    args = parser.parse_args()
    
    # 레이블링 도구 생성
    tool = SimpleLPLabelingTool(args.data_dir, args.output_dir)
    
    if args.mode == 'interactive':
        tool.run_interactive()
    elif args.mode == 'batch':
        if not args.label:
            print("❌ 배치 모드에서는 --label 옵션이 필요합니다.")
            return
        tool.run_batch(args.label, args.count)

if __name__ == "__main__":
    main()
