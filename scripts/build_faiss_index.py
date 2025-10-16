#!/usr/bin/env python3
"""
FAISS 벡터 검색 인덱스 구축 스크립트

기능:
1. CLIP 임베딩을 FAISS 인덱스로 변환
2. 다양한 인덱스 타입 테스트
3. 검색 성능 벤치마크
4. 인덱스 저장 및 검색 테스트
"""

import os
import sys
import time
import json
import numpy as np
from pathlib import Path
import pickle

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("❌ FAISS 라이브러리가 설치되지 않았습니다.")
    print("설치 방법:")
    print("  pip install faiss-cpu  # CPU 버전")
    print("  pip install faiss-gpu  # GPU 버전")
    FAISS_AVAILABLE = False
    sys.exit(1)

class FAISSIndexBuilder:
    """FAISS 인덱스 구축 클래스"""
    
    def __init__(self, 
                 embeddings_dir='data/processed/embeddings',
                 output_dir='data/processed/faiss_index'):
        
        self.embeddings_dir = Path(embeddings_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = None
        self.metadata = None
        self.dimension = None
        self.num_vectors = None
        
        # 인덱스들
        self.index_flat = None
        self.index_ivf = None
    
    def load_embeddings(self):
        """임베딩 및 메타데이터 로드"""
        print("\n📂 임베딩 데이터 로드 중...")
        
        # 임베딩 로드
        embeddings_file = self.embeddings_dir / 'clip_embeddings.npy'
        if not embeddings_file.exists():
            print(f"❌ 임베딩 파일을 찾을 수 없습니다: {embeddings_file}")
            return False
        
        self.embeddings = np.load(embeddings_file)
        self.num_vectors, self.dimension = self.embeddings.shape
        
        print(f"✅ 임베딩 로드 완료")
        print(f"   벡터 개수: {self.num_vectors:,}개")
        print(f"   벡터 차원: {self.dimension}")
        print(f"   데이터 크기: {self.embeddings.nbytes / 1024 / 1024:.2f} MB")
        
        # 메타데이터 로드
        metadata_file = self.embeddings_dir / 'metadata_mapping.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            print(f"✅ 메타데이터 로드 완료: {len(self.metadata):,}개")
        
        return True
    
    def build_flat_index(self):
        """Flat 인덱스 구축 (정확도 우선)"""
        print(f"\n🔨 IndexFlatL2 구축 중...")
        print("   - 타입: Flat (Brute-force)")
        print("   - 특징: 가장 정확하지만 느림")
        
        start_time = time.time()
        
        # L2 거리 기반 Flat 인덱스
        self.index_flat = faiss.IndexFlatL2(self.dimension)
        self.index_flat.add(self.embeddings.astype('float32'))
        
        build_time = time.time() - start_time
        
        print(f"✅ IndexFlatL2 구축 완료")
        print(f"   빌드 시간: {build_time:.2f}초")
        print(f"   인덱스 크기: {self.index_flat.ntotal:,}개 벡터")
        
        return build_time
    
    def build_ivf_index(self, nlist=100):
        """IVF 인덱스 구축 (속도 우선)"""
        print(f"\n🔨 IndexIVFFlat 구축 중...")
        print(f"   - 타입: IVF (Inverted File)")
        print(f"   - nlist: {nlist} (클러스터 개수)")
        print(f"   - 특징: 빠르지만 약간의 정확도 손실")
        
        start_time = time.time()
        
        # Quantizer (L2 거리 기반)
        quantizer = faiss.IndexFlatL2(self.dimension)
        
        # IVF 인덱스 생성
        self.index_ivf = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        # 훈련 (클러스터링)
        print("   훈련 중...")
        self.index_ivf.train(self.embeddings.astype('float32'))
        
        # 벡터 추가
        print("   벡터 추가 중...")
        self.index_ivf.add(self.embeddings.astype('float32'))
        
        build_time = time.time() - start_time
        
        print(f"✅ IndexIVFFlat 구축 완료")
        print(f"   빌드 시간: {build_time:.2f}초")
        print(f"   인덱스 크기: {self.index_ivf.ntotal:,}개 벡터")
        print(f"   클러스터 수: {nlist}")
        
        return build_time
    
    def benchmark_search(self, k=10, n_queries=100):
        """검색 성능 벤치마크"""
        print(f"\n⏱️  검색 성능 벤치마크")
        print(f"=" * 60)
        print(f"   쿼리 개수: {n_queries}개")
        print(f"   Top-K: {k}")
        
        # 랜덤 쿼리 선택
        query_indices = np.random.choice(self.num_vectors, n_queries, replace=False)
        query_vectors = self.embeddings[query_indices].astype('float32')
        
        results = {}
        
        # IndexFlatL2 벤치마크
        if self.index_flat:
            print(f"\n📊 IndexFlatL2 벤치마크:")
            start_time = time.time()
            
            for query in query_vectors:
                distances, indices = self.index_flat.search(query.reshape(1, -1), k)
            
            flat_time = (time.time() - start_time) / n_queries
            print(f"   평균 검색 시간: {flat_time * 1000:.2f}ms")
            
            results['flat'] = {
                'avg_time_ms': flat_time * 1000,
                'index_type': 'IndexFlatL2'
            }
        
        # IndexIVFFlat 벤치마크
        if self.index_ivf:
            print(f"\n📊 IndexIVFFlat 벤치마크:")
            
            # nprobe 값 조정 (검색할 클러스터 수)
            for nprobe in [1, 5, 10, 20]:
                self.index_ivf.nprobe = nprobe
                
                start_time = time.time()
                
                for query in query_vectors:
                    distances, indices = self.index_ivf.search(query.reshape(1, -1), k)
                
                ivf_time = (time.time() - start_time) / n_queries
                print(f"   nprobe={nprobe:2d}: {ivf_time * 1000:.2f}ms")
                
                results[f'ivf_nprobe_{nprobe}'] = {
                    'avg_time_ms': ivf_time * 1000,
                    'index_type': 'IndexIVFFlat',
                    'nprobe': nprobe
                }
        
        return results
    
    def test_search_quality(self, k=10):
        """검색 품질 테스트"""
        print(f"\n🎯 검색 품질 테스ト")
        print(f"=" * 60)
        
        # 테스트 쿼리 (첫 번째 이미지)
        test_query = self.embeddings[0:1].astype('float32')
        
        # Flat 인덱스 검색
        if self.index_flat:
            distances_flat, indices_flat = self.index_flat.search(test_query, k)
            
            print(f"\n📊 IndexFlatL2 검색 결과:")
            print(f"   Top-{k} 유사 이미지:")
            for i, (dist, idx) in enumerate(zip(distances_flat[0], indices_flat[0])):
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    print(f"   {i+1}. {meta['genre']:15s} | {meta['filename'][:40]:40s} | 거리: {dist:.4f}")
        
        # IVF 인덱스 검색 (nprobe=10)
        if self.index_ivf:
            self.index_ivf.nprobe = 10
            distances_ivf, indices_ivf = self.index_ivf.search(test_query, k)
            
            print(f"\n📊 IndexIVFFlat 검색 결과 (nprobe=10):")
            print(f"   Top-{k} 유사 이미지:")
            for i, (dist, idx) in enumerate(zip(distances_ivf[0], indices_ivf[0])):
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    print(f"   {i+1}. {meta['genre']:15s} | {meta['filename'][:40]:40s} | 거리: {dist:.4f}")
    
    def save_indexes(self):
        """인덱스 저장"""
        print(f"\n💾 인덱스 저장 중...")
        
        # Flat 인덱스 저장
        if self.index_flat:
            flat_file = self.output_dir / 'index_flat_l2.faiss'
            faiss.write_index(self.index_flat, str(flat_file))
            file_size = flat_file.stat().st_size / 1024 / 1024
            print(f"✅ IndexFlatL2 저장: {flat_file}")
            print(f"   파일 크기: {file_size:.2f} MB")
        
        # IVF 인덱스 저장
        if self.index_ivf:
            ivf_file = self.output_dir / 'index_ivf_flat.faiss'
            faiss.write_index(self.index_ivf, str(ivf_file))
            file_size = ivf_file.stat().st_size / 1024 / 1024
            print(f"✅ IndexIVFFlat 저장: {ivf_file}")
            print(f"   파일 크기: {file_size:.2f} MB")
        
        # 메타데이터 매핑 저장
        mapping_file = self.output_dir / 'id_to_metadata_mapping.json'
        id_mapping = {
            i: meta for i, meta in enumerate(self.metadata)
        }
        
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(id_mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ ID 매핑 저장: {mapping_file}")
    
    def save_index_info(self, benchmark_results, build_times):
        """인덱스 정보 저장"""
        print(f"\n📋 인덱스 정보 저장 중...")
        
        info = {
            'creation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'num_vectors': int(self.num_vectors),
            'dimension': int(self.dimension),
            'embeddings_file': 'clip_embeddings.npy',
            'build_times': build_times,
            'benchmark_results': benchmark_results,
            'indexes': {
                'flat': {
                    'type': 'IndexFlatL2',
                    'file': 'index_flat_l2.faiss',
                    'description': 'Exact search (brute-force)',
                    'pros': ['Most accurate', 'Simple'],
                    'cons': ['Slower for large datasets']
                },
                'ivf': {
                    'type': 'IndexIVFFlat',
                    'file': 'index_ivf_flat.faiss',
                    'description': 'Approximate search with clustering',
                    'pros': ['Faster search', 'Good accuracy'],
                    'cons': ['Requires training', 'Small accuracy loss'],
                    'recommended_nprobe': 10
                }
            },
            'recommendation': 'Use IndexFlatL2 for < 100K vectors, IndexIVFFlat for > 100K'
        }
        
        info_file = self.output_dir / 'index_info.json'
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 인덱스 정보 저장: {info_file}")
    
    def create_summary_report(self, benchmark_results, build_times):
        """요약 리포트 생성"""
        print(f"\n" + "=" * 70)
        print(f"📋 FAISS 인덱스 구축 요약")
        print(f"=" * 70)
        
        print(f"\n📊 인덱스 정보:")
        print(f"   벡터 개수: {self.num_vectors:,}개")
        print(f"   벡터 차원: {self.dimension}")
        print(f"   총 데이터 크기: {self.embeddings.nbytes / 1024 / 1024:.2f} MB")
        
        print(f"\n⏱️  빌드 시간:")
        for index_type, build_time in build_times.items():
            print(f"   {index_type}: {build_time:.2f}초")
        
        print(f"\n🔍 검색 성능 (평균):")
        for index_name, result in benchmark_results.items():
            print(f"   {index_name}: {result['avg_time_ms']:.2f}ms")
        
        print(f"\n💡 권장사항:")
        if self.num_vectors < 100000:
            print(f"   ⭐ IndexFlatL2 사용 권장")
            print(f"   이유: 벡터 개수({self.num_vectors:,})가 10만 개 미만")
            print(f"   검색 속도: ~{benchmark_results.get('flat', {}).get('avg_time_ms', 0):.2f}ms")
        else:
            print(f"   ⭐ IndexIVFFlat (nprobe=10) 사용 권장")
            print(f"   이유: 벡터 개수가 많아 속도 최적화 필요")
        
        print(f"\n📁 생성된 파일:")
        print(f"   - index_flat_l2.faiss")
        print(f"   - index_ivf_flat.faiss")
        print(f"   - id_to_metadata_mapping.json")
        print(f"   - index_info.json")
        
        print(f"=" * 70)

def main():
    """메인 함수"""
    print("🎯 FAISS 벡터 검색 인덱스 구축")
    print("=" * 70)
    
    if not FAISS_AVAILABLE:
        return
    
    # 인덱스 빌더 생성
    builder = FAISSIndexBuilder(
        embeddings_dir='data/processed/embeddings',
        output_dir='data/processed/faiss_index'
    )
    
    # 1. 임베딩 로드
    if not builder.load_embeddings():
        print("❌ 임베딩 로드 실패")
        return
    
    build_times = {}
    
    # 2. Flat 인덱스 구축
    flat_time = builder.build_flat_index()
    build_times['IndexFlatL2'] = flat_time
    
    # 3. IVF 인덱스 구축
    ivf_time = builder.build_ivf_index(nlist=100)
    build_times['IndexIVFFlat'] = ivf_time
    
    # 4. 검색 성능 벤치마크
    benchmark_results = builder.benchmark_search(k=10, n_queries=100)
    
    # 5. 검색 품질 테스트
    builder.test_search_quality(k=10)
    
    # 6. 인덱스 저장
    builder.save_indexes()
    
    # 7. 인덱스 정보 저장
    builder.save_index_info(benchmark_results, build_times)
    
    # 8. 요약 리포트
    builder.create_summary_report(benchmark_results, build_times)
    
    print(f"\n🎉 FAISS 인덱스 구축 완료!")
    print(f"\n🚀 다음 단계: 검색 API 개발")

if __name__ == "__main__":
    main()

