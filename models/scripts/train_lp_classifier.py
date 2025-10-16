#!/usr/bin/env python3
"""
LP 이미지 분류 모델 훈련 스크립트
앞면(front), 뒤면(back), 속지(inner) 분류를 위한 모델 훈련
"""

import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
import pandas as pd
from pathlib import Path
from PIL import Image
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import argparse
from datetime import datetime

class LPDataset(Dataset):
    """LP 이미지 데이터셋 클래스"""
    
    def __init__(self, data_dir: str, split: str, transform=None):
        self.data_dir = Path(data_dir)
        self.split = split
        self.transform = transform
        
        # 메타데이터 로드
        metadata_file = self.data_dir / split / f'{split}_metadata.csv'
        if not metadata_file.exists():
            raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {metadata_file}")
        
        self.metadata = pd.read_csv(metadata_file)
        # 실제 데이터에서 레이블 매핑 생성
        unique_labels = sorted(self.metadata['label'].unique())
        self.label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
        self.idx_to_label = {idx: label for label, idx in self.label_to_idx.items()}
        
    def __len__(self):
        return len(self.metadata)
    
    def __getitem__(self, idx):
        row = self.metadata.iloc[idx]
        
        # 이미지 로드
        image_path = self.data_dir / self.split / row['label'] / row['filename']
        image = Image.open(image_path).convert('RGB')
        
        # 변환 적용
        if self.transform:
            image = self.transform(image)
        
        # 레이블 인코딩
        label = self.label_to_idx[row['label']]
        
        return image, label

class LPClassifier(nn.Module):
    """LP 이미지 분류 모델"""
    
    def __init__(self, num_classes=4, pretrained=True):
        super(LPClassifier, self).__init__()
        
        # ResNet50 백본 사용
        self.backbone = models.resnet50(pretrained=pretrained)
        
        # 마지막 분류 레이어 수정
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)

