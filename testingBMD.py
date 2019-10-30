import os, sys
import pandas as pd
from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib.pyplot as plt

from sklearn import svm, datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels

if __name__ == '__main__':
    
    mypath = os.path.dirname(os.path.realpath('__file__'))
    sys.path.append(os.path.join(mypath, os.pardir))
    
from bmdcluster import *    

#########################################
#############  Zoo Dataset ##############
#########################################

zoo = pd.read_csv('./data/zoo.csv', sep = ',', index_col = 0)

class_labels = zoo.type.values - 1   # get class labels of animal types
zoo = zoo.iloc[:, 0:21]              # remove labels from data
print(zoo.columns)
numberOfClusters = 7

# fit BMD model
BMD_model = bmdcluster(n_clusters = numberOfClusters, method = 'block_diagonal', B_ident = True, use_bootstrap = True, b = 10)
#BMD_model = bmdcluster(n_clusters = numberOfClusters, method = 'general', B_ident = True, use_bootstrap = True, b = 10)
cost, A, B = BMD_model.fit(zoo.values, verbose = 1, return_results= True)
print("Cost")
print(cost)
print("A matrix")
print(A)
print("B matrix")
print(B)

class_names = ['animal1','animal2','animal3','animal4','animal5','animal6','animal7']
# show confusion matrix
print("confusion matrix")
print(confusion_matrix(class_labels, np.argmax(BMD_model.A, axis = 1)))

np.set_printoptions(precision=2)

# add in the features that belong to each cluster that has been found
#clusterFeatures = [[],[],[],[],[],[],[]]
clusterFeatures = []
for i in range(numberOfClusters):
    clusterFeatures.append([])

for idx, clusterMembership in enumerate(B):
    for idy, membership in enumerate(clusterMembership):
        if membership:
            clusterFeatures[idy].append(zoo.columns[idx])
for clusterFeatureList in clusterFeatures:
    print(clusterFeatureList)

# create an empty data frame that is used as the check frame 
checkFrame = zoo.copy()
print("copied check frame")
print(checkFrame)
# clear the checkframe
for feature in checkFrame.columns:
    for rowId in checkFrame.index.values:
        checkFrame.at[rowId, feature] = 0
# print out the empty checkframe
print("empty check frame")
print(checkFrame)

# use the data cluster assignments (A) to assign the features that belong to each cluster (clusterFeatures) into a recreatedframe that contains just the cluster features
rowIds = checkFrame.index.values
recreatedFrame = checkFrame.copy()
for idrow, dataClusterAssignment in enumerate(A):
    for idclass, assigned in enumerate(dataClusterAssignment):
        if assigned == 1:
            for feature in clusterFeatures[idclass]:
                recreatedFrame.at[rowIds[idrow], feature] = 1
print("recreated frame")
print(recreatedFrame)

# compare X and the recreatedframe - where a feature was in X and not in RF mark as 2, where only in the recreatedframe mark as 3, where in both mark 1, where in neither mark 0
featuresMatched = 0
nonFeaturesMatched = 0
featuresMissed = 0
featureFalseAdds = 0

for feature in zoo.columns:
    for row in rowIds:
        zooCell = zoo.at[row, feature]
        recCell = recreatedFrame.at[row, feature]
        if zooCell == 1 and recCell == 1:
            checkFrame.at[row, feature] = 1
            featuresMatched += 1
        elif zooCell == 0 and recCell == 0:
            checkFrame.at[row, feature] = 0
            nonFeaturesMatched += 1
        elif zooCell == 1 and recCell == 0:
            checkFrame.at[row, feature] = 2
            featuresMissed += 1
        elif zooCell == 0 and recCell == 1:
            checkFrame.at[row, feature] = 3
            featureFalseAdds += 1
                   

print(checkFrame)
total = featuresMatched + nonFeaturesMatched + featuresMissed + featureFalseAdds
print(f'featuresMatched: {featuresMatched}')
print(f'nonFeaturesMatched: {nonFeaturesMatched}')
print(f'featuresMissed: {featuresMissed}')
print(f'featureFalseAdds: {featureFalseAdds}')
print(f'success: {(featuresMatched + nonFeaturesMatched)/total}%')
print(f'safe assignment: {(featuresMatched + nonFeaturesMatched + featureFalseAdds)/total}%')
