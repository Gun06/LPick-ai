#!/usr/bin/env python3
"""
LP 이미지 분류 전체 파이프라인 실행 스크립트
1. 레이블링 도구 실행
2. 레이블링된 데이터 전처리
3. 텍스트 추출
4. 모델 훈련
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

def run_command(command, description):
    """명령어 실행"""
    print(f"\n🔄 {description}...")
    print(f"실행 명령: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ 성공!")
        if result.stdout:
            print("출력:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {e}")
        if e.stderr:
            print("오류:", e.stderr)
        return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='LP 이미지 분류 전체 파이프라인')
    parser.add_argument('--skip_labeling', action='store_true', help='레이블링 단계 건너뛰기')
    parser.add_argument('--skip_text_extraction', action='store_true', help='텍스트 추출 단계 건너뛰기')
    parser.add_argument('--skip_training', action='store_true', help='모델 훈련 단계 건너뛰기')
    parser.add_argument('--data_dir', default='data/raw/discogs', help='원본 데이터 디렉토리')
    parser.add_argument('--epochs', type=int, default=20, help='훈련 에포크 수')
    parser.add_argument('--batch_size', type=int, default=16, help='배치 크기')
    
    args = parser.parse_args()
    
    print("🎵 LP 이미지 분류 AI 파이프라인을 시작합니다!")
    print("=" * 60)
    
    # 1. 레이블링 도구 실행
    if not args.skip_labeling:
        print("\n📝 1단계: LP 이미지 레이블링")
        print("=" * 40)
        
        if not Path(args.data_dir).exists():
            print(f"❌ 데이터 디렉토리를 찾을 수 없습니다: {args.data_dir}")
            print("먼저 LP 이미지 데이터를 다운로드해주세요.")
            return
        
        print("레이블링 도구를 실행합니다...")
        print("레이블링이 완료되면 이 스크립트를 다시 실행해주세요.")
        
        # 레이블링 도구 실행
        from data.scripts.labeling_tool import LPLabelingTool
        app = LPLabelingTool(args.data_dir, "data/processed/labeled")
        app.run()
        
        print("\n레이블링이 완료되었습니다. 다음 단계를 진행합니다...")
    
    # 2. 레이블링된 데이터 전처리
    print("\n📊 2단계: 레이블링된 데이터 전처리")
    print("=" * 40)
    
    if not Path("data/processed/labeled").exists():
        print("❌ 레이블링된 데이터를 찾을 수 없습니다.")
        print("먼저 레이블링을 완료해주세요.")
        return
    
    success = run_command(
        "python data/scripts/prepare_labeled_data.py --labeled_dir data/processed/labeled --output_dir data/processed/dataset",
        "레이블링된 데이터 전처리"
    )
    
    if not success:
        print("❌ 데이터 전처리에 실패했습니다.")
        return
    
    # 3. 텍스트 추출
    if not args.skip_text_extraction:
        print("\n📄 3단계: LP 이미지 텍스트 추출")
        print("=" * 40)
        
        # 샘플 이미지에서 텍스트 추출 테스트
        success = run_command(
            "python src/utils/ocr_utils.py --image_dir data/processed/dataset/train --output data/processed/extracted_text.json --method tesseract",
            "LP 이미지 텍스트 추출"
        )
        
        if not success:
            print("⚠️  텍스트 추출에 실패했지만 계속 진행합니다.")
    
    # 4. 모델 훈련
    if not args.skip_training:
        print("\n🤖 4단계: LP 분류 모델 훈련")
        print("=" * 40)
        
        if not Path("data/processed/dataset").exists():
            print("❌ 전처리된 데이터셋을 찾을 수 없습니다.")
            return
        
        success = run_command(
            f"python models/scripts/train_lp_classifier.py --data_dir data/processed/dataset --model_dir models/saved_models/lp_classifier --epochs {args.epochs} --batch_size {args.batch_size}",
            "LP 분류 모델 훈련"
        )
        
        if not success:
            print("❌ 모델 훈련에 실패했습니다.")
            return
    
    print("\n🎉 전체 파이프라인이 완료되었습니다!")
    print("=" * 60)
    print("📁 결과 파일들:")
    print("  - 레이블링된 데이터: data/processed/labeled/")
    print("  - 전처리된 데이터셋: data/processed/dataset/")
    print("  - 훈련된 모델: models/saved_models/lp_classifier/")
    print("  - 추출된 텍스트: data/processed/extracted_text.json")
    print()
    print("🚀 이제 LP 이미지 분류 모델을 사용할 수 있습니다!")

if __name__ == "__main__":
    main()