class LPModelTrainer:
    """LP 모델 훈련 클래스"""
    
    def __init__(self, data_dir: str, model_dir: str, device: str = None):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 디바이스 설정
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"사용 디바이스: {self.device}")
        
        # 데이터 변환 설정
        self.train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def create_data_loaders(self, batch_size=32, num_workers=4):
        """데이터 로더 생성"""
        # 데이터셋 생성
        train_dataset = LPDataset(self.data_dir, 'train', self.train_transform)
        val_dataset = LPDataset(self.data_dir, 'val', self.val_transform)
        test_dataset = LPDataset(self.data_dir, 'test', self.val_transform)
        
        # 클래스 수 확인
        num_classes = len(train_dataset.label_to_idx)
        print(f"데이터셋에서 발견된 클래스 수: {num_classes}")
        print(f"클래스 매핑: {train_dataset.label_to_idx}")
        
        # 데이터 로더 생성
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True, 
            num_workers=num_workers, pin_memory=True
        )
        val_loader = DataLoader(
            val_dataset, batch_size=batch_size, shuffle=False, 
            num_workers=num_workers, pin_memory=True
        )
        test_loader = DataLoader(
            test_dataset, batch_size=batch_size, shuffle=False, 
            num_workers=num_workers, pin_memory=True
        )
        
        return train_loader, val_loader, test_loader, num_classes
    
    def train_epoch(self, model, train_loader, optimizer, criterion):
        """한 에포크 훈련"""
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        pbar = tqdm(train_loader, desc="Training")
        for images, labels in pbar:
            images, labels = images.to(self.device), labels.to(self.device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            pbar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100 * correct / total:.2f}%'
            })
        
        epoch_loss = running_loss / len(train_loader)
        epoch_acc = 100 * correct / total
        
        return epoch_loss, epoch_acc
    
    def validate_epoch(self, model, val_loader, criterion):
        """검증 에포크"""
        model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc="Validation"):
                images, labels = images.to(self.device), labels.to(self.device)
                
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        epoch_loss = running_loss / len(val_loader)
        epoch_acc = 100 * correct / total
        
        return epoch_loss, epoch_acc
    
    def train(self, epochs=50, batch_size=32, learning_rate=0.001, patience=10):
        """모델 훈련"""
        # 데이터 로더 생성
        train_loader, val_loader, test_loader, num_classes = self.create_data_loaders(batch_size)
        
        # 모델 생성
        model = LPClassifier(num_classes=num_classes, pretrained=True)
        model = model.to(self.device)
        
        # 손실 함수 및 옵티마이저
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
        
        # 훈련 기록
        train_losses = []
        val_losses = []
        train_accs = []
        val_accs = []
        
        best_val_acc = 0
        patience_counter = 0
        
        print("훈련 시작...")
        for epoch in range(epochs):
            print(f"\nEpoch {epoch+1}/{epochs}")
            print("-" * 50)
            
            # 훈련
            train_loss, train_acc = self.train_epoch(model, train_loader, optimizer, criterion)
            
            # 검증
            val_loss, val_acc = self.validate_epoch(model, val_loader, criterion)
            
            # 기록
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            train_accs.append(train_acc)
            val_accs.append(val_acc)
            
            # 스케줄러 업데이트
            scheduler.step(val_loss)
            
            print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            print(f"Learning Rate: {optimizer.param_groups[0]['lr']:.6f}")
            
            # 최고 성능 모델 저장
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                
                # 모델 저장
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_acc': val_acc,
                    'val_loss': val_loss
                }, self.model_dir / 'best_model.pth')
                
                print(f"새로운 최고 성능! Val Acc: {val_acc:.2f}%")
            else:
                patience_counter += 1
            
            # 조기 종료
            if patience_counter >= patience:
                print(f"조기 종료: {patience} 에포크 동안 개선 없음")
                break
        
        # 훈련 완료 후 최고 모델 로드
        checkpoint = torch.load(self.model_dir / 'best_model.pth')
        model.load_state_dict(checkpoint['model_state_dict'])
        
        # 테스트 평가
        test_loss, test_acc = self.validate_epoch(model, test_loader, criterion)
        print(f"\n최종 테스트 성능:")
        print(f"Test Loss: {test_loss:.4f}, Test Acc: {test_acc:.2f}%")
        
        # 훈련 기록 저장
        training_history = {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'train_accs': train_accs,
            'val_accs': val_accs,
            'best_val_acc': best_val_acc,
            'test_acc': test_acc,
            'test_loss': test_loss,
            'epochs_trained': len(train_losses)
        }
        
        with open(self.model_dir / 'training_history.json', 'w') as f:
            json.dump(training_history, f, indent=2)
        
        # 학습 곡선 시각화
        self.plot_training_history(training_history)
        
        return model, training_history
    
    def plot_training_history(self, history):
        """훈련 과정 시각화"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # 손실 곡선
        ax1.plot(history['train_losses'], label='Train Loss')
        ax1.plot(history['val_losses'], label='Val Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # 정확도 곡선
        ax2.plot(history['train_accs'], label='Train Acc')
        ax2.plot(history['val_accs'], label='Val Acc')
        ax2.set_title('Training and Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(self.model_dir / 'training_history.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def evaluate_model(self, model, test_loader):
        """모델 상세 평가"""
        model.eval()
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in tqdm(test_loader, desc="Evaluating"):
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                
                all_predictions.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # 분류 리포트
        class_names = ['front', 'back', 'inner', 'disk']
        report = classification_report(all_labels, all_predictions, target_names=class_names)
        print("Classification Report:")
        print(report)
        
        # 혼동 행렬
        cm = confusion_matrix(all_labels, all_predictions)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        plt.savefig(self.model_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return report, cm

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='LP 이미지 분류 모델 훈련')
    parser.add_argument('--data_dir', default='data/processed/dataset', help='데이터셋 디렉토리')
    parser.add_argument('--model_dir', default='models/saved_models/lp_classifier', help='모델 저장 디렉토리')
    parser.add_argument('--epochs', type=int, default=50, help='훈련 에포크 수')
    parser.add_argument('--batch_size', type=int, default=32, help='배치 크기')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='학습률')
    parser.add_argument('--patience', type=int, default=10, help='조기 종료 patience')
    parser.add_argument('--device', help='사용할 디바이스 (cuda/cpu)')
    
    args = parser.parse_args()
    
    # 훈련 시작
    trainer = LPModelTrainer(args.data_dir, args.model_dir, args.device)
    model, history = trainer.train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        patience=args.patience
    )
    
    # 상세 평가
    _, val_loader, test_loader, _ = trainer.create_data_loaders(args.batch_size)
    trainer.evaluate_model(model, test_loader)
    
    print("훈련 완료!")

if __name__ == "__main__":
    main()
