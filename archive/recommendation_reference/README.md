# 이전 추천 참조 구현

`recommendation_demo.py`와 `verify.py`는 이전 대화에서 NumPy/pandas로 검증한 참고 코드다.
현재 운영용 파이프라인은 프로젝트 루트의 `run_pipeline.py`, `recommender.py`, `api.py`를 사용한다.
이 참조 코드는 원문을 그대로 보존했으며 현재 API에서 import하지 않는다.

원본 CSV를 복제하지 않고 참조 코드를 실행하려면 원본 경로를 명시한다.

```powershell
cd D:\JungPra\pythonpra\NSMC
.\.venv\Scripts\python.exe archive\recommendation_reference\recommendation_demo.py D:\JungPra\pythonpra\NSMC\Koreanmovie_review.csv
```

참조 검증 JSON은 이 폴더에 생성된다. 참고 실험을 다시 하고 싶을 때만 실행한다.
