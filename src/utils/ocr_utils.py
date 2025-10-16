#!/usr/bin/env python3
"""
LP 이미지에서 텍스트 추출을 위한 OCR 유틸리티
Tesseract OCR과 Google Vision API를 사용하여 텍스트 추출
"""

import os
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Tuple, Optional
import pytesseract
import json
from pathlib import Path

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Google Vision API가 설치되지 않았습니다. pip install google-cloud-vision")

class LPTextExtractor:
    """LP 이미지에서 텍스트를 추출하는 클래스"""
    
    def __init__(self, google_credentials_path: Optional[str] = None):
        self.google_vision_available = GOOGLE_VISION_AVAILABLE
        
        if self.google_vision_available and google_credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials_path
            self.vision_client = vision.ImageAnnotatorClient()
        else:
            self.vision_client = None
    
    def preprocess_image(self, image: np.ndarray) -> List[np.ndarray]:
        """이미지 전처리 - 다양한 전처리 방법 적용"""
        processed_images = []
        
        # 원본 이미지
        processed_images.append(image)
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        processed_images.append(gray)
        
        # 가우시안 블러 적용
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        processed_images.append(blurred)
        
        # 적응적 임계값 적용
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(thresh)
        
        # 모폴로지 연산 적용
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(morph)
        
        # 노이즈 제거
        denoised = cv2.medianBlur(gray, 3)
        processed_images.append(denoised)
        
        return processed_images
    
    def extract_text_tesseract(self, image: np.ndarray) -> Dict[str, any]:
        """Tesseract OCR을 사용하여 텍스트 추출"""
        try:
            # 이미지 전처리
            processed_images = self.preprocess_image(image)
            
            best_result = None
            best_confidence = 0
            
            for processed_img in processed_images:
                # Tesseract 설정
                config = '--oem 3 --psm 6'
                
                # 텍스트 추출
                data = pytesseract.image_to_data(processed_img, config=config, output_type=pytesseract.Output.DICT)
                
                # 신뢰도 계산
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = np.mean(confidences) if confidences else 0
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_result = data
            
            if best_result is None:
                return {'text': '', 'confidence': 0, 'words': []}
            
            # 결과 정리
            words = []
            for i in range(len(best_result['text'])):
                if int(best_result['conf'][i]) > 30:  # 신뢰도 30 이상만
                    word = best_result['text'][i].strip()
                    if word:
                        words.append({
                            'text': word,
                            'confidence': int(best_result['conf'][i]),
                            'bbox': {
                                'x': best_result['left'][i],
                                'y': best_result['top'][i],
                                'width': best_result['width'][i],
                                'height': best_result['height'][i]
                            }
                        })
            
            # 전체 텍스트 조합
            full_text = ' '.join([word['text'] for word in words])
            
            return {
                'text': full_text,
                'confidence': best_confidence,
                'words': words,
                'method': 'tesseract'
            }
            
        except Exception as e:
            print(f"Tesseract OCR 오류: {e}")
            return {'text': '', 'confidence': 0, 'words': [], 'error': str(e)}
    
    def extract_text_google_vision(self, image: np.ndarray) -> Dict[str, any]:
        """Google Vision API를 사용하여 텍스트 추출"""
        if not self.google_vision_available or not self.vision_client:
            return {'text': '', 'confidence': 0, 'words': [], 'error': 'Google Vision API not available'}
        
        try:
            # 이미지를 bytes로 변환
            _, encoded_image = cv2.imencode('.jpg', image)
            image_bytes = encoded_image.tobytes()
            
            # Vision API 요청
            image_obj = vision.Image(content=image_bytes)
            response = self.vision_client.text_detection(image=image_obj)
            
            if response.error.message:
                return {'text': '', 'confidence': 0, 'words': [], 'error': response.error.message}
            
            # 결과 파싱
            texts = response.text_annotations
            if not texts:
                return {'text': '', 'confidence': 0, 'words': []}
            
            # 첫 번째 텍스트는 전체 텍스트
            full_text = texts[0].description
            
            # 개별 단어 정보
            words = []
            for text in texts[1:]:  # 첫 번째는 전체 텍스트이므로 제외
                vertices = text.bounding_poly.vertices
                bbox = {
                    'x': vertices[0].x if vertices else 0,
                    'y': vertices[0].y if vertices else 0,
                    'width': vertices[2].x - vertices[0].x if len(vertices) > 2 else 0,
                    'height': vertices[2].y - vertices[0].y if len(vertices) > 2 else 0
                }
                
                words.append({
                    'text': text.description,
                    'confidence': 0.9,  # Google Vision은 개별 단어 신뢰도를 제공하지 않음
                    'bbox': bbox
                })
            
            return {
                'text': full_text,
                'confidence': 0.9,  # Google Vision은 전체 신뢰도를 제공하지 않음
                'words': words,
                'method': 'google_vision'
            }
            
        except Exception as e:
            print(f"Google Vision API 오류: {e}")
            return {'text': '', 'confidence': 0, 'words': [], 'error': str(e)}
    
    def extract_text_combined(self, image: np.ndarray) -> Dict[str, any]:
        """Tesseract와 Google Vision API를 결합하여 텍스트 추출"""
        # Tesseract 결과
        tesseract_result = self.extract_text_tesseract(image)
        
        # Google Vision 결과
        google_result = self.extract_text_google_vision(image)
        
        # 결과 비교 및 선택
        if tesseract_result['confidence'] > google_result['confidence']:
            best_result = tesseract_result
            best_result['alternative'] = google_result
        else:
            best_result = google_result
            best_result['alternative'] = tesseract_result
        
        best_result['method'] = 'combined'
        return best_result
    
    def extract_text_from_file(self, image_path: str, method: str = 'combined') -> Dict[str, any]:
        """파일에서 텍스트 추출"""
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                return {'text': '', 'confidence': 0, 'words': [], 'error': '이미지 로드 실패'}
            
            # 메서드에 따라 텍스트 추출
            if method == 'tesseract':
                return self.extract_text_tesseract(image)
            elif method == 'google_vision':
                return self.extract_text_google_vision(image)
            elif method == 'combined':
                return self.extract_text_combined(image)
            else:
                return {'text': '', 'confidence': 0, 'words': [], 'error': f'알 수 없는 메서드: {method}'}
                
        except Exception as e:
            return {'text': '', 'confidence': 0, 'words': [], 'error': str(e)}
    
    def batch_extract_text(self, image_dir: str, output_file: str, method: str = 'combined'):
        """디렉토리 내 모든 이미지에서 텍스트 추출"""
        image_dir = Path(image_dir)
        results = []
        
        # 지원되는 이미지 확장자
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        for img_file in image_dir.rglob('*'):
            if img_file.suffix.lower() in image_extensions:
                print(f"처리 중: {img_file}")
                
                result = self.extract_text_from_file(str(img_file), method)
                result['file_path'] = str(img_file)
                result['filename'] = img_file.name
                
                results.append(result)
        
        # 결과 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"텍스트 추출 완료: {len(results)}개 파일")
        print(f"결과 저장: {output_file}")

def main():
    """메인 함수 - 테스트용"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LP 이미지 텍스트 추출')
    parser.add_argument('--image_path', help='이미지 파일 경로')
    parser.add_argument('--image_dir', help='이미지 디렉토리 경로')
    parser.add_argument('--output', help='출력 파일 경로')
    parser.add_argument('--method', choices=['tesseract', 'google_vision', 'combined'], 
                       default='combined', help='텍스트 추출 방법')
    parser.add_argument('--google_credentials', help='Google Vision API 인증서 경로')
    
    args = parser.parse_args()
    
    # 텍스트 추출기 생성
    extractor = LPTextExtractor(args.google_credentials)
    
    if args.image_path:
        # 단일 이미지 처리
        result = extractor.extract_text_from_file(args.image_path, args.method)
        print(f"추출된 텍스트: {result['text']}")
        print(f"신뢰도: {result['confidence']}")
        print(f"단어 수: {len(result['words'])}")
        
    elif args.image_dir:
        # 배치 처리
        if not args.output:
            args.output = 'extracted_text.json'
        extractor.batch_extract_text(args.image_dir, args.output, args.method)

if __name__ == "__main__":
    main()
