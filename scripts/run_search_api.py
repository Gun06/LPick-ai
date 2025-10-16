#!/usr/bin/env python3
"""
LP 앨범 이미지 검색 API 서버 실행 스크립트
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """API 서버 실행"""
    
    # 도움말
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print("🎯 LP 앨범 이미지 검색 API")
        print("=" * 50)
        print("사용법:")
        print("  python3 run_search_api.py [포트]")
        print("")
        print("매개변수:")
        print("  포트     API 서버 포트 (기본값: 8000)")
        print("")
        print("예시:")
        print("  python3 run_search_api.py")
        print("  python3 run_search_api.py 8080")
        print("")
        print("API 엔드포인트:")
        print("  POST /search/image   - 이미지 업로드 검색")
        print("  POST /search/text    - 텍스트 검색")
        print("  GET  /metadata/{id}  - 메타데이터 조회")
        print("  GET  /image/{id}     - 이미지 파일")
        print("  GET  /stats          - 통계")
        print("")
        print("API 문서:")
        print("  http://localhost:8000/docs")
        return
    
    # 프로젝트 루트로 이동
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 포트 설정
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ 잘못된 포트 번호: {sys.argv[1]}")
            return
    
    print("🚀 LP 앨범 이미지 검색 API 시작")
    print("=" * 70)
    print(f"🌐 서버 주소: http://localhost:{port}")
    print(f"📖 API 문서: http://localhost:{port}/docs")
    print(f"🔍 테스트: http://localhost:{port}")
    print("=" * 70)
    
    # 필요한 파일 확인
    required_files = [
        'data/processed/faiss_index/index_flat_l2.faiss',
        'data/processed/faiss_index/id_to_metadata_mapping.json',
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("\n❌ 필요한 파일이 없습니다:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n먼저 다음 단계를 실행하세요:")
        print("   1. python3 scripts/generate_embeddings.py")
        print("   2. python3 scripts/build_faiss_index.py")
        return
    
    # API 서버 실행
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.api.image_search_api:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 API 서버를 종료합니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서버 실행 중 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()

