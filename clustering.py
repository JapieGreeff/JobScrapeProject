"""
Clustering the data using the BMD algorithm. 
"""
import pandas as pd
import numpy as np
from bmdcluster import * 
import csv   
import plotly.express as px
import time
import math
import os
import shutil
from docx import Document
from docx.shared import Inches

def clusterAveKMeans(numberiterations, codingsessiondata, technologies, minrowcount, noclusters, minclasssize, pathToDumpReports, numtechtoplot):
        class FoundClass:
            # create the class the first time you find it
            def __init__(self, classdictionary, classsize):
                self.classdictionary = classdictionary
                self.classsize = classsize
                self.count = 1
                self.childrenclasses = []
          
            # every time a class is found add it's values to the percentages (counttoadd will be used when merging into master class)
            def addtofoundclass(self, otherclass):
                for key, value in otherclass.classdictionary.items():
                    self.classdictionary[key] = self.classdictionary[key] + value 
                self.classsize = self.classsize + otherclass.classsize
                self.count = self.count + otherclass.count

            # once all the searches have completed, average the percentages by calling this function
            def average(self):
                for key,value in self.classdictionary.items():
                    self.classdictionary[key] = self.classdictionary[key] / self.count
                self.classsize = self.classsize / self.count
           
            def comparemeansquareerror(self, otherclass):
                meansquareerrorrunningtotal = 0
                for key, value in self.classdictionary.items():
                    meansquareerrorrunningtotal += (value - otherclass.classdictionary[key])*(value - otherclass.classdictionary[key])
                return meansquareerrorrunningtotal / len(self.classdictionary.keys())

            #plot the data as a bar chart using plotly express
            def plotbarchart(self, pathtowriteto, numtechtoplot):
                # first create a dataframe from the dictionary
                topfifteentechnologies = sorted(self.classdictionary.items(), key=lambda kv: kv[1], reverse=True) [:int(numtechtoplot)]
                df = pd.DataFrame()
                classdictasdict = dict(topfifteentechnologies)
                leftaxisname = f'percentage (n={math.ceil(self.classsize)})'
                df['technologies'] = classdictasdict.keys()
                df[leftaxisname] = classdictasdict.values()
                fig = px.bar(df, x='technologies', y=leftaxisname)
                if pathtowriteto is not None:
                    fig.write_image(pathtowriteto)
                else:
                    fig.show()


        resulttext = ""
        classesfound = []
        for _ in range(int(numberiterations)):
            #first filter out all of the technologies that have been selected
            filtereddataframe = codingsessiondata.copy()
            for technology in technologies:
                if technology.filtered:
                    filtereddataframe = filtereddataframe.drop(columns=[technology.name])
            textresult, classesreturned = clusterusingbmdpercentageoutput(filtereddataframe, 
                int(minrowcount),
                int(noclusters),
                len(filtereddataframe.columns),
                0,
                int(minclasssize))
            if len(classesreturned) > 0:
                for classinstancefound in classesreturned:
                    classesfound.append(FoundClass(classinstancefound[0], classinstancefound[1]))
        
        # for all of the classes found in the BMD clustering, first remove the classes that have as their top two technologies < 50% (so the catch all classes)
        filteredclasses = []
        for foundclass in classesfound:
            toptwotechnologies = sorted(foundclass.classdictionary.items(), key=lambda kv: kv[1], reverse=True) [:2]
            if toptwotechnologies[0][1] > 50 and toptwotechnologies[1][1] > 50:
                filteredclasses.append(foundclass)

        # create a 2d array to hold the mse values and populate with the mse for each class to each other class
        msearray = np.zeros(shape=(len(filteredclasses),len(filteredclasses)))
        # to calculate how many classes are required, for each class it contributes 1/n towards the class count where n is the number of other classes where the mse is < 10%
        rowcount = 0
        cumulativeclasscount = 0
        for foundclass in filteredclasses:
            colcount = 0
            n = 0
            for otherclass in filteredclasses:
                mse = foundclass.comparemeansquareerror(otherclass)
                msearray[rowcount][colcount] = mse
                #if mse < 10:
                if mse < 25:
                    n = n + 1
                colcount = colcount + 1
            cumulativeclasscount = cumulativeclasscount + 1/n
            rowcount = rowcount + 1  
        # the cumulative class count to be used for k means clustering is rounded up
        cumulativeclasscount = math.ceil(cumulativeclasscount)
        from sklearn.cluster import KMeans
        est = KMeans(n_clusters=cumulativeclasscount).fit(msearray)
        print(est.labels_)
        # create a dictionary to hold the class allocations for the KMeans clustering
        labeldict = {}
        for i in range(cumulativeclasscount):
            labeldict[i] = []
        for label, foundclass in zip(est.labels_, filteredclasses):
            toptentechnologies = sorted(foundclass.classdictionary.items(), key=lambda kv: kv[1], reverse=True) [:10]
            print(f'{foundclass.count}:{foundclass.classsize}:{toptentechnologies}')
            labeldict[label].append(foundclass)
        # print out the class groupings that were found but only for classes that were found at least twice
        groupedclasses = 0
        averagedClasses = []
        for i in range(cumulativeclasscount):
            if len(labeldict[i]) > 1:
                #resulttext += f"{groupedclasses}:class{i}: \n"
                groupedclasses = groupedclasses + 1
                averagingclass = labeldict[i][0]
                for foundclass in labeldict[i]:
                    if foundclass is not averagingclass:
                        averagingclass.addtofoundclass(foundclass)
                averagingclass.average()
                averagedClasses.append(averagingclass)

        # Create the session path
        os.mkdir(pathToDumpReports)

        # write bar charts of each of the average classes to file and into a docx document
        document = Document()
        for idx, averageclass in enumerate(averagedClasses):
            pathtowriteimage = pathToDumpReports + f'/class{idx}_{math.ceil(averageclass.classsize)}.png'
            print(f"writing {pathtowriteimage}")
            averageclass.plotbarchart(pathtowriteimage, numtechtoplot)
            document.add_picture(pathtowriteimage, width=Inches(6), height=Inches(4))
            time.sleep(1)
        documentpath = pathToDumpReports + '/barcharts.docx'
        document.save(documentpath)
        
        # write each of the 

        # print out the averaged classes that have now been identified as well as the dictionary that contains the size and class dictionary
        resulttext = ""
        classestooutput = []
        for idx, averageclass in enumerate(averagedClasses):
            resulttext += f"{idx}:{averageclass.classsize}:{averageclass.classdictionary} \n \n"
            averageclass.classdictionary['classSize'] = averageclass.classsize
            classestooutput.append(averageclass.classdictionary)

        # write out the averaged found class groupings to a csv file so it can be plotted using excel
        pathtocsvaverageclasses = pathToDumpReports+'/averagefoundclasses.csv'
        tosave = pd.DataFrame(classestooutput)
        tosave.to_csv(pathtocsvaverageclasses)
        return resulttext

