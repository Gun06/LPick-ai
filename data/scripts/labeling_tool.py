#!/usr/bin/env python3
"""
LP 이미지 레이블링 도구
LP의 앞면(front), 뒤면(back), 속지(inner)를 구분하여 레이블링하는 인터랙티브 도구
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import random

class LPLabelingTool:
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.labels = ['front', 'back', 'inner']
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
        
        # GUI 설정
        self.setup_gui()
        self.load_next_image()
    
    def setup_gui(self):
        """GUI 인터페이스 설정"""
        self.root = tk.Tk()
        self.root.title("LP 이미지 레이블링 도구")
        self.root.geometry("1200x800")
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단 정보 프레임
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(info_frame, text="진행률: 0/0")
        self.progress_label.pack(side=tk.LEFT)
        
        self.current_file_label = ttk.Label(info_frame, text="현재 파일: 없음")
        self.current_file_label.pack(side=tk.RIGHT)
        
        # 이미지 표시 프레임
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        # 이미지 캔버스
        self.image_canvas = tk.Canvas(image_frame, bg='white')
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 레이블링 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 레이블 버튼들
        self.label_buttons = {}
        for i, label in enumerate(self.labels):
            btn = ttk.Button(
                button_frame, 
                text=f"{label.upper()}", 
                command=lambda l=label: self.label_image(l),
                width=15
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.label_buttons[label] = btn
        
        # 건너뛰기 버튼
        skip_btn = ttk.Button(button_frame, text="건너뛰기", command=self.skip_image)
        skip_btn.pack(side=tk.LEFT, padx=5)
        
        # 저장 및 종료 버튼
        save_btn = ttk.Button(button_frame, text="저장", command=self.save_progress)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        exit_btn = ttk.Button(button_frame, text="종료", command=self.exit_app)
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        # 키보드 단축키
        self.root.bind('<KeyPress-1>', lambda e: self.label_image('front'))
        self.root.bind('<KeyPress-2>', lambda e: self.label_image('back'))
        self.root.bind('<KeyPress-3>', lambda e: self.label_image('inner'))
        self.root.bind('<KeyPress-s>', lambda e: self.skip_image())
        self.root.focus_set()
    
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
    
    def load_next_image(self):
        """다음 이미지 로드"""
        # 아직 레이블링되지 않은 이미지 찾기
        unlabeled_files = [f for f in self.image_files if str(f) not in self.labeled_data]
        
        if not unlabeled_files:
            messagebox.showinfo("완료", "모든 이미지가 레이블링되었습니다!")
            return
        
        # 랜덤하게 이미지 선택
        self.current_file = random.choice(unlabeled_files)
        self.current_file_label.config(text=f"현재 파일: {self.current_file.name}")
        
        # 이미지 로드 및 표시
        try:
            image = Image.open(self.current_file)
            # 이미지 크기 조정 (최대 800x600)
            image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            
            # 캔버스에 이미지 표시
            self.image_canvas.delete("all")
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
        except Exception as e:
            messagebox.showerror("오류", f"이미지 로드 실패: {e}")
            self.skip_image()
    
    def label_image(self, label: str):
        """이미지에 레이블 할당"""
        if not hasattr(self, 'current_file'):
            return
        
        self.current_label = label
        self.labeled_data[str(self.current_file)] = label
        self.labeled_count += 1
        
        # 이미지를 해당 레이블 폴더로 복사
        dest_dir = self.output_dir / label
        dest_file = dest_dir / f"{self.labeled_count:06d}_{self.current_file.name}"
        shutil.copy2(self.current_file, dest_file)
        
        # 진행률 업데이트
        self.update_progress()
        
        # 다음 이미지 로드
        self.load_next_image()
    
    def skip_image(self):
        """현재 이미지 건너뛰기"""
        if not hasattr(self, 'current_file'):
            return
        
        self.labeled_data[str(self.current_file)] = 'skipped'
        self.update_progress()
        self.load_next_image()
    
    def update_progress(self):
        """진행률 업데이트"""
        progress_text = f"진행률: {self.labeled_count}/{self.total_images}"
        self.progress_label.config(text=progress_text)
        print(f"레이블링 완료: {self.labeled_count}/{self.total_images}")
    
    def save_progress(self):
        """진행상황 저장"""
        progress_data = {
            'labeled_data': self.labeled_data,
            'labeled_count': self.labeled_count,
            'total_images': self.total_images
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo("저장 완료", f"진행상황이 저장되었습니다.\n레이블링된 이미지: {self.labeled_count}개")
    
    def exit_app(self):
        """앱 종료"""
        self.save_progress()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """앱 실행"""
        self.root.mainloop()

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LP 이미지 레이블링 도구')
    parser.add_argument('--data_dir', default='data/raw/discogs', help='원본 이미지 디렉토리')
    parser.add_argument('--output_dir', default='data/processed/labeled', help='레이블링된 이미지 출력 디렉토리')
    
    args = parser.parse_args()
    
    # 레이블링 도구 실행
    app = LPLabelingTool(args.data_dir, args.output_dir)
    app.run()

if __name__ == "__main__":
    main()
