#!/usr/bin/env python3
"""
전체 이미지 임베딩 생성 스크립트

기능:
1. 86,171개 LP 앨범 이미지의 CLIP 임베딩 생성
2. 배치 처리로 효율적인 처리
3. 체크포인트 시스템으로 재시작 가능
4. 진행상황 실시간 표시
5. 메타데이터 매핑 파일 생성
"""

import os
import sys
import time
import json
import pickle
import numpy as np
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from datetime import datetime

import torch
from transformers import CLIPProcessor, CLIPModel

class EmbeddingGenerator:
    """CLIP 임베딩 생성기"""
    
    def __init__(self, 
                 data_dir='data/raw/discogs',
                 output_dir='data/processed/embeddings',
                 batch_size=32,
                 checkpoint_interval=1000):
        
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.checkpoint_dir = self.output_dir / 'checkpoints'
        self.batch_size = batch_size
        self.checkpoint_interval = checkpoint_interval
        
        # 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Device 설정
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Device: {self.device}")
        if torch.cuda.is_available():
            print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        
        # 모델 초기화
        self.model = None
        self.processor = None
        
        # 진행 상황 추적
        self.processed_images = set()
        self.embeddings_list = []
        self.metadata_list = []
        self.start_time = None
    
    def load_model(self):
        """CLIP 모델 로드"""
        print("\n🤖 CLIP 모델 로드 중...")
        try:
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model.eval()  # 평가 모드
            print(f"✅ CLIP 모델 로드 완료")
            print(f"   임베딩 차원: {self.model.config.projection_dim}")
            return True
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            return False
    
    def collect_image_files(self):
        """모든 이미지 파일 경로 수집"""
        print("\n📸 이미지 파일 수집 중...")
        
        image_files = []
        genres = [d for d in self.data_dir.iterdir() if d.is_dir()]
        
        for genre_dir in tqdm(genres, desc="장르별 이미지 수집"):
            genre_name = genre_dir.name
            images = list(genre_dir.glob('*.jpeg')) + list(genre_dir.glob('*.jpg'))
            
            for img_path in images:
                image_files.append({
                    'path': str(img_path),
                    'genre': genre_name,
                    'filename': img_path.name
                })
        
        print(f"✅ 총 {len(image_files):,}개 이미지 파일 수집 완료")
        return image_files
    
    def load_checkpoint(self):
        """체크포인트 로드"""
        checkpoint_file = self.checkpoint_dir / 'latest_checkpoint.pkl'
        
        if checkpoint_file.exists():
            try:
                print(f"\n💾 체크포인트 발견: {checkpoint_file}")
                with open(checkpoint_file, 'rb') as f:
                    checkpoint = pickle.load(f)
                
                self.processed_images = set(checkpoint['processed_images'])
                self.embeddings_list = checkpoint['embeddings_list']
                self.metadata_list = checkpoint['metadata_list']
                
                print(f"✅ 체크포인트 로드 완료")
                print(f"   이미 처리된 이미지: {len(self.processed_images):,}개")
                return True
            except Exception as e:
                print(f"⚠️  체크포인트 로드 실패: {e}")
                print("   처음부터 시작합니다.")
                return False
        else:
            print("\n📝 새로운 작업 시작")
            return False
    
    def save_checkpoint(self):
        """체크포인트 저장"""
        checkpoint_file = self.checkpoint_dir / 'latest_checkpoint.pkl'
        
        checkpoint = {
            'processed_images': list(self.processed_images),
            'embeddings_list': self.embeddings_list,
            'metadata_list': self.metadata_list,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint, f)
            return True
        except Exception as e:
            print(f"⚠️  체크포인트 저장 실패: {e}")
            return False
    
    def process_batch(self, batch_images):
        """배치 단위로 이미지 처리"""
        images = []
        valid_indices = []
        
        # 이미지 로드
        for idx, img_info in enumerate(batch_images):
            try:
                img = Image.open(img_info['path']).convert('RGB')
                images.append(img)
                valid_indices.append(idx)
            except Exception as e:
                print(f"\n⚠️  이미지 로드 실패: {img_info['filename']} - {e}")
                continue
        
        if not images:
            return []
        
        # 배치 처리
        try:
            inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # 정규화
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            embeddings = image_features.cpu().numpy()
            
            # 결과 리스트 생성
            results = []
            for i, idx in enumerate(valid_indices):
                results.append({
                    'embedding': embeddings[i],
                    'metadata': batch_images[idx]
                })
            
            return results
            
        except Exception as e:
            print(f"\n❌ 배치 처리 실패: {e}")
            return []
    
    def generate_embeddings(self, image_files):
        """전체 이미지 임베딩 생성"""
        print(f"\n🚀 임베딩 생성 시작")
        print(f"=" * 70)
        print(f"총 이미지: {len(image_files):,}개")
        print(f"배치 크기: {self.batch_size}")
        print(f"체크포인트 간격: {self.checkpoint_interval}개")
        print(f"=" * 70)
        
        self.start_time = time.time()
        
        # 아직 처리되지 않은 이미지만 필터링
        remaining_images = [
            img for img in image_files 
            if img['path'] not in self.processed_images
        ]
        
        if not remaining_images:
            print("✅ 모든 이미지가 이미 처리되었습니다!")
            return
        
        print(f"\n처리할 이미지: {len(remaining_images):,}개")
        
        # 배치 단위로 처리
        total_batches = (len(remaining_images) + self.batch_size - 1) // self.batch_size
        
        with tqdm(total=len(remaining_images), desc="임베딩 생성", unit="images") as pbar:
            for batch_idx in range(total_batches):
                start_idx = batch_idx * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(remaining_images))
                batch = remaining_images[start_idx:end_idx]
                
                # 배치 처리
                results = self.process_batch(batch)
                
                # 결과 저장
                for result in results:
                    self.embeddings_list.append(result['embedding'])
                    self.metadata_list.append(result['metadata'])
                    self.processed_images.add(result['metadata']['path'])
                
                pbar.update(len(batch))
                
                # 체크포인트 저장
                if len(self.processed_images) % self.checkpoint_interval == 0:
                    self.save_checkpoint()
                    
                    # 진행 상황 출력
                    elapsed = time.time() - self.start_time
                    images_per_sec = len(self.processed_images) / elapsed
                    remaining = len(image_files) - len(self.processed_images)
                    eta_seconds = remaining / images_per_sec if images_per_sec > 0 else 0
                    
                    print(f"\n💾 체크포인트 저장 완료 ({len(self.processed_images):,}/{len(image_files):,})")
                    print(f"   처리 속도: {images_per_sec:.2f} images/sec")
                    print(f"   예상 남은 시간: {eta_seconds/60:.1f}분")
        
        # 최종 체크포인트 저장
        self.save_checkpoint()
        
        print(f"\n✅ 임베딩 생성 완료!")
        print(f"   총 처리된 이미지: {len(self.processed_images):,}개")
        print(f"   총 소요 시간: {(time.time() - self.start_time)/60:.1f}분")
    
    def save_embeddings(self):
        """임베딩 및 메타데이터 저장"""
        print(f"\n💾 임베딩 저장 중...")
        
        # Numpy 배열로 변환
        embeddings_array = np.array(self.embeddings_list, dtype=np.float32)
        
        # 임베딩 저장
        embeddings_file = self.output_dir / 'clip_embeddings.npy'
        np.save(embeddings_file, embeddings_array)
        print(f"✅ 임베딩 저장: {embeddings_file}")
        print(f"   형태: {embeddings_array.shape}")
        print(f"   크기: {embeddings_array.nbytes / 1024 / 1024:.2f} MB")
        
        # 메타데이터 저장
        metadata_file = self.output_dir / 'metadata_mapping.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_list, f, indent=2, ensure_ascii=False)
        print(f"✅ 메타데이터 저장: {metadata_file}")
        
        # 임베딩 정보 저장
        info = {
            'model': 'openai/clip-vit-base-patch32',
            'embedding_dim': embeddings_array.shape[1],
            'num_images': embeddings_array.shape[0],
            'device': self.device,
            'batch_size': self.batch_size,
            'creation_date': datetime.now().isoformat(),
            'total_time_minutes': (time.time() - self.start_time) / 60 if self.start_time else 0
        }
        
        info_file = self.output_dir / 'embedding_info.json'
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        print(f"✅ 임베딩 정보 저장: {info_file}")
        
        # 체크포인트 정리
        print(f"\n🧹 체크포인트 파일 정리 중...")
        checkpoint_file = self.checkpoint_dir / 'latest_checkpoint.pkl'
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print(f"✅ 체크포인트 파일 삭제")
    
    def create_summary_report(self):
        """요약 리포트 생성"""
        print(f"\n📊 요약 리포트 생성 중...")
        
        # 장르별 통계
        genre_counts = {}
        for metadata in self.metadata_list:
            genre = metadata['genre']
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        report = {
            'summary': {
                'total_images': len(self.metadata_list),
                'embedding_dimension': 512,
                'total_time_minutes': (time.time() - self.start_time) / 60 if self.start_time else 0,
                'device': self.device
            },
            'genre_distribution': genre_counts,
            'files': {
                'embeddings': 'clip_embeddings.npy',
                'metadata': 'metadata_mapping.json',
                'info': 'embedding_info.json'
            }
        }
        
        report_file = self.output_dir / 'embedding_summary.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 요약 리포트 저장: {report_file}")
        
        # 콘솔 출력
        print(f"\n" + "=" * 70)
        print(f"📋 임베딩 생성 요약")
        print(f"=" * 70)
        print(f"총 이미지: {len(self.metadata_list):,}개")
        print(f"임베딩 차원: {report['summary']['embedding_dimension']}")
        print(f"총 소요 시간: {report['summary']['total_time_minutes']:.1f}분")
        print(f"Device: {self.device}")
        print(f"\n장르별 분포:")
        for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {genre:20s}: {count:8,}개")
        print(f"=" * 70)

