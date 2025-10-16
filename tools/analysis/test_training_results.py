#!/usr/bin/env python3
"""
학습 완료 그래프 테스트 스크립트
학습된 모델의 성능을 분석하고 시각화합니다.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from PIL import Image
import torchvision.transforms as transforms
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_training_history(history_path):
    """학습 히스토리 로드"""
    with open(history_path, 'r', encoding='utf-8') as f:
        history = json.load(f)
    return history

def plot_training_history(history, save_path=None):
    """학습 히스토리 시각화"""
    epochs = range(1, len(history['train_losses']) + 1)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('LP Classifier Training Results', fontsize=16, fontweight='bold')
    
    # Loss 그래프
    ax1.plot(epochs, history['train_losses'], 'b-', label='Training Loss', linewidth=2, marker='o')
    ax1.plot(epochs, history['val_losses'], 'r-', label='Validation Loss', linewidth=2, marker='s')
    ax1.set_title('Training and Validation Loss', fontsize=14)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Accuracy 그래프
    ax2.plot(epochs, history['train_accs'], 'b-', label='Training Accuracy', linewidth=2, marker='o')
    ax2.plot(epochs, history['val_accs'], 'r-', label='Validation Accuracy', linewidth=2, marker='s')
    ax2.set_title('Training and Validation Accuracy', fontsize=14)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 최종 성능 요약
    ax3.text(0.1, 0.8, f"Best Validation Accuracy: {history['best_val_acc']:.2f}%", 
             fontsize=12, transform=ax3.transAxes, fontweight='bold')
    ax3.text(0.1, 0.6, f"Test Accuracy: {history['test_acc']:.2f}%", 
             fontsize=12, transform=ax3.transAxes, fontweight='bold')
    ax3.text(0.1, 0.4, f"Test Loss: {history['test_loss']:.4f}", 
             fontsize=12, transform=ax3.transAxes, fontweight='bold')
    ax3.text(0.1, 0.2, f"Epochs Trained: {history['epochs_trained']}", 
             fontsize=12, transform=ax3.transAxes, fontweight='bold')
    ax3.set_title('Final Performance Summary', fontsize=14)
    ax3.axis('off')
    
    # 학습 진행률
    progress = history['epochs_trained']
    ax4.bar(['Epochs Trained'], [progress], color='skyblue', alpha=0.7)
    ax4.set_title('Training Progress', fontsize=14)
    ax4.set_ylabel('Number of Epochs')
    ax4.set_ylim(0, max(10, progress + 2))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 그래프가 저장되었습니다: {save_path}")
    
    plt.show()

def analyze_training_performance(history):
    """학습 성능 분석"""
    print("🎯 LP Classifier 학습 성능 분석")
    print("=" * 50)
    
    # 기본 통계
    print(f"📈 학습 에포크 수: {history['epochs_trained']}")
    print(f"🏆 최고 검증 정확도: {history['best_val_acc']:.2f}%")
    print(f"🧪 테스트 정확도: {history['test_acc']:.2f}%")
    print(f"📉 테스트 손실: {history['test_loss']:.4f}")
    
    # 학습 진행 분석
    train_losses = history['train_losses']
    val_losses = history['val_losses']
    train_accs = history['train_accs']
    val_accs = history['val_accs']
    
    print(f"\n📊 학습 진행 분석:")
    print(f"  - 초기 훈련 손실: {train_losses[0]:.4f}")
    print(f"  - 최종 훈련 손실: {train_losses[-1]:.4f}")
    print(f"  - 손실 감소율: {((train_losses[0] - train_losses[-1]) / train_losses[0] * 100):.1f}%")
    
    print(f"  - 초기 훈련 정확도: {train_accs[0]:.2f}%")
    print(f"  - 최종 훈련 정확도: {train_accs[-1]:.2f}%")
    print(f"  - 정확도 향상률: {((train_accs[-1] - train_accs[0]) / train_accs[0] * 100):.1f}%")
    
    # 과적합 분석
    if len(val_losses) > 1:
        val_loss_trend = val_losses[-1] - val_losses[0]
        train_loss_trend = train_losses[-1] - train_losses[0]
        
        print(f"\n🔍 과적합 분석:")
        if val_loss_trend > train_loss_trend:
            print("  ⚠️  과적합 가능성이 있습니다 (검증 손실이 훈련 손실보다 많이 증가)")
        else:
            print("  ✅ 과적합 없음 (검증 손실이 안정적)")
    
    # 성능 평가
    print(f"\n🎯 성능 평가:")
    if history['test_acc'] > 80:
        print("  🌟 우수한 성능!")
    elif history['test_acc'] > 60:
        print("  👍 양호한 성능")
    elif history['test_acc'] > 40:
        print("  ⚠️  개선이 필요합니다")
    else:
        print("  ❌ 성능이 매우 낮습니다. 모델 재설계가 필요합니다.")
    
    return {
        'epochs': history['epochs_trained'],
        'best_val_acc': history['best_val_acc'],
        'test_acc': history['test_acc'],
        'test_loss': history['test_loss'],
        'train_loss_improvement': ((train_losses[0] - train_losses[-1]) / train_losses[0] * 100),
        'train_acc_improvement': ((train_accs[-1] - train_accs[0]) / train_accs[0] * 100)
    }

def create_detailed_analysis(history, output_dir):
    """상세 분석 리포트 생성"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 1. 학습 히스토리 그래프
    plot_training_history(history, output_path / "detailed_training_analysis.png")
    
    # 2. 성능 분석
    analysis = analyze_training_performance(history)
    
    # 3. 개선 제안
    print(f"\n💡 개선 제안:")
    if analysis['test_acc'] < 50:
        print("  - 더 많은 데이터 수집 필요")
        print("  - 데이터 증강(augmentation) 적용")
        print("  - 모델 아키텍처 개선")
        print("  - 하이퍼파라미터 튜닝")
    elif analysis['test_acc'] < 80:
        print("  - 정규화 기법 적용 (Dropout, BatchNorm 등)")
        print("  - 학습률 스케줄링")
        print("  - 앙상블 모델 고려")
    else:
        print("  - 모델이 잘 학습되었습니다!")
        print("  - 실제 데이터로 추가 검증 필요")
    
    return analysis

def main():
    """메인 함수"""
    # 경로 설정
    model_dir = Path("models/saved_models/lp_classifier")
    history_path = model_dir / "training_history.json"
    output_dir = "models/analysis_results"
    
    print("🎯 LP Classifier 학습 완료 그래프 테스트")
    print("=" * 60)
    
    # 학습 히스토리 로드
    if not history_path.exists():
        print(f"❌ 학습 히스토리 파일을 찾을 수 없습니다: {history_path}")
        return
    
    print(f"📁 학습 히스토리 로드: {history_path}")
    history = load_training_history(history_path)
    
    # 상세 분석 실행
    analysis = create_detailed_analysis(history, output_dir)
    
    print(f"\n✅ 분석 완료! 결과가 {output_dir} 폴더에 저장되었습니다.")
    print("=" * 60)

if __name__ == "__main__":
    main()
