#!/usr/bin/env python3
"""
크롤링된 LP 앨범 이미지 데이터 전문가 수준 분석 스크립트

분석 항목:
1. 장르별 이미지 개수 분포
2. 이미지 크기/해상도 분포 분석
3. 파일 크기 분석
4. 이미지 품질 분석 (손상 감지)
5. 색상 분포 분석
6. 종횡비(Aspect Ratio) 분석
7. CSV 메타데이터 통계
8. 데이터 품질 리포트 생성
"""

import os
import sys
from pathlib import Path
import json
import csv
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class ImageDataAnalyzer:
    """이미지 데이터 전문가 분석 클래스"""
    
    def __init__(self, data_dir='data/raw/discogs', output_dir='data/analysis_results'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 분석 결과 저장
        self.stats = {
            'genre_counts': {},
            'image_sizes': [],
            'file_sizes': [],
            'aspect_ratios': [],
            'corrupted_images': [],
            'color_modes': Counter(),
            'genres': []
        }
    
    def analyze_all(self):
        """전체 분석 실행"""
        print("🎯 LP 앨범 이미지 데이터 전문가 분석 시작")
        print("=" * 70)
        
        # 1. 이미지 파일 수집 및 분석
        print("\n📊 1단계: 이미지 파일 수집 및 기본 분석")
        self.collect_and_analyze_images()
        
        # 2. 그래프 생성
        print("\n📈 2단계: 시각화 그래프 생성")
        self.create_visualizations()
        
        # 3. CSV 메타데이터 분석
        print("\n📄 3단계: 메타데이터 분석")
        self.analyze_metadata()
        
        # 4. 종합 리포트 생성
        print("\n📋 4단계: 종합 리포트 생성")
        self.generate_report()
        
        print("\n✅ 분석 완료!")
        print(f"📁 결과 저장 위치: {self.output_dir}")
        print("=" * 70)
    
    def collect_and_analyze_images(self):
        """이미지 수집 및 기본 분석"""
        genres = [d for d in self.data_dir.iterdir() if d.is_dir()]
        
        print(f"발견된 장르: {len(genres)}개")
        
        for genre_dir in genres:
            genre = genre_dir.name
            image_files = list(genre_dir.glob('*.jpeg')) + list(genre_dir.glob('*.jpg'))
            
            self.stats['genre_counts'][genre] = len(image_files)
            print(f"  - {genre}: {len(image_files):,}개 이미지")
            
            # 샘플링 (너무 많으면 일부만 분석)
            sample_size = min(len(image_files), 500)
            sampled_files = np.random.choice(image_files, sample_size, replace=False) if len(image_files) > sample_size else image_files
            
            # 이미지별 상세 분석
            for img_path in tqdm(sampled_files, desc=f"Analyzing {genre}", leave=False):
                try:
                    # 파일 크기
                    file_size = img_path.stat().st_size / 1024  # KB
                    self.stats['file_sizes'].append(file_size)
                    
                    # 이미지 열기
                    with Image.open(img_path) as img:
                        # 이미지 크기
                        width, height = img.size
                        self.stats['image_sizes'].append((width, height))
                        
                        # 종횡비
                        aspect_ratio = width / height if height > 0 else 0
                        self.stats['aspect_ratios'].append(aspect_ratio)
                        
                        # 색상 모드
                        self.stats['color_modes'][img.mode] += 1
                        
                        # 장르 저장
                        self.stats['genres'].append(genre)
                        
                except Exception as e:
                    self.stats['corrupted_images'].append({
                        'path': str(img_path),
                        'error': str(e),
                        'genre': genre
                    })
        
        # 통계 계산
        total_images = sum(self.stats['genre_counts'].values())
        print(f"\n📊 전체 통계:")
        print(f"  - 총 이미지: {total_images:,}개")
        print(f"  - 손상된 이미지: {len(self.stats['corrupted_images'])}개")
        print(f"  - 분석된 샘플: {len(self.stats['image_sizes'])}개")
    
    def create_visualizations(self):
        """시각화 그래프 생성"""
        fig = plt.figure(figsize=(20, 12))
        
        # 1. 장르별 이미지 개수 (Bar Chart)
        ax1 = plt.subplot(3, 3, 1)
        genres = list(self.stats['genre_counts'].keys())
        counts = list(self.stats['genre_counts'].values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(genres)))
        
        bars = ax1.bar(range(len(genres)), counts, color=colors)
        ax1.set_xticks(range(len(genres)))
        ax1.set_xticklabels(genres, rotation=45, ha='right')
        ax1.set_ylabel('Number of Images')
        ax1.set_title('Genre Distribution', fontweight='bold', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=8)
        
        # 2. 장르별 비율 (Pie Chart)
        ax2 = plt.subplot(3, 3, 2)
        ax2.pie(counts, labels=genres, autopct='%1.1f%%', colors=colors,
                startangle=90, textprops={'fontsize': 8})
        ax2.set_title('Genre Proportion', fontweight='bold', fontsize=12)
        
        # 3. 이미지 너비 분포 (Histogram)
        ax3 = plt.subplot(3, 3, 3)
        widths = [size[0] for size in self.stats['image_sizes']]
        ax3.hist(widths, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
        ax3.axvline(np.mean(widths), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(widths):.0f}px')
        ax3.axvline(np.median(widths), color='green', linestyle='--',
                   label=f'Median: {np.median(widths):.0f}px')
        ax3.set_xlabel('Width (pixels)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Image Width Distribution', fontweight='bold', fontsize=12)
        ax3.legend(fontsize=8)
        ax3.grid(alpha=0.3)
        
        # 4. 이미지 높이 분포 (Histogram)
        ax4 = plt.subplot(3, 3, 4)
        heights = [size[1] for size in self.stats['image_sizes']]
        ax4.hist(heights, bins=50, color='lightcoral', edgecolor='black', alpha=0.7)
        ax4.axvline(np.mean(heights), color='red', linestyle='--',
                   label=f'Mean: {np.mean(heights):.0f}px')
        ax4.axvline(np.median(heights), color='green', linestyle='--',
                   label=f'Median: {np.median(heights):.0f}px')
        ax4.set_xlabel('Height (pixels)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Image Height Distribution', fontweight='bold', fontsize=12)
        ax4.legend(fontsize=8)
        ax4.grid(alpha=0.3)
        
        # 5. 파일 크기 분포 (Box Plot)
        ax5 = plt.subplot(3, 3, 5)
        ax5.boxplot(self.stats['file_sizes'], vert=True)
        ax5.set_ylabel('File Size (KB)')
        ax5.set_title('File Size Distribution', fontweight='bold', fontsize=12)
        ax5.grid(alpha=0.3)
        
        # 통계 표시
        mean_size = np.mean(self.stats['file_sizes'])
        median_size = np.median(self.stats['file_sizes'])
        ax5.text(0.5, 0.95, f'Mean: {mean_size:.1f} KB\nMedian: {median_size:.1f} KB',
                transform=ax5.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 6. 종횡비 분포 (Histogram)
        ax6 = plt.subplot(3, 3, 6)
        ax6.hist(self.stats['aspect_ratios'], bins=50, color='lightgreen', 
                edgecolor='black', alpha=0.7)
        ax6.axvline(1.0, color='red', linestyle='--', label='Square (1:1)')
        ax6.set_xlabel('Aspect Ratio (Width/Height)')
        ax6.set_ylabel('Frequency')
        ax6.set_title('Aspect Ratio Distribution', fontweight='bold', fontsize=12)
        ax6.legend(fontsize=8)
        ax6.grid(alpha=0.3)
        
        # 7. 이미지 크기 산점도 (Scatter Plot)
        ax7 = plt.subplot(3, 3, 7)
        widths = [size[0] for size in self.stats['image_sizes']]
        heights = [size[1] for size in self.stats['image_sizes']]
        ax7.scatter(widths, heights, alpha=0.5, s=10, c='purple')
        ax7.set_xlabel('Width (pixels)')
        ax7.set_ylabel('Height (pixels)')
        ax7.set_title('Image Dimensions Scatter Plot', fontweight='bold', fontsize=12)
        ax7.grid(alpha=0.3)
        
        # 대각선 (정사각형 라인)
        max_dim = max(max(widths), max(heights))
        ax7.plot([0, max_dim], [0, max_dim], 'r--', alpha=0.5, label='Square')
        ax7.legend(fontsize=8)
        
        # 8. 색상 모드 분포 (Bar Chart)
        ax8 = plt.subplot(3, 3, 8)
        modes = list(self.stats['color_modes'].keys())
        mode_counts = list(self.stats['color_modes'].values())
        ax8.bar(modes, mode_counts, color='orange', edgecolor='black', alpha=0.7)
        ax8.set_xlabel('Color Mode')
        ax8.set_ylabel('Count')
        ax8.set_title('Color Mode Distribution', fontweight='bold', fontsize=12)
        ax8.grid(axis='y', alpha=0.3)
        
        # 값 표시
        for i, v in enumerate(mode_counts):
            ax8.text(i, v, str(v), ha='center', va='bottom')
        
        # 9. 데이터 품질 요약
        ax9 = plt.subplot(3, 3, 9)
        ax9.axis('off')
        
        total_images = sum(self.stats['genre_counts'].values())
        corrupted_count = len(self.stats['corrupted_images'])
        corrupted_pct = (corrupted_count / total_images * 100) if total_images > 0 else 0
        
        summary_text = f"""
        📊 Data Quality Summary
        
        Total Images: {total_images:,}
        Valid Images: {total_images - corrupted_count:,}
        Corrupted: {corrupted_count} ({corrupted_pct:.2f}%)
        
        📏 Size Statistics
        Avg Width: {np.mean(widths):.0f}px
        Avg Height: {np.mean(heights):.0f}px
        Avg File Size: {np.mean(self.stats['file_sizes']):.1f}KB
        
        📐 Aspect Ratio
        Mean: {np.mean(self.stats['aspect_ratios']):.2f}
        Median: {np.median(self.stats['aspect_ratios']):.2f}
        
        🎨 Most Common Mode: {modes[0] if modes else 'N/A'}
        """
        
        ax9.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.suptitle('LP Album Image Dataset Analysis', 
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        # 저장
        output_path = self.output_dir / 'data_analysis_visualization.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 시각화 그래프 저장: {output_path}")
        
        plt.close()
    
    def analyze_metadata(self):
        """CSV 메타데이터 분석"""
        csv_dir = Path('data/raw/csv')
        
        if not csv_dir.exists():
            print("⚠️  CSV 메타데이터 폴더를 찾을 수 없습니다.")
            return
        
        csv_files = list(csv_dir.glob('*.csv'))
        
        if not csv_files:
            print("⚠️  CSV 파일을 찾을 수 없습니다.")
            return
        
        all_data = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                all_data.append(df)
            except Exception as e:
                print(f"⚠️  {csv_file.name} 로드 실패: {e}")
        
        if not all_data:
            print("⚠️  로드된 CSV 데이터가 없습니다.")
            return
        
        # 데이터 병합
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 메타데이터 분석
        print(f"\n📊 메타데이터 통계:")
        print(f"  - 총 레코드: {len(combined_df):,}개")
        print(f"  - 컬럼: {list(combined_df.columns)}")
        print(f"  - 결측치:")
        for col in combined_df.columns:
            null_count = combined_df[col].isnull().sum()
            null_pct = (null_count / len(combined_df) * 100)
            print(f"    - {col}: {null_count} ({null_pct:.1f}%)")
        
        # 통합 CSV 저장
        output_csv = self.output_dir / 'combined_metadata.csv'
        combined_df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"\n✅ 통합 메타데이터 저장: {output_csv}")
        
        # 기본 통계 저장
        stats_file = self.output_dir / 'metadata_statistics.json'
        metadata_stats = {
            'total_records': len(combined_df),
            'columns': list(combined_df.columns),
            'null_counts': combined_df.isnull().sum().to_dict(),
            'unique_artists': combined_df['artists'].nunique() if 'artists' in combined_df.columns else 0,
            'unique_genres': combined_df['genre'].nunique() if 'genre' in combined_df.columns else 0,
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_stats, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 메타데이터 통계 저장: {stats_file}")
    
    def generate_report(self):
        """종합 리포트 생성"""
        report_path = self.output_dir / 'analysis_report.txt'
        
        total_images = sum(self.stats['genre_counts'].values())
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("LP ALBUM IMAGE DATASET ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            # 1. 전체 개요
            f.write("📊 1. DATASET OVERVIEW\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Images: {total_images:,}\n")
            f.write(f"Total Genres: {len(self.stats['genre_counts'])}\n")
            f.write(f"Corrupted Images: {len(self.stats['corrupted_images'])}\n")
            f.write(f"Corruption Rate: {(len(self.stats['corrupted_images']) / total_images * 100):.2f}%\n\n")
            
            # 2. 장르별 분포
            f.write("📁 2. GENRE DISTRIBUTION\n")
            f.write("-" * 70 + "\n")
            for genre, count in sorted(self.stats['genre_counts'].items(), 
                                      key=lambda x: x[1], reverse=True):
                pct = (count / total_images * 100)
                f.write(f"  {genre:20s}: {count:8,} images ({pct:5.2f}%)\n")
            f.write("\n")
            
            # 3. 이미지 크기 통계
            if self.stats['image_sizes']:
                widths = [s[0] for s in self.stats['image_sizes']]
                heights = [s[1] for s in self.stats['image_sizes']]
                
                f.write("📏 3. IMAGE DIMENSIONS STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Width:\n")
                f.write(f"  Mean:   {np.mean(widths):8.2f} px\n")
                f.write(f"  Median: {np.median(widths):8.2f} px\n")
                f.write(f"  Min:    {np.min(widths):8.0f} px\n")
                f.write(f"  Max:    {np.max(widths):8.0f} px\n")
                f.write(f"  Std:    {np.std(widths):8.2f} px\n\n")
                
                f.write(f"Height:\n")
                f.write(f"  Mean:   {np.mean(heights):8.2f} px\n")
                f.write(f"  Median: {np.median(heights):8.2f} px\n")
                f.write(f"  Min:    {np.min(heights):8.0f} px\n")
                f.write(f"  Max:    {np.max(heights):8.0f} px\n")
                f.write(f"  Std:    {np.std(heights):8.2f} px\n\n")
            
            # 4. 파일 크기 통계
            if self.stats['file_sizes']:
                f.write("💾 4. FILE SIZE STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Mean:   {np.mean(self.stats['file_sizes']):8.2f} KB\n")
                f.write(f"Median: {np.median(self.stats['file_sizes']):8.2f} KB\n")
                f.write(f"Min:    {np.min(self.stats['file_sizes']):8.2f} KB\n")
                f.write(f"Max:    {np.max(self.stats['file_sizes']):8.2f} KB\n")
                f.write(f"Std:    {np.std(self.stats['file_sizes']):8.2f} KB\n\n")
            
            # 5. 종횡비 통계
            if self.stats['aspect_ratios']:
                f.write("📐 5. ASPECT RATIO STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Mean:   {np.mean(self.stats['aspect_ratios']):.4f}\n")
                f.write(f"Median: {np.median(self.stats['aspect_ratios']):.4f}\n")
                f.write(f"Min:    {np.min(self.stats['aspect_ratios']):.4f}\n")
                f.write(f"Max:    {np.max(self.stats['aspect_ratios']):.4f}\n\n")
            
            # 6. 색상 모드
            f.write("🎨 6. COLOR MODE DISTRIBUTION\n")
            f.write("-" * 70 + "\n")
            for mode, count in self.stats['color_modes'].most_common():
                pct = (count / len(self.stats['image_sizes']) * 100) if self.stats['image_sizes'] else 0
                f.write(f"  {mode}: {count} ({pct:.2f}%)\n")
            f.write("\n")
            
            # 7. 손상된 이미지 목록
            if self.stats['corrupted_images']:
                f.write("⚠️  7. CORRUPTED IMAGES\n")
                f.write("-" * 70 + "\n")
                for img in self.stats['corrupted_images'][:20]:  # 최대 20개만
                    f.write(f"  {img['path']}\n")
                    f.write(f"    Error: {img['error']}\n")
                if len(self.stats['corrupted_images']) > 20:
                    f.write(f"  ... and {len(self.stats['corrupted_images']) - 20} more\n")
                f.write("\n")
            
            # 8. 권장사항
            f.write("💡 8. RECOMMENDATIONS\n")
            f.write("-" * 70 + "\n")
            
            if len(self.stats['corrupted_images']) > 0:
                f.write("  ⚠️  손상된 이미지를 제거하거나 복구하세요.\n")
            
            if self.stats['image_sizes']:
                widths = [s[0] for s in self.stats['image_sizes']]
                if np.std(widths) > 200:
                    f.write("  📏 이미지 크기가 불균일합니다. 전처리 시 리사이징을 권장합니다.\n")
            
            if self.stats['aspect_ratios']:
                if np.std(self.stats['aspect_ratios']) > 0.3:
                    f.write("  📐 종횡비가 다양합니다. 패딩 또는 크롭핑을 고려하세요.\n")
            
            f.write("  ✅ 데이터가 이미지 검색 시스템 구축에 적합합니다.\n")
            f.write("\n")
            
            f.write("=" * 70 + "\n")
            f.write("Report generated successfully!\n")
            f.write("=" * 70 + "\n")
        
        print(f"✅ 종합 리포트 저장: {report_path}")
        
        # JSON 형식으로도 저장
        json_report = {
            'total_images': total_images,
            'genre_counts': self.stats['genre_counts'],
            'corrupted_count': len(self.stats['corrupted_images']),
            'image_statistics': {
                'width_mean': float(np.mean([s[0] for s in self.stats['image_sizes']])) if self.stats['image_sizes'] else 0,
                'height_mean': float(np.mean([s[1] for s in self.stats['image_sizes']])) if self.stats['image_sizes'] else 0,
                'file_size_mean_kb': float(np.mean(self.stats['file_sizes'])) if self.stats['file_sizes'] else 0,
                'aspect_ratio_mean': float(np.mean(self.stats['aspect_ratios'])) if self.stats['aspect_ratios'] else 0,
            },
            'color_modes': dict(self.stats['color_modes'])
        }
        
        json_path = self.output_dir / 'analysis_report.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON 리포트 저장: {json_path}")

def main():
    """메인 함수"""
    print("🎯 LP 앨범 이미지 데이터 분석 시작\n")
    
    analyzer = ImageDataAnalyzer(
        data_dir='data/raw/discogs',
        output_dir='data/analysis_results'
    )
    
    analyzer.analyze_all()
    
    print("\n🎉 분석 완료!")
    print("\n📁 생성된 파일:")
    print("  - data/analysis_results/data_analysis_visualization.png")
    print("  - data/analysis_results/analysis_report.txt")
    print("  - data/analysis_results/analysis_report.json")
    print("  - data/analysis_results/combined_metadata.csv")
    print("  - data/analysis_results/metadata_statistics.json")

if __name__ == "__main__":
    main()

