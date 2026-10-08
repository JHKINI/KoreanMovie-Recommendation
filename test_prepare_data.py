import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import pandas as pd
from prepare_data import audit_frame, main


def fixture():
    return pd.DataFrame({
        'review_id': [1, 2], 'review': ['좋았다', '별로였다'],
        'rating': [4.5, 1.0], 'MOVIE_NM': ['가', '나'],
        'DRCTR_NM': ['감독 A', '감독 B'], 'GENRE_NM': ['드라마', '코미디'],
        'MOVIE_SDIV_NM': ['일반영화'] * 2, 'GRAD_NM': ['전체관람가'] * 2,
        'OPN_DE': [20250101] * 2, 'TOT_SCRN_CO': [1, 100],
        'VIEWNG_NMPR_CO': [100, 200], 'bert_label': [1, 0],
        'pos_score': [.9, .1], 'neg_score': [.1, .9],
    })


class AuditTests(unittest.TestCase):
    def test_clean_and_no_mutation(self):
        d = fixture(); before = d.copy(deep=True)
        self.assertEqual(audit_frame(d)['status'], 'pass')
        pd.testing.assert_frame_equal(d, before)

    def test_missing_is_warning_not_deletion(self):
        d = fixture().astype({'rating': 'float64'})
        d.loc[0, 'rating'] = float('nan'); d.loc[1, 'review'] = '   '
        r = audit_frame(d)
        self.assertEqual(r['status'], 'pass_with_warnings')
        self.assertEqual(r['rows'], 2)
        self.assertEqual(r['blank_strings']['review'], 1)

    def test_invalid_numbers_fail(self):
        for value in ['bad', 'inf', '-inf', -1, 5.5, 3.3]:
            with self.subTest(value=value):
                d = fixture().astype({'rating': 'object'})
                d.loc[0, 'rating'] = value
                self.assertEqual(audit_frame(d)['status'], 'fail')

    def test_sentiment_and_metadata_domains(self):
        for col, value in [('bert_label', 2), ('pos_score', 1.1),
                           ('neg_score', -.1), ('TOT_SCRN_CO', -2)]:
            with self.subTest(col=col):
                d = fixture(); d.loc[0, col] = value
                self.assertEqual(audit_frame(d)['status'], 'fail')

    def test_duplicate_conflict_and_title_candidates(self):
        d = fixture(); d.loc[1, 'MOVIE_NM'] = '가'
        r = audit_frame(pd.concat([d, d.iloc[[0]]], ignore_index=True))
        self.assertEqual(r['duplicates']['movie_review_rating_extra_rows'], 1)
        self.assertEqual(r['metadata_conflicts']['DRCTR_NM']['movie_count'], 1)
        d.loc[1, 'MOVIE_NM'] = '가,'
        self.assertEqual(len(audit_frame(d)['possible_title_variants']), 1)
        self.assertEqual(audit_frame(d)['movies']['raw_unique_names'], 2)

    def test_missing_columns_and_empty_are_fatal(self):
        with self.assertRaises(ValueError): audit_frame(fixture().drop(columns='rating'))
        with self.assertRaises(ValueError): audit_frame(fixture().iloc[:0])

    def test_no_numeric_ratings_serializes_null(self):
        d = fixture().astype({'rating': 'object'}); d['rating'] = [' ', None]
        self.assertIsNone(audit_frame(d)['rating']['min'])

    def test_cli_exit_codes_and_input_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'input.csv'; out = Path(tmp) / 'report.json'
            fixture().to_csv(src, index=False)
            original = src.read_bytes()
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(main(['--input', str(src), '--output', str(out)]), 0)
                self.assertTrue(out.exists())
                self.assertEqual(main(['--input', str(src), '--output', str(src)]), 2)
                self.assertEqual(src.read_bytes(), original)
                self.assertEqual(main(['--input', str(src)+'missing', '--output', str(out)]), 2)
                d=fixture(); d.loc[0, 'rating']=10; d.to_csv(src,index=False)
                self.assertEqual(main(['--input', str(src), '--output', str(out)]), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
