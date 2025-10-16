#!/usr/bin/env python3
"""
검색 API 테스트 스크립트
"""

import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """헬스 체크"""
    print("\n🏥 헬스 체크...")
    response = requests.get(f"{API_URL}/health")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_stats():
    """통계 조회"""
    print("\n📊 통계 조회...")
    response = requests.get(f"{API_URL}/stats")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_text_search(query="jazz album", top_k=5):
    """텍스트 검색"""
    print(f"\n🔍 텍스트 검색: '{query}'")
    print("=" * 60)
    
    response = requests.post(
        f"{API_URL}/search/text",
        params={"query": query, "top_k": top_k}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 검색 성공!")
        print(f"   검색 시간: {data['query_time_ms']:.2f}ms")
        print(f"   결과 개수: {data['total_results']}개")
        print(f"\n📋 Top-{top_k} 결과:")
        
        for result in data['results']:
            print(f"   {result['rank']}. {result['genre']:15s} | {result['filename'][:40]:40s} | 유사도: {result['similarity']:.4f}")
    else:
        print(f"❌ 검색 실패: {response.status_code}")
        print(response.text)

def test_image_search(image_path, top_k=5):
    """이미지 검색"""
    print(f"\n🖼️  이미지 검색: {image_path}")
    print("=" * 60)
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{API_URL}/search/image",
            files=files,
            params={"top_k": top_k}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 검색 성공!")
        print(f"   검색 시간: {data['query_time_ms']:.2f}ms")
        print(f"   결과 개수: {data['total_results']}개")
        print(f"\n📋 Top-{top_k} 결과:")
        
        for result in data['results']:
            print(f"   {result['rank']}. {result['genre']:15s} | {result['filename'][:40]:40s} | 유사도: {result['similarity']:.4f}")
    else:
        print(f"❌ 검색 실패: {response.status_code}")
        print(response.text)

def test_metadata(image_id=0):
    """메타데이터 조회"""
    print(f"\n📄 메타데이터 조회: ID {image_id}")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/metadata/{image_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 조회 실패: {response.status_code}")

def main():
    """메인 함수"""
    print("🎯 LP 앨범 이미지 검색 API 테스트")
    print("=" * 70)
    
    try:
        # 1. 헬스 체크
        test_health()
        
        # 2. 통계 조회
        test_stats()
        
        # 3. 텍스트 검색 테스트
        test_text_search("jazz album", top_k=5)
        test_text_search("rock music", top_k=5)
        test_text_search("classical piano", top_k=5)
        
        # 4. 메타데이터 조회
        test_metadata(0)
        test_metadata(100)
        
        # 5. 이미지 검색 테스트 (샘플 이미지)
        sample_image = Path("data/raw/discogs")
        genres = [d for d in sample_image.iterdir() if d.is_dir()]
        if genres:
            test_img = list(genres[0].glob('*.jpeg'))[0]
            test_image_search(test_img, top_k=5)
        
        print("\n" + "=" * 70)
        print("✅ 모든 API 테스트 완료!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ API 서버에 연결할 수 없습니다.")
        print("먼저 API 서버를 시작하세요:")
        print("  python3 scripts/run_search_api.py")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main()

