#!/usr/bin/env python3
"""
간단한 검색 시스템 테스트
"""

import requests
import json
import time

API_URL = "http://localhost:8000"

def test_all():
    """모든 테스트 실행"""
    print("🎯 LP 앨범 이미지 검색 시스템 테스트")
    print("=" * 70)
    
    results = {
        'tests_passed': 0,
        'tests_failed': 0,
        'details': []
    }
    
    # 1. 헬스 체크
    print("\n1️⃣ 헬스 체크...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json()
        if data['status'] == 'healthy':
            print("   ✅ 서버 정상")
            results['tests_passed'] += 1
            results['details'].append({'test': 'health_check', 'status': 'passed'})
        else:
            print("   ❌ 서버 이상")
            results['tests_failed'] += 1
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        results['tests_failed'] += 1
        return results
    
    # 2. 통계 API
    print("\n2️⃣ 통계 API...")
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        data = response.json()
        print(f"   ✅ 총 이미지: {data['total_images']:,}개")
        print(f"   ✅ 장르: {data['total_genres']}개")
        print(f"   ✅ 검색 속도: {data['search_speed_ms']}ms")
        results['tests_passed'] += 1
        results['details'].append({'test': 'stats_api', 'status': 'passed', 'data': data})
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        results['tests_failed'] += 1
    
    # 3. 텍스트 검색 (간단)
    print("\n3️⃣ 텍스트 검색...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/search/text",
            params={'query': 'jazz album', 'top_k': 5},
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 검색 성공")
            print(f"   ✅ 결과: {data['total_results']}개")
            print(f"   ✅ 응답 시간: {(end_time - start_time) * 1000:.2f}ms")
            print(f"   ✅ API 보고 시간: {data['query_time_ms']:.2f}ms")
            results['tests_passed'] += 1
            results['details'].append({
                'test': 'text_search',
                'status': 'passed',
                'response_time_ms': (end_time - start_time) * 1000
            })
        else:
            print(f"   ❌ 상태 코드: {response.status_code}")
            results['tests_failed'] += 1
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        results['tests_failed'] += 1
    
    # 4. 메타데이터 조회
    print("\n4️⃣ 메타데이터 조회...")
    try:
        response = requests.get(f"{API_URL}/metadata/0", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 조회 성공")
            print(f"   ✅ 장르: {data['metadata']['genre']}")
            results['tests_passed'] += 1
            results['details'].append({'test': 'metadata_api', 'status': 'passed'})
        else:
            print(f"   ❌ 상태 코드: {response.status_code}")
            results['tests_failed'] += 1
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        results['tests_failed'] += 1
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    print(f"✅ 성공: {results['tests_passed']}개")
    print(f"❌ 실패: {results['tests_failed']}개")
    print(f"총 테스트: {results['tests_passed'] + results['tests_failed']}개")
    
    success_rate = results['tests_passed'] / (results['tests_passed'] + results['tests_failed']) * 100
    print(f"\n성공률: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("평가: ⭐⭐⭐ 완벽!")
    elif success_rate >= 75:
        print("평가: ⭐⭐ 양호")
    else:
        print("평가: ⭐ 개선 필요")
    
    print("=" * 70)
    
    # JSON 저장
    with open('tests/test_results/simple_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n💾 결과 저장: tests/test_results/simple_test_results.json")
    
    return results

if __name__ == "__main__":
    import os
    os.makedirs('tests/test_results', exist_ok=True)
    test_all()

