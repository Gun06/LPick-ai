#!/usr/bin/env python3
"""
바운딩 박스 라벨링 도구 실행 스크립트
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """바운딩 박스 라벨링 도구 실행"""
    
    # 도움말 표시
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print("🎯 LP 바운딩 박스 라벨링 도구")
        print("=" * 50)
        print("사용법:")
        print("  python3 run_bbox_labeling.py [데이터디렉토리] [출력디렉토리] [포트]")
        print("")
        print("매개변수:")
        print("  데이터디렉토리    원본 이미지가 있는 디렉토리 (기본값: data/raw/discogs)")
        print("  출력디렉토리      어노테이션을 저장할 디렉토리 (기본값: data/processed)")
        print("  포트            웹 서버 포트 (기본값: 5001)")
        print("")
        print("예시:")
        print("  python3 run_bbox_labeling.py")
        print("  python3 run_bbox_labeling.py data/raw/discogs data/processed 5001")
        print("")
        print("특징:")
        print("  - labelImg 스타일의 웹 기반 바운딩 박스 라벨링")
        print("  - YOLO 형식으로 어노테이션 저장")
        print("  - 4가지 라벨 지원: 앞면, 뒤면, 속지, LP판")
        print("  - 키보드 단축키 지원")
        return
    
    # 현재 디렉토리를 프로젝트 루트로 설정
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🎯 LP 바운딩 박스 라벨링 도구를 시작합니다!")
    print("=" * 60)
    
    # 기본 설정
    data_dir = "data/raw/discogs"
    output_dir = "data/processed"
    port = 5001
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        port = int(sys.argv[3])
    
    print(f"📁 데이터 디렉토리: {data_dir}")
    print(f"📁 출력 디렉토리: {output_dir}")
    print(f"🌐 포트: {port}")
    print("=" * 60)
    
    # 데이터 디렉토리 확인
    if not Path(data_dir).exists():
        print(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
        print("💡 사용법: python run_bbox_labeling.py [데이터디렉토리] [출력디렉토리] [포트]")
        return
    
    # 바운딩 박스 라벨링 서버 실행
    try:
        cmd = [
            sys.executable, "tools/labeling/bbox_labeling_server.py",
            "--data_dir", data_dir,
            "--output_dir", output_dir,
            "--port", str(port)
        ]
        
        print(f"🚀 서버를 시작합니다...")
        print(f"🌐 브라우저에서 http://localhost:{port} 를 열어주세요")
        print("=" * 60)
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 바운딩 박스 라벨링 도구를 종료합니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서버 실행 중 오류가 발생했습니다: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
