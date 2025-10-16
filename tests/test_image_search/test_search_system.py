#!/usr/bin/env python3
"""
이미지 검색 시스템 통합 테스트

테스트 항목:
1. 검색 품질 테스트 (정확도)
2. 검색 속도 테스트 (성능)
3. API 엔드포인트 테스트
4. 에러 처리 테스트
5. 동시 요청 처리 테스트
"""

import os
import sys
import time
import json
import requests
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
import statistics

API_URL = "http://localhost:8000"

class SearchSystemTester:
    """검색 시스템 테스트 클래스"""
    
    def __init__(self, output_dir='tests/test_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_results = {
            'quality_tests': [],
            'performance_tests': [],
            'api_tests': [],
            'error_tests': [],
            'concurrent_tests': []
        }
    
    def check_server(self):
        """서버 상태 확인"""
        print("\n🏥 서버 상태 확인...")
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            data = response.json()
            
            if data['status'] == 'healthy':
                print("✅ 서버 정상 작동 중")
                return True
            else:
                print("❌ 서버 상태 이상")
                return False
        except Exception as e:
            print(f"❌ 서버 연결 실패: {e}")
            print("먼저 서버를 시작하세요: python3 scripts/run_search_api.py")
            return False
    
    def test_search_quality(self):
        """검색 품질 테스트"""
        print("\n🎯 검색 품질 테스트")
        print("=" * 70)
        
        # 샘플 이미지로 테스트
        data_dir = Path('data/raw/discogs')
        genres = [d for d in data_dir.iterdir() if d.is_dir()]
        
        quality_scores = []
        
        for i, genre_dir in enumerate(genres[:5]):  # 5개 장르 테스트
            images = list(genre_dir.glob('*.jpeg'))[:3]  # 각 장르당 3개
            
            for img_path in images:
                print(f"\n테스트 {i+1}: {genre_dir.name} - {img_path.name[:30]}...")
                
                # 이미지 검색
                with open(img_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{API_URL}/search/image",
                        files=files,
                        params={'top_k': 10}
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data['results']
                    
                    # 첫 번째 결과가 동일 이미지인지 확인
                    if results[0]['similarity'] > 0.99:
                        print("  ✅ 1위: 동일 이미지 검색 성공")
                        quality_score = 1.0
                    else:
                        print(f"  ⚠️  1위: 유사도 {results[0]['similarity']:.4f}")
                        quality_score = results[0]['similarity']
                    
                    # 같은 장르 비율 확인
                    same_genre_count = sum(1 for r in results if r['genre'] == genre_dir.name)
                    genre_ratio = same_genre_count / len(results)
                    
                    print(f"  📊 같은 장르 비율: {genre_ratio*100:.1f}% ({same_genre_count}/10)")
                    
                    quality_scores.append({
                        'genre': genre_dir.name,
                        'similarity': quality_score,
                        'same_genre_ratio': genre_ratio,
                        'query_time_ms': data['query_time_ms']
                    })
                else:
                    print(f"  ❌ 검색 실패: {response.status_code}")
        
        # 평균 품질
        avg_similarity = np.mean([s['similarity'] for s in quality_scores])
        avg_genre_ratio = np.mean([s['same_genre_ratio'] for s in quality_scores])
        
        print(f"\n📊 품질 테스트 요약:")
        print(f"  평균 유사도: {avg_similarity:.4f}")
        print(f"  평균 같은 장르 비율: {avg_genre_ratio*100:.1f}%")
        
        self.test_results['quality_tests'] = quality_scores
        
        return quality_scores
    
    def test_search_performance(self, n_queries=50):
        """검색 속도 테스트"""
        print(f"\n⏱️  검색 속도 테스트 ({n_queries}개 쿼리)")
        print("=" * 70)
        
        # 샘플 이미지
        data_dir = Path('data/raw/discogs')
        all_images = []
        for genre_dir in data_dir.iterdir():
            if genre_dir.is_dir():
                all_images.extend(list(genre_dir.glob('*.jpeg'))[:5])
        
        sample_images = np.random.choice(all_images, min(n_queries, len(all_images)), replace=False)
        
        response_times = []
        
        print("이미지 검색 속도 테스트 중...")
        for img_path in sample_images:
            try:
                with open(img_path, 'rb') as f:
                    files = {'file': f}
                    start_time = time.time()
                    response = requests.post(
                        f"{API_URL}/search/image",
                        files=files,
                        params={'top_k': 10}
                    )
                    end_time = time.time()
                
                if response.status_code == 200:
                    response_time = (end_time - start_time) * 1000  # ms
                    response_times.append(response_time)
            except Exception as e:
                print(f"⚠️  오류: {e}")
        
        # 통계
        if response_times:
            print(f"\n📊 성능 테스트 결과:")
            print(f"  평균 응답 시간: {np.mean(response_times):.2f}ms")
            print(f"  중앙값: {np.median(response_times):.2f}ms")
            print(f"  최소: {np.min(response_times):.2f}ms")
            print(f"  최대: {np.max(response_times):.2f}ms")
            print(f"  표준편차: {np.std(response_times):.2f}ms")
            
            self.test_results['performance_tests'] = {
                'mean': np.mean(response_times),
                'median': np.median(response_times),
                'min': np.min(response_times),
                'max': np.max(response_times),
                'std': np.std(response_times),
                'n_queries': len(response_times)
            }
        
        return response_times
    
    def test_text_search_quality(self):
        """텍스트 검색 품질 테스트"""
        print(f"\n💬 텍스트 검색 품질 테스트")
        print("=" * 70)
        
        test_queries = [
            ("jazz album", "Jazz"),
            ("rock music", "Rock"),
            ("classical piano", "Classical"),
            ("blues guitar", "Blues"),
            ("electronic music", "Electronic")
        ]
        
        results_summary = []
        
        for query, expected_genre in test_queries:
            print(f"\n쿼리: '{query}' (예상 장르: {expected_genre})")
            
            response = requests.post(
                f"{API_URL}/search/text",
                params={'query': query, 'top_k': 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data['results']
                
                # 예상 장르가 결과에 있는지 확인
                genre_count = sum(1 for r in results if expected_genre.lower() in r['genre'].lower())
                genre_ratio = genre_count / len(results)
                
                print(f"  검색 시간: {data['query_time_ms']:.2f}ms")
                print(f"  {expected_genre} 장르 비율: {genre_ratio*100:.1f}% ({genre_count}/10)")
                print(f"  Top-3 장르: {', '.join([r['genre'] for r in results[:3]])}")
                
                results_summary.append({
                    'query': query,
                    'expected_genre': expected_genre,
                    'genre_ratio': genre_ratio,
                    'query_time_ms': data['query_time_ms']
                })
            else:
                print(f"  ❌ 검색 실패")
        
        avg_ratio = np.mean([r['genre_ratio'] for r in results_summary])
        print(f"\n📊 평균 장르 일치율: {avg_ratio*100:.1f}%")
        
        self.test_results['text_search_quality'] = results_summary
        
        return results_summary
    
    def test_concurrent_requests(self, n_concurrent=10):
        """동시 요청 처리 테스트"""
        print(f"\n🔀 동시 요청 처리 테스트 ({n_concurrent}개)")
        print("=" * 70)
        
        # 텍스트 검색으로 동시 요청
        queries = ["jazz", "rock", "classical", "blues", "pop"] * (n_concurrent // 5)
        
        def make_request(query):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{API_URL}/search/text",
                    params={'query': query, 'top_k': 5},
                    timeout=30
                )
                end_time = time.time()
                return {
                    'success': response.status_code == 200,
                    'time': (end_time - start_time) * 1000
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # 동시 실행
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=n_concurrent) as executor:
            results = list(executor.map(make_request, queries))
        total_time = time.time() - start_time
        
        # 통계
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        print(f"\n📊 동시 요청 테스트 결과:")
        print(f"  총 요청: {len(results)}개")
        print(f"  성공: {len(successful)}개")
        print(f"  실패: {len(failed)}개")
        print(f"  총 소요 시간: {total_time:.2f}초")
        
        if successful:
            response_times = [r['time'] for r in successful]
            print(f"  평균 응답 시간: {np.mean(response_times):.2f}ms")
            print(f"  최대 응답 시간: {np.max(response_times):.2f}ms")
        
        self.test_results['concurrent_tests'] = {
            'n_concurrent': n_concurrent,
            'total_requests': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'total_time': total_time
        }
        
        return results
    
    def test_api_endpoints(self):
        """모든 API 엔드포인트 테스트"""
        print(f"\n🔌 API 엔드포인트 테스트")
        print("=" * 70)
        
        endpoints = [
            ('GET', '/api', 'API 정보'),
            ('GET', '/stats', '통계'),
            ('GET', '/health', '헬스 체크'),
            ('GET', '/metadata/0', '메타데이터 조회'),
        ]
        
        results = []
        
        for method, path, description in endpoints:
            try:
                url = f"{API_URL}{path}"
                response = requests.request(method, url, timeout=5)
                
                status = "✅" if response.status_code == 200 else "❌"
                print(f"  {status} {method:6s} {path:20s} - {description}")
                
                results.append({
                    'endpoint': path,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                })
            except Exception as e:
                print(f"  ❌ {method:6s} {path:20s} - 오류: {e}")
                results.append({
                    'endpoint': path,
                    'success': False,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r.get('success'))
        print(f"\n  총 {len(results)}개 중 {success_count}개 성공")
        
        self.test_results['api_tests'] = results
        
        return results
    
    def create_performance_charts(self, response_times):
        """성능 테스트 결과 차트 생성"""
        print(f"\n📊 성능 차트 생성 중...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # 1. 응답 시간 히스토그램
        ax1.hist(response_times, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
        ax1.axvline(np.mean(response_times), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(response_times):.2f}ms')
        ax1.axvline(np.median(response_times), color='green', linestyle='--',
                   label=f'Median: {np.median(response_times):.2f}ms')
        ax1.set_xlabel('Response Time (ms)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Search Response Time Distribution')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # 2. 응답 시간 박스플롯
        ax2.boxplot(response_times, vert=True)
        ax2.set_ylabel('Response Time (ms)')
        ax2.set_title('Response Time Box Plot')
        ax2.grid(alpha=0.3)
        
        # 통계 표시
        stats_text = f"""
        Mean: {np.mean(response_times):.2f}ms
        Median: {np.median(response_times):.2f}ms
        Min: {np.min(response_times):.2f}ms
        Max: {np.max(response_times):.2f}ms
        Std: {np.std(response_times):.2f}ms
        """
        ax2.text(0.6, 0.95, stats_text, transform=ax2.transAxes,
                verticalalignment='top', fontsize=10, family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        output_path = self.output_dir / 'performance_charts.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 차트 저장: {output_path}")
        
        plt.close()
    
    def save_test_results(self):
        """테스트 결과 저장"""
        print(f"\n💾 테스트 결과 저장 중...")
        
        output_file = self.output_dir / 'test_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 테스트 결과 저장: {output_file}")
    
    def generate_report(self):
        """종합 테스트 리포트 생성"""
        print(f"\n" + "=" * 70)
        print(f"📋 종합 테스트 리포트")
        print(f"=" * 70)
        
        # 품질 테스트
        if self.test_results['quality_tests']:
            quality = self.test_results['quality_tests']
            avg_sim = np.mean([q['similarity'] for q in quality])
            avg_genre = np.mean([q['same_genre_ratio'] for q in quality])
            
            print(f"\n🎯 검색 품질:")
            print(f"  평균 유사도: {avg_sim:.4f}")
            print(f"  같은 장르 비율: {avg_genre*100:.1f}%")
            
            if avg_sim > 0.95:
                print(f"  평가: ⭐⭐⭐ 우수")
            elif avg_sim > 0.85:
                print(f"  평가: ⭐⭐ 양호")
            else:
                print(f"  평가: ⭐ 개선 필요")
        
        # 성능 테스트
        if self.test_results['performance_tests']:
            perf = self.test_results['performance_tests']
            print(f"\n⚡ 검색 성능:")
            print(f"  평균 응답 시간: {perf['mean']:.2f}ms")
            print(f"  중앙값: {perf['median']:.2f}ms")
            print(f"  표준편차: {perf['std']:.2f}ms")
            
            if perf['mean'] < 50:
                print(f"  평가: ⭐⭐⭐ 매우 빠름")
            elif perf['mean'] < 100:
                print(f"  평가: ⭐⭐ 빠름")
            else:
                print(f"  평가: ⭐ 개선 필요")
        
        # API 테스트
        if self.test_results['api_tests']:
            api = self.test_results['api_tests']
            success_count = sum(1 for r in api if r.get('success'))
            print(f"\n🔌 API 엔드포인트:")
            print(f"  성공: {success_count}/{len(api)}개")
            
            if success_count == len(api):
                print(f"  평가: ✅ 모든 API 정상")
            else:
                print(f"  평가: ⚠️  일부 API 오류")
        
        # 동시 요청
        if self.test_results['concurrent_tests']:
            conc = self.test_results['concurrent_tests']
            print(f"\n🔀 동시 요청 처리:")
            print(f"  동시 요청: {conc['n_concurrent']}개")
            print(f"  성공률: {conc['successful']/conc['total_requests']*100:.1f}%")
            print(f"  총 소요 시간: {conc['total_time']:.2f}초")
            
            if conc['successful'] == conc['total_requests']:
                print(f"  평가: ✅ 안정적")
            else:
                print(f"  평가: ⚠️  일부 실패")
        
        print(f"\n" + "=" * 70)
        print(f"✅ 전체 테스트 완료!")
        print(f"=" * 70)

def main():
    """메인 함수"""
    print("🎯 이미지 검색 시스템 통합 테스트")
    print("=" * 70)
    
    tester = SearchSystemTester()
    
    # 1. 서버 상태 확인
    if not tester.check_server():
        return
    
    # 2. API 엔드포인트 테스트
    tester.test_api_endpoints()
    
    # 3. 검색 품질 테스트
    tester.test_search_quality()
    
    # 4. 텍스트 검색 품질 테스트
    tester.test_text_search_quality()
    
    # 5. 검색 속도 테스트
    response_times = tester.test_search_performance(n_queries=50)
    
    # 6. 동시 요청 테스트
    tester.test_concurrent_requests(n_concurrent=10)
    
    # 7. 성능 차트 생성
    if response_times:
        tester.create_performance_charts(response_times)
    
    # 8. 결과 저장
    tester.save_test_results()
    
    # 9. 종합 리포트
    tester.generate_report()
    
    print(f"\n📁 테스트 결과:")
    print(f"  - tests/test_results/test_results.json")
    print(f"  - tests/test_results/performance_charts.png")

if __name__ == "__main__":
    main()

