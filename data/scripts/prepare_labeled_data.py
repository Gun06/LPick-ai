#!/usr/bin/env python3
"""
레이블링된 LP 이미지 데이터 준비 및 전처리
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from PIL import Image
import numpy as np

class LabeledDataProcessor:
    def __init__(self, labeled_dir: str, output_dir: str):
        self.labeled_dir = Path(labeled_dir)
        self.output_dir = Path(output_dir)
        self.labels = ['front', 'back', 'inner', 'disk']
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for split in ['train', 'val', 'test']:
            for label in self.labels:
                (self.output_dir / split / label).mkdir(parents=True, exist_ok=True)
    
    def process_labeled_data(self, test_size: float = 0.2, val_size: float = 0.2):
        """레이블링된 데이터를 train/val/test로 분할"""
        
        # 각 레이블별 이미지 수집
        label_data = {label: [] for label in self.labels}
        
        for label in self.labels:
            label_dir = self.labeled_dir / label
            if label_dir.exists():
                for img_file in label_dir.glob('*.jpeg'):
                    label_data[label].append(img_file)
        
        # 데이터 분할
        all_data = []
        for label, files in label_data.items():
            for file_path in files:
                all_data.append({
                    'file_path': str(file_path),
                    'label': label,
                    'filename': file_path.name
                })
        
        # DataFrame 생성
        df = pd.DataFrame(all_data)
        
        # 레이블별로 분할
        train_data = []
        val_data = []
        test_data = []
        
        for label in self.labels:
            label_df = df[df['label'] == label]
            if len(label_df) == 0:
                continue
            
            # train/val/test 분할
            train, temp = train_test_split(label_df, test_size=test_size + val_size, random_state=42)
            val, test = train_test_split(temp, test_size=test_size/(test_size + val_size), random_state=42)
            
            train_data.append(train)
            val_data.append(val)
            test_data.append(test)
        
        # 분할된 데이터 저장
        train_df = pd.concat(train_data, ignore_index=True)
        val_df = pd.concat(val_data, ignore_index=True)
        test_df = pd.concat(test_data, ignore_index=True)
        
        # 파일 복사 및 메타데이터 저장
        self._copy_and_save_split(train_df, 'train')
        self._copy_and_save_split(val_df, 'val')
        self._copy_and_save_split(test_df, 'test')
        
        # 전체 메타데이터 저장
        metadata = {
            'total_images': len(df),
            'train_images': len(train_df),
            'val_images': len(val_df),
            'test_images': len(test_df),
            'label_distribution': df['label'].value_counts().to_dict(),
            'train_distribution': train_df['label'].value_counts().to_dict(),
            'val_distribution': val_df['label'].value_counts().to_dict(),
            'test_distribution': test_df['label'].value_counts().to_dict()
        }
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("데이터 분할 완료!")
        print(f"총 이미지: {metadata['total_images']}")
        print(f"Train: {metadata['train_images']}, Val: {metadata['val_images']}, Test: {metadata['test_images']}")
        print("레이블 분포:")
        for label, count in metadata['label_distribution'].items():
            print(f"  {label}: {count}")
    
    def _copy_and_save_split(self, df: pd.DataFrame, split_name: str):
        """분할된 데이터를 해당 디렉토리로 복사"""
        split_dir = self.output_dir / split_name
        
        for _, row in df.iterrows():
            src_path = Path(row['file_path'])
            dst_path = split_dir / row['label'] / row['filename']
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
        
        # 메타데이터 저장
        df.to_csv(split_dir / f'{split_name}_metadata.csv', index=False)
        print(f"{split_name} 분할 완료: {len(df)}개 이미지")
    
    def create_dataset_info(self):
        """데이터셋 정보 파일 생성"""
        dataset_info = {
            'name': 'LP Album Cover Classification Dataset',
            'description': 'LP 앨범의 앞면, 뒤면, 속지, LP판을 구분하는 이미지 분류 데이터셋',
            'labels': {
                'front': '앞면 (앨범 커버)',
                'back': '뒤면 (앨범 뒷면)',
                'inner': '속지 (내부 페이지)',
                'disk': 'LP판 (디스크)'
            },
            'image_format': 'JPEG',
            'image_size': 'Variable (resized to 224x224 for training)',
            'splits': ['train', 'val', 'test'],
            'created_date': pd.Timestamp.now().isoformat()
        }
        
        with open(self.output_dir / 'dataset_info.json', 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='레이블링된 LP 이미지 데이터 준비')
    parser.add_argument('--labeled_dir', default='data/processed/labeled', help='레이블링된 이미지 디렉토리')
    parser.add_argument('--output_dir', default='data/processed/dataset', help='최종 데이터셋 출력 디렉토리')
    parser.add_argument('--test_size', type=float, default=0.2, help='테스트 세트 비율')
    parser.add_argument('--val_size', type=float, default=0.2, help='검증 세트 비율')
    
    args = parser.parse_args()
    
    # 데이터 처리
    processor = LabeledDataProcessor(args.labeled_dir, args.output_dir)
    processor.process_labeled_data(args.test_size, args.val_size)
    processor.create_dataset_info()
    
    print("데이터 준비 완료!")

if __name__ == "__main__":
    main()