def clusterusingbmdpercentageoutput(sessiondata, minimumcount, noclusters, maxtechnologiesinaclass, technologypercentagecutoff, minclassinstances ):
    """
    parameters:
        sessiondata - the coding session's dataframe that is to be clustered
        minimumcount - technologies that have less than this will not be taken into account
        noclusters - number of clusters that will searched for
        maxtechnologiesinaclass - number of the most used technologies in a class used to identify the class
        technologypercentagecutoff - below this percentage a technology is not considered a feature in a class
        minclassinstances - only return classes that have at least this many row instances

    returns:
        text output of the results
        array of (dictionary,int) tuples that contain the technologies in the class and the percentage technology use as well as int class size
    """
    # only cluster on rows that have been coded
    clusterdataframe = sessiondata.copy()
    clusterdataframe = clusterdataframe[clusterdataframe.Coded != False]

    # drop the columns that aren't clustered
    clusterdataframe = clusterdataframe.drop(columns=['ID', 'Coded'])

    # drop columns that have less than "filter" number of instances
    filtersize = int(minimumcount)
    columnstodrop = []
    for column in clusterdataframe:
        if clusterdataframe[column].sum() < filtersize:
            columnstodrop.append(column)
    for column in columnstodrop:
        clusterdataframe = clusterdataframe.drop(columns=[column])

    # perform the clustering using the BMD algorithm
    numberOfClusters = int(noclusters)
    BMD_model = bmdcluster(n_clusters = numberOfClusters, method = 'block_diagonal', B_ident = True, use_bootstrap = True, b = 10)
    cost, A, B = BMD_model.fit(clusterdataframe.values, verbose = 1, return_results= True)
    
    # create an array of arrays for the features that are assigned to each cluster, as well as an array that holds the count of data rows each cluster has assigned to it
    clusterFeatures = []
    clusterCount = []
    for i in range(numberOfClusters):
        clusterFeatures.append([])
        clusterCount.append(0)
    
    # loop over the feature membership matrix to see which clusters each feature should be assigned to
    for idx, clusterMembership in enumerate(B):
        for idy, membership in enumerate(clusterMembership):
            if membership:
                clusterFeatures[idy].append(clusterdataframe.columns[idx])

    # append the assignment array to the end of the clusterData
    assignmentArray = np.array(A)
    for col in range(numberOfClusters):
        clusterdataframe[f'class{col}'] = assignmentArray[:,col]

    # iterate over the listings that have been assigned to clusters in A and increment the count for each cluster for each listing assigned to it.
    for listingAssignment in A:
        indexOffset = 0
        for clusterAssignment in listingAssignment:
            if clusterAssignment == 1:
                clusterCount[indexOffset] = clusterCount[indexOffset] + 1
            indexOffset = indexOffset + 1

    resultText = ''

    for clusterFeatureList, count in zip(clusterFeatures, clusterCount):
        print(f"{count}:{clusterFeatureList}")
        resultText += f"{count}:{clusterFeatureList} \n"
    resultText += '\n'
    
    # calculate the percentage use of each technology in each of the found classes
    classesToReturn = []
    for col in range(numberOfClusters):
        technologiesCount = {}
        # get a dataframe of the data rows that are all members of the class and populate the dictionary with the percentage of the data rows that have that feature 
        tempdf = clusterdataframe.loc[clusterdataframe[f'class{col}'] == 1]
        # from this tempdf remove the class features
        for coltodrop in range(numberOfClusters):
            tempdf = tempdf.drop(columns=[f'class{coltodrop}'])
        for tech in tempdf:
            percentageuse = 100 * tempdf[tech].sum() / len(tempdf.index) 
            # take the toptechnologies used by the class, with the cut off at technologypercentagecutoff
            if percentageuse >= technologypercentagecutoff:
                technologiesCount[tech] = percentageuse
        # only take the top maxtechnologiesinaclass
        sortedtechnologiesCount = sorted(technologiesCount.items(), key=lambda kv: kv[1], reverse=True) [:maxtechnologiesinaclass]
        # turn the sorted and limited list back into a dictionary
        if len(sortedtechnologiesCount) > 1 and len(tempdf.index) > minclassinstances:
            classdictionary = {}
            for technologyandpercentage in sortedtechnologiesCount:
                classdictionary[technologyandpercentage[0]] = technologyandpercentage[1]
            classesToReturn.append((classdictionary, len(tempdf.index)))
        resultText += '\n'
        resultText += f'class{col} technologies: \n'
        for tech in sortedtechnologiesCount:
            resultText += f'{tech}'
        resultText += '\n'

    # create an empty data frame that is used as the check frame 
    checkFrame = clusterdataframe.copy()
    print("copied check frame")
    #print(checkFrame)
    # clear the checkframe
    for feature in checkFrame.columns:
        for rowId in checkFrame.index.values:
            checkFrame.at[rowId, feature] = 0
    # print out the empty checkframe
    print("empty check frame")
    #print(checkFrame)

    # use the data cluster assignments (A) to assign the features that belong to each cluster (clusterFeatures) into a recreatedframe that contains just the cluster features
    rowIds = checkFrame.index.values
    recreatedFrame = checkFrame.copy()
    for idrow, dataClusterAssignment in enumerate(A):
        for idclass, assigned in enumerate(dataClusterAssignment):
            if assigned == 1:
                for feature in clusterFeatures[idclass]:
                    recreatedFrame.at[rowIds[idrow], feature] = 1
    print("recreated frame")
    #print(recreatedFrame)

    # compare X and the recreatedframe - where a feature was in X and not in RF mark as 2, where only in the recreatedframe mark as 3, where in both mark 1, where in neither mark 0
    featuresMatched = 0
    nonFeaturesMatched = 0
    featuresMissed = 0
    featureFalseAdds = 0

    for feature in clusterdataframe.columns:
        for row in rowIds:
            origCell = clusterdataframe.at[row, feature]
            recCell = recreatedFrame.at[row, feature]
            if origCell == 1 and recCell == 1:
                checkFrame.at[row, feature] = 1
                featuresMatched += 1
            elif origCell == 0 and recCell == 0:
                checkFrame.at[row, feature] = 0
                nonFeaturesMatched += 1
            elif origCell == 1 and recCell == 0:
                checkFrame.at[row, feature] = 2
                featuresMissed += 1
            elif origCell == 0 and recCell == 1:
                checkFrame.at[row, feature] = 3
                featureFalseAdds += 1
                    
    #print(checkFrame)
    total = featuresMatched + nonFeaturesMatched + featuresMissed + featureFalseAdds
    print(f'featuresMatched: {featuresMatched}')
    print(f'nonFeaturesMatched: {nonFeaturesMatched}')
    print(f'featuresMissed: {featuresMissed}')
    print(f'featureFalseAdds: {featureFalseAdds}')
    print(f'success: {(featuresMatched + nonFeaturesMatched)/total}%')
    print(f'safe assignment: {(featuresMatched + nonFeaturesMatched + featureFalseAdds)/total}%')
    
    resultText += f'featuresMatched: {featuresMatched} \n'
    resultText += f'nonFeaturesMatched: {nonFeaturesMatched} \n'
    resultText += f'featuresMissed: {featuresMissed} \n'
    resultText += f'featureFalseAdds: {featureFalseAdds} \n'
    resultText += f'success: {(featuresMatched + nonFeaturesMatched)/total}% \n'
    resultText += f'safe assignment: {(featuresMatched + nonFeaturesMatched + featureFalseAdds)/total}% \n'
    return resultText, classesToReturn