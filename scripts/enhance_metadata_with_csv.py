#!/usr/bin/env python3
"""
CSV 파일에서 release_id, title 정보를 읽어서 메타데이터 매핑에 추가하는 스크립트
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

def load_csv_mappings(csv_dir):
    """CSV 파일들을 읽어서 filename -> release_id, title 매핑 생성"""
    print("📂 CSV 파일에서 release_id, title 정보 로드 중...")
    
    csv_dir = Path(csv_dir)
    csv_files = list(csv_dir.glob("discogs_*.csv"))
    
    if not csv_files:
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_dir}")
        return {}
    
    # filename -> (release_id, title) 매핑
    # 같은 파일명이 여러 release_id에 있을 수 있으므로 리스트로 저장
    filename_to_release = defaultdict(list)
    
    for csv_file in tqdm(csv_files, desc="CSV 파일 처리"):
        try:
            df = pd.read_csv(csv_file)
            
            # 필요한 컬럼 확인
            required_cols = ['image_file', 'release_id', 'title']
            if not all(col in df.columns for col in required_cols):
                print(f"⚠️  {csv_file.name}에 필요한 컬럼이 없습니다. 스킵합니다.")
                continue
            
            for _, row in df.iterrows():
                filename = str(row['image_file']).strip()
                release_id = int(row['release_id']) if pd.notna(row['release_id']) else None
                title = str(row['title']).strip() if pd.notna(row['title']) else None
                
                if filename and release_id and title:
                    filename_to_release[filename].append({
                        'release_id': release_id,
                        'title': title
                    })
        
        except Exception as e:
            print(f"❌ {csv_file.name} 처리 중 오류: {e}")
            continue
    
    print(f"✅ {len(filename_to_release):,}개 파일명 매핑 생성 완료")
    return filename_to_release

def enhance_metadata(metadata_path, filename_to_release):
    """메타데이터 매핑에 release_id, title 추가"""
    print(f"\n📝 메타데이터 매핑 강화 중...")
    
    metadata_path = Path(metadata_path)
    
    # 기존 메타데이터 로드
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"   기존 메타데이터: {len(metadata):,}개")
    
    # 각 메타데이터 항목에 release_id, title 추가
    matched_count = 0
    unmatched_count = 0
    
    for idx, info in tqdm(metadata.items(), desc="메타데이터 강화"):
        filename = info.get('filename', '')
        
        if filename in filename_to_release:
            # 매칭된 경우 첫 번째 항목 사용
            release_info = filename_to_release[filename][0]
            info['release_id'] = release_info['release_id']
            info['title'] = release_info['title']
            matched_count += 1
        else:
            # 매칭되지 않은 경우 None
            info['release_id'] = None
            info['title'] = None
            unmatched_count += 1
    
    # 백업 생성
    backup_path = metadata_path.with_suffix('.json.backup')
    print(f"\n💾 백업 생성: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # 강화된 메타데이터 저장
    print(f"💾 강화된 메타데이터 저장: {metadata_path}")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 메타데이터 강화 완료!")
    print(f"   매칭 성공: {matched_count:,}개 ({matched_count/len(metadata)*100:.1f}%)")
    print(f"   매칭 실패: {unmatched_count:,}개 ({unmatched_count/len(metadata)*100:.1f}%)")
    
    return metadata

def main():
    """메인 함수"""
    print("🎯 메타데이터 강화 스크립트")
    print("=" * 70)
    
    # 경로 설정
    csv_dir = Path('data/raw/csv')
    metadata_path = Path('data/processed/faiss_index/id_to_metadata_mapping.json')
    
    # 파일 존재 확인
    if not csv_dir.exists():
        print(f"❌ CSV 디렉토리를 찾을 수 없습니다: {csv_dir}")
        return
    
    if not metadata_path.exists():
        print(f"❌ 메타데이터 파일을 찾을 수 없습니다: {metadata_path}")
        return
    
    # 1. CSV에서 매핑 로드
    filename_to_release = load_csv_mappings(csv_dir)
    
    if not filename_to_release:
        print("❌ CSV 매핑을 생성할 수 없습니다.")
        return
    
    # 2. 메타데이터 강화
    enhanced_metadata = enhance_metadata(metadata_path, filename_to_release)
    
    print("\n" + "=" * 70)
    print("🎉 메타데이터 강화 완료!")
    print(f"📁 강화된 파일: {metadata_path}")
    print(f"💾 백업 파일: {metadata_path.with_suffix('.json.backup')}")

if __name__ == "__main__":
    main()

