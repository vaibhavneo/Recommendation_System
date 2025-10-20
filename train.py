import pandas as pd, scipy.sparse as sp
from implicit.als import AlternatingLeastSquares


E = pd.read_csv('data/events.csv') # user_id,item_id,weight
n_users = E.user_id.max()+1; n_items = E.item_id.max()+1
X = sp.coo_matrix((E.weight,(E.user_id,E.item_id)), shape=(n_users,n_items)).tocsr()
model = AlternatingLeastSquares(factors=64, regularization=0.01, iterations=20)
model.fit(X)
model.save('models/als.npz')