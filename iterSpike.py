import numpy as np
from sklearn.cluster import KMeans
from sklearn import datasets

iris = datasets.load_iris()
X = iris.data
y = iris.target

est = KMeans(n_clusters=3).fit(X)
print(est.labels_)
