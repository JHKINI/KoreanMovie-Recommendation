from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from collections import Counter
ROOT = Path(__file__).resolve().parent
SOURCE = Path('D:/JungPra/pythonpra/NSMC/Koreanmovie_review.csv')
df = pd.read_csv(SOURCE)
raw = df.dropna(subset=['review','bert_label'])
cols = ['DRCTR_NM','MOVIE_SDIV_NM','GRAD_NM','GENRE_NM','OPN_DE','TOT_SCRN_CO','VIEWNG_NMPR_CO']
orig = raw.groupby('MOVIE_NM').agg({**{c:'first' for c in cols},'rating':'mean','bert_label':'mean'})
d = df.copy()
d['review'] = d['review'].fillna('').str.strip()
d = d[d['review'].ne('')].drop_duplicates(['MOVIE_NM','review','rating'])
g = d.groupby('MOVIE_NM', sort=True)
p = g.agg(**{c:(c,'first') for c in cols}, R=('rating','mean'), v=('rating','count'), n=('review','size'), positive=('bert_label','mean'))
p['text'] = g['review'].apply(lambda s:' '.join(s.drop_duplicates()))
# Independent reference: bounded metadata similarities, no scikit-learn dependency.
cat = p[['MOVIE_SDIV_NM','GRAD_NM']].fillna('미상')
cat_sim = np.mean([(cat[c].to_numpy()[:,None] == cat[c].to_numpy()[None,:]).astype(float) for c in cat],axis=0)
num = p[['TOT_SCRN_CO','VIEWNG_NMPR_CO','R','positive']].astype(float)
num.iloc[:,:2] = np.log1p(num.iloc[:,:2])
num = num.fillna(num.median()).fillna(0)
span = (num.max()-num.min()).replace(0,1)
z = ((num-num.min())/span).to_numpy()
num_sim = 1-np.abs(z[:,None,:]-z[None,:,:]).mean(axis=2)
meta = 0.5*cat_sim+0.5*num_sim
# Character 2-3 gram TF-IDF, min_df=2, max_features=5000; independent reference.
counts=[]; total=Counter(); freq=Counter()
for t in p['text']:
 t=' '.join(t.lower().split())
 c=Counter(t[i:i+n] for n in (2,3) for i in range(len(t)-n+1))
 counts.append(c); total.update(c); freq.update(c.keys())
vocab=sorted((w for w in total if freq[w]>=2),key=lambda w:(-total[w],w))[:5000]
lookup={w:i for i,w in enumerate(vocab)}
x=np.zeros((len(p),len(vocab)))
for i,c in enumerate(counts):
 for w,k in c.items():
  if w in lookup: x[i,lookup[w]]=1+np.log(k)
idf=np.array([np.log((1+len(p))/(1+freq[w]))+1 for w in vocab])
x*=idf; x/=np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
text_sim=x@x.T
C=d['rating'].mean(); m=20
p['B']=(p.v*p.R.fillna(C)+m*C)/(p.v+m)
p['Q']=((p.B-0.5)/4.5).clip(0,1)

def recommend(name,top_n=5):
 if name not in p.index: raise ValueError('영화명을 찾을 수 없습니다.')
 if not 1<=top_n<=20: raise ValueError('top_n은 1~20이어야 합니다.')
 i=p.index.get_loc(name); genre=p.iloc[i]['GENRE_NM']
 if pd.isna(genre): return pd.DataFrame()
 director=p.iloc[i]['DRCTR_NM']
 same=(p.DRCTR_NM.eq(director).fillna(False).to_numpy() if pd.notna(director) else np.zeros(len(p),bool))
 s=np.clip(0.4*meta[i]+0.6*text_sim[i]+0.05*same,0,1)
 out=p.copy(); out['similarity']=s
 out=out.loc[out.GENRE_NM.eq(genre).fillna(False) & (out.index!=name)]
 out=out.sort_values('similarity',ascending=False,kind='stable').head(20)
 out['score']=0.7*out.similarity+0.3*out.Q
 return out.sort_values('score',ascending=False,kind='stable').head(top_n)

checks=[]
for name in p.index:
 r=recommend(name)
 assert name not in r.index
 assert len(r)<=5 and r.index.is_unique
 if not r.empty:
  assert r.GENRE_NM.eq(p.loc[name,'GENRE_NM']).all()
  assert np.isfinite(r[['similarity','score','B']]).all().all()
  assert r.score.is_monotonic_decreasing
 checks.append(name)
for args in [('존재하지않는영화',5),('승부',0),('승부',21)]:
 try: recommend(*args)
 except ValueError: pass
 else: raise AssertionError(args)
assert np.allclose(text_sim,text_sim.T)
assert np.allclose(np.diag(text_sim),1)
assert np.isfinite(meta).all()
assert list(p.index)==list(g['review'].apply(lambda s:' '.join(s.drop_duplicates())).index)
report={
 'rows':len(df),'movies_raw':df.MOVIE_NM.nunique(),'original_movies':len(orig),
 'original_numeric_missing':orig[['TOT_SCRN_CO','VIEWNG_NMPR_CO','rating','bert_label']].isna().sum().to_dict(),
 'clean_rows':len(d),'movies_clean':len(p),'genre_counts':p.GENRE_NM.fillna('미상').value_counts().to_dict(),
 'movie_missing':p[cols+['R','positive']].isna().sum().to_dict(),
 'conflicts':{c:int((df.groupby('MOVIE_NM')[c].nunique()>1).sum()) for c in cols},
 'label_values':sorted(df.bert_label.dropna().unique().tolist()),
 'label_score_agreement':float((df.dropna(subset=['bert_label','pos_score','neg_score']).bert_label.to_numpy()==(df.dropna(subset=['bert_label','pos_score','neg_score']).pos_score.to_numpy()>df.dropna(subset=['bert_label','pos_score','neg_score']).neg_score.to_numpy()).astype(int)).mean()),
 'rating_range':[float(d.rating.min()),float(d.rating.max())], 'global_mean':C,'m':m,
 'verified_movies':len(checks),'reference_features':len(vocab),
 'example':recommend('승부')[['GENRE_NM','R','v','positive','similarity','B','score']].reset_index().to_dict('records'),
 'input_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'versions':{'numpy':np.__version__,'pandas':pd.__version__},
}
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))

# Review display: use actual ratings, not predicted sentiment as rating.
def show_reviews(movie_name, top_n=5, order='high'):
    if movie_name not in p.index:
        raise ValueError('영화명을 찾을 수 없습니다.')
    if order not in ('high','low') or not 1 <= top_n <= 20:
        raise ValueError('order는 high/low, top_n은 1~20입니다.')
    rows = d.loc[d.MOVIE_NM.eq(movie_name), ['review','rating']].copy()
    rows = rows.dropna(subset=['rating'])
    return rows.sort_values('rating', ascending=(order=='low'), kind='stable').head(top_n)

for name in p.index:
    for order in ('high','low'):
        rows=show_reviews(name,order=order)
        assert len(rows)<=5
        assert (rows.rating.is_monotonic_decreasing if order=='high' else rows.rating.is_monotonic_increasing)
        assert rows.review.str.strip().ne('').all()
report['dropped_movies']=sorted(set(df.MOVIE_NM)-set(p.index))
report['missing_genre_movies']=p.index[p.GENRE_NM.isna()].tolist()
report['reviews_sort_checks']=len(p)*2
report['review_example']=show_reviews('서울의 봄',3).to_dict('records')
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('REVIEW_SORT_PASS', report['reviews_sort_checks'])
print('DROPPED',report['dropped_movies'])
print('UNKNOWN_GENRE',report['missing_genre_movies'])