def main():
    """메인 함수"""
    print("🎯 전체 이미지 임베딩 생성")
    print("=" * 70)
    
    # 설정
    generator = EmbeddingGenerator(
        data_dir='data/raw/discogs',
        output_dir='data/processed/embeddings',
        batch_size=32,  # CPU: 16-32, GPU: 64-128 권장
        checkpoint_interval=1000
    )
    
    # 1. 모델 로드
    if not generator.load_model():
        print("❌ 모델 로드 실패. 종료합니다.")
        return
    
    # 2. 이미지 파일 수집
    image_files = generator.collect_image_files()
    
    if not image_files:
        print("❌ 이미지 파일을 찾을 수 없습니다.")
        return
    
    # 3. 체크포인트 로드 (있으면)
    generator.load_checkpoint()
    
    # 4. 임베딩 생성
    try:
        generator.generate_embeddings(image_files)
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자가 중단했습니다.")
        print("💾 현재까지의 진행상황을 저장합니다...")
        generator.save_checkpoint()
        print("✅ 체크포인트 저장 완료. 나중에 다시 실행하면 이어서 진행됩니다.")
        return
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("💾 현재까지의 진행상황을 저장합니다...")
        generator.save_checkpoint()
        raise
    
    # 5. 임베딩 저장
    generator.save_embeddings()
    
    # 6. 요약 리포트 생성
    generator.create_summary_report()
    
    print(f"\n🎉 모든 작업 완료!")
    print(f"\n📁 생성된 파일:")
    print(f"  - data/processed/embeddings/clip_embeddings.npy")
    print(f"  - data/processed/embeddings/metadata_mapping.json")
    print(f"  - data/processed/embeddings/embedding_info.json")
    print(f"  - data/processed/embeddings/embedding_summary.json")
    print(f"\n🚀 다음 단계: FAISS 인덱스 구축")

if __name__ == "__main__":
    main()

