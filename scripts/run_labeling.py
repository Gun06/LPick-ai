#!/usr/bin/env python3
"""
LP 레이블링 도구 실행 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from data.scripts.labeling_tool import LPLabelingTool

def main():
    """메인 함수"""
    print("🎵 LP 이미지 레이블링 도구를 시작합니다!")
    print("=" * 50)
    
    # 데이터 디렉토리 설정
    data_dir = "data/raw/discogs"
    output_dir = "data/processed/labeled"
    
    # 디렉토리 존재 확인
    if not Path(data_dir).exists():
        print(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
        print("먼저 LP 이미지 데이터를 다운로드해주세요.")
        return
    
    print(f"📁 데이터 디렉토리: {data_dir}")
    print(f"📁 출력 디렉토리: {output_dir}")
    print()
    print("🎯 레이블링 방법:")
    print("  - 1번 키: 앞면 (Front Cover)")
    print("  - 2번 키: 뒤면 (Back Cover)")
    print("  - 3번 키: 속지 (Inner Sleeve)")
    print("  - S키: 건너뛰기")
    print("  - 저장 버튼: 진행상황 저장")
    print()
    print("🚀 레이블링 도구를 시작합니다...")
    
    try:
        # 레이블링 도구 실행
        app = LPLabelingTool(data_dir, output_dir)
        app.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  레이블링이 중단되었습니다.")
        print("진행상황은 자동으로 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")
        print("문제를 해결한 후 다시 시도해주세요.")

if __name__ == "__main__":
    main()
