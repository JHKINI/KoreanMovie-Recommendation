"""리뷰 문구 단위로 학습용/평가용 데이터를 나누고 CSV로 저장합니다."""
from pathlib import Path
import argparse
import pandas as pd


def main():
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=base_dir / 'movie_reviews_ready.csv')
    parser.add_argument('--output-dir', type=Path, default=base_dir)
    args = parser.parse_args()

    # 1. 정리된 리뷰와 실제 평점 읽기
    data = pd.read_csv(args.input)
    if list(data.columns) != ['review', 'rating']:
        raise ValueError('입력 CSV에는 review, rating 두 컬럼이 필요합니다.')
    if data.empty or data.isna().any().any():
        raise ValueError('데이터가 비어 있거나 결측치가 있습니다.')
    if data['review'].str.strip().eq('').any():
        raise ValueError('빈 리뷰가 있습니다.')

    # 2. 리뷰 문구의 20%를 평가용으로 선택
    # 같은 문구에 평점이 여러 개 있어도 모든 행이 같은 쪽으로 들어갑니다.
    reviews = data['review'].drop_duplicates()
    test_reviews = reviews.sample(frac=0.2, random_state=42)
    is_test = data['review'].isin(test_reviews)

    # 3. 평가용 행과 나머지 학습용 행 분리
    train_data = data.loc[~is_test].reset_index(drop=True)
    test_data = data.loc[is_test].reset_index(drop=True)

    # 4. 리뷰 누수와 행 수 확인
    overlap = set(train_data['review']) & set(test_data['review'])
    assert len(overlap) == 0, '학습용과 평가용에 동일 리뷰가 있습니다.'
    assert len(train_data) + len(test_data) == len(data)

    # 5. 입력 파일과 다른 이름으로 저장
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.output_dir / 'movie_reviews_train.csv'
    test_path = args.output_dir / 'movie_reviews_test.csv'
    if args.input.resolve() in {train_path.resolve(), test_path.resolve()}:
        raise ValueError('출력 파일은 입력 파일과 달라야 합니다.')
    train_data.to_csv(train_path, index=False, encoding='utf-8-sig')
    test_data.to_csv(test_path, index=False, encoding='utf-8-sig')

    print('전체 행 수:', len(data))
    print('학습용 행 수:', len(train_data))
    print('평가용 행 수:', len(test_data))
    print('양쪽에 겹치는 리뷰 수:', len(overlap))
    ratio = pd.DataFrame({
        '학습용(%)': train_data['rating'].value_counts(normalize=True) * 100,
        '평가용(%)': test_data['rating'].value_counts(normalize=True) * 100,
    }).fillna(0).sort_index()
    print('\n평점별 비율:')
    print(ratio.round(2))
    print('\n저장:', train_path)
    print('저장:', test_path)


if __name__ == '__main__':
    main()
