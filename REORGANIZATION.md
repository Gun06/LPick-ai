# 프로젝트 구조 정리 완료

## 📋 정리 일시

2024년 10월 16일

## 🎯 정리 목적

- 루트 디렉토리에 산재되어 있던 스크립트 파일들을 체계적으로 정리
- 프로젝트 구조를 명확하게 하여 유지보수성 향상
- 새로운 개발자가 프로젝트 구조를 쉽게 파악할 수 있도록 개선

## 📦 변경 사항

### 1. 새로 생성된 폴더

#### `tools/` - 개발 도구들

프로젝트 개발에 사용되는 각종 도구들을 모아둔 폴더

##### `tools/labeling/` - 라벨링 도구

- `web_labeling.py` - 웹 기반 카테고리 라벨링 도구 (루트에서 이동)
- `interactive_labeling.py` - 콘솔 기반 라벨링 도구 (루트에서 이동)
- `bbox_labeling_server.py` - 바운딩 박스 라벨링 서버 (루트에서 이동)

##### `tools/analysis/` - 분석 도구

- `test_training_results.py` - 학습 결과 분석 스크립트 (루트에서 이동)

#### `scripts/` - 실행 스크립트

사용자가 직접 실행하는 스크립트들

- `run_labeling.py` - 라벨링 도구 실행 스크립트 (루트에서 이동)
- `run_bbox_labeling.py` - 바운딩 박스 라벨링 실행 스크립트 (루트에서 이동)
- `run_full_pipeline.py` - 전체 파이프라인 실행 스크립트 (루트에서 이동)

### 2. 수정된 파일

#### `scripts/run_bbox_labeling.py`

```python
# 변경 전
project_root = Path(__file__).parent
cmd = [sys.executable, "bbox_labeling_server.py", ...]

# 변경 후
project_root = Path(__file__).parent.parent  # scripts/ -> lpick-ai/
cmd = [sys.executable, "tools/labeling/bbox_labeling_server.py", ...]
```

#### `scripts/run_labeling.py`

```python
# 변경 전
project_root = Path(__file__).parent

# 변경 후
project_root = Path(__file__).parent.parent  # scripts/ -> lpick-ai/
```

#### `README.md`

- 폴더 구조 섹션을 실제 프로젝트 구조에 맞게 업데이트
- 라벨링 도구 사용법 경로 업데이트
  - `python web_labeling.py` → `python tools/labeling/web_labeling.py`
  - `python run_bbox_labeling.py` → `python scripts/run_bbox_labeling.py`

### 3. 이동된 파일 목록

| 이전 경로                  | 새 경로                                   | 용도                    |
| -------------------------- | ----------------------------------------- | ----------------------- |
| `bbox_labeling_server.py`  | `tools/labeling/bbox_labeling_server.py`  | 바운딩 박스 라벨링 서버 |
| `interactive_labeling.py`  | `tools/labeling/interactive_labeling.py`  | 콘솔 기반 라벨링 도구   |
| `web_labeling.py`          | `tools/labeling/web_labeling.py`          | 웹 기반 라벨링 도구     |
| `test_training_results.py` | `tools/analysis/test_training_results.py` | 학습 결과 분석          |
| `run_bbox_labeling.py`     | `scripts/run_bbox_labeling.py`            | 바운딩 박스 라벨링 실행 |
| `run_full_pipeline.py`     | `scripts/run_full_pipeline.py`            | 전체 파이프라인 실행    |
| `run_labeling.py`          | `scripts/run_labeling.py`                 | 라벨링 도구 실행        |

## 📁 정리된 프로젝트 구조

```
lpick-ai/
├── data/                    # 데이터 관련
│   ├── raw/                # 원본 데이터
│   ├── processed/          # 전처리된 데이터
│   └── scripts/            # 데이터 처리 스크립트
├── models/                 # 모델 관련
│   ├── model_architectures/
│   ├── saved_models/
│   ├── scripts/           # 모델 학습/평가 스크립트
│   └── utils/
├── tools/                  # 개발 도구 (NEW!)
│   ├── labeling/          # 라벨링 도구
│   └── analysis/          # 분석 도구
├── scripts/               # 실행 스크립트 (NEW!)
│   ├── run_labeling.py
│   ├── run_bbox_labeling.py
│   └── run_full_pipeline.py
├── src/                   # 소스 코드
│   ├── api/
│   ├── data_loader/
│   ├── models/
│   ├── utils/
│   └── visualization/
├── templates/             # HTML 템플릿
├── tests/                 # 테스트
├── notebooks/             # Jupyter 노트북
├── config/                # 설정 파일
└── logs/                  # 로그 파일
```

## 🚀 사용 방법 변경

### 라벨링 도구 실행

#### 이전:

```bash
python web_labeling.py --data_dir data/raw/discogs --output_dir data/processed/labeled --port 5000
python run_bbox_labeling.py
```

#### 현재:

```bash
# 직접 실행
python tools/labeling/web_labeling.py --data_dir data/raw/discogs --output_dir data/processed/labeled --port 5000

# 실행 스크립트 사용 (권장)
python scripts/run_labeling.py
python scripts/run_bbox_labeling.py
```

### 분석 도구 실행

#### 이전:

```bash
python test_training_results.py
```

#### 현재:

```bash
python tools/analysis/test_training_results.py
```

### 전체 파이프라인 실행

#### 이전:

```bash
python run_full_pipeline.py
```

#### 현재:

```bash
python scripts/run_full_pipeline.py
```

## ✅ 정리 효과

1. **명확한 구조**: 파일의 용도에 따라 폴더가 분리되어 있어 찾기 쉬움
2. **유지보수성 향상**: 관련 파일들이 함께 위치하여 관리가 용이
3. **확장성**: 새로운 도구나 스크립트 추가 시 어디에 넣을지 명확함
4. **협업 용이**: 새로운 개발자가 프로젝트 구조를 빠르게 이해 가능

## 📝 주의사항

1. **경로 변경**: 파일 경로가 변경되었으므로, 기존에 절대 경로로 참조하던 코드가 있다면 수정 필요
2. **IDE 설정**: IDE에서 Python 모듈 경로가 프로젝트 루트로 설정되어 있는지 확인
3. **가상환경**: 가상환경을 사용 중이라면 activate 후 실행

## 🔄 향후 개선 사항

1. ✅ 루트 디렉토리 정리 완료
2. ⏳ 테스트 코드 추가
3. ⏳ CI/CD 파이프라인 구축
4. ⏳ Docker 컨테이너화
5. ⏳ API 문서화

## 📞 문의

정리된 구조에 대한 질문이나 제안사항이 있다면 이슈를 등록해주세요.
