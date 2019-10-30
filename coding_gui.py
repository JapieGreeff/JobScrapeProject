from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence
from PyQt5 import Qt, QtCore

import os
import pickle
from job_listing import JobListing
import pandas as pd
import numpy as np

from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
from sklearn import svm, datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels
# from bmdcluster import * 

#from clustering import clusterusingbmdtextoutput,clusterusingbmdpercentageoutput, clusterAveKMeans
from clustering import clusterAveKMeans
from reporting import create_analytics_graph, createtechnologyassociationgraph

# import plotly.graph_objects as go
# import plotly.express as px
# import networkx as nx
#import random
#import math
import time
from datetime import datetime

class TechnologyLineItem:
    def __init__(self, name, groupBox, presentFunction, notPresentFunction, columnNumber, technologyPresent, technologyNotPresent, filterlayout, reportingwidget):
        self.name = name
        self.groupBox = groupBox
        self.presentFunction = presentFunction
        self.notPresentFunction = notPresentFunction
        self.columnNumber = columnNumber
        self.active = True
        self.technologyPresent = technologyPresent
        self.technologyNotPresent = technologyNotPresent
        self.filtered = False
        self.reporton = False
        self.filterwidget = filterlayout
        self.reportingwidget = reportingwidget
    
    def setPresent(self):
        self.technologyNotPresent.setChecked(False)
        self.technologyPresent.setChecked(True)
    
    def setNotPresent(self):
        self.technologyPresent.setChecked(False)
        self.technologyNotPresent.setChecked(True)

    def deactivate(self):
        self.active = False

    def enablefilter(self):
        self.filtered = True
    
    def disablefilter(self):
        self.filtered = False
    
    def enablereporton(self):
        self.reporton = True
    
    def disablereporton(self):
        self.reporton = False

class MainWindow(QMainWindow):
    def linkToApp(self, codingApp):
        self.codingApp = codingApp

    def clean(self):
        self.dirtyFlag = False

    def dirty(self):
        self.dirtyFlag = True

    def closeEvent(self, e):
        # to do, save the pandas file to the coding session
        if not self.dirtyFlag:
            return
        answer = QMessageBox.question(self, None, "You have unsaved changes. Save before closing?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if answer & QMessageBox.Save:
            self.codingApp.saveSession()
        elif answer & QMessageBox.Cancel:
            e.ignore()
        pass


class CodingApp:
    def __init__(self):
        self.technologyCounter = 0
        self.technologies = []
        self.listingNumber = 0
        self.path_to_scrape_session = None
        self.path_to_coding_session= None
        self.scrapeSessionData = None
        self.codingSessionData = None

        self.app = QApplication([])
        self.windowFrame = MainWindow()
        self.windowFrame.linkToApp(self)
        self.windowFrame.clean()
        self.windowFrame.setWindowTitle("Job Coding V0.2")

        # create the menu so that session can be loaded
        file_menu = self.windowFrame.menuBar().addMenu("&File")
        open = self.addmenuitem("&Open", self.show_open_file_dialog, QKeySequence.Open)
        save = self.addmenuitem("&Save", self.saveSession, QKeySequence.Save)
        #cluster = menuitem("&Cluster", self.cluster, None)
        plot = self.addmenuitem("&Plot", self.plot, None)
        file_menu.addAction(open)
        file_menu.addAction(save)
        #file_menu.addAction(cluster)
        file_menu.addAction(plot)
 
        #---------------------------------
        # tagging tab UI elements
        #---------------------------------
        self.TopLevelLayout = QHBoxLayout()
        self.TextBox = QPlainTextEdit()
        self.DetailBoxLayout = QVBoxLayout()
        self.TechnologiesBoxLayout = QVBoxLayout()
        self.addtablayoutelements(self.TopLevelLayout, self.TextBox, self.DetailBoxLayout, self.TechnologiesBoxLayout)
        
        # add a button that allows for the removal of a listing if it is not relevant
        self.removeListingButton = QPushButton("Remove Listing")
        self.addlargebuttontolayout(self.removeListingButton, self.remove_listing, False, self.DetailBoxLayout)

        # populate the left side detail layout with the details box and the 
        self.BackButton = QPushButton("<--")
        self.FwdButton = QPushButton("-->")
        self.BackButton.setFixedSize(160, 18)
        self.FwdButton.setFixedSize(160, 18)
        self.BackButton.clicked.connect(self.previous_listing)
        self.FwdButton.clicked.connect(self.next_listing)
        self.BackButton.setEnabled(False)
        self.FwdButton.setEnabled(False)
        self.addwidgetpairtolayout(self.BackButton, self.FwdButton, self.DetailBoxLayout)

        # add in a textbox to allow the the number of clusters to be set
        self.ClusterSizeText = QLineEdit()
        self.createlabeltextboxpair("Clusters:", 160, 18, self.ClusterSizeText, "7", self.DetailBoxLayout)

        # add in a textbox to allow the the graph node filter size to be set
        self.GraphFilterText = QLineEdit()
        self.createlabeltextboxpair("FilterSize:", 160, 18, self.GraphFilterText, "3", self.DetailBoxLayout)

        # add in the ID labels
        self.IdValueLabel = QLabel("Placeholder Label")
        self.createlabelpair("ID:", 160, 18, self.IdValueLabel, self.DetailBoxLayout)

        # add in the title labels
        self.TitleValueLabel = QLabel("Placeholder Title")
        self.createlabelpair("TITLE:", 160, 18, self.TitleValueLabel, self.DetailBoxLayout)

        # add in the company labels
        self.CompanyValueLabel = QLabel("Placeholder Company")
        self.createlabelpair("COMPANY:", 160, 18, self.CompanyValueLabel, self.DetailBoxLayout)
        
        # add in the first detail labels
        self.Detail1ValueLabel = QLabel("Detail Placeholder")
        self.createlabelpair("DETAIL1:", 160, 18, self.Detail1ValueLabel, self.DetailBoxLayout)

        # add in the second detail labels
        self.Detail2ValueLabel = QLabel("Detail Placeholder")
        self.createlabelpair("DETAIL2:", 160, 18, self.Detail2ValueLabel, self.DetailBoxLayout)

        # add in the third detail labels
        self.Detail3ValueLabel = QLabel("Detail Placeholder")
        self.createlabelpair("DETAIL3:", 160, 18, self.Detail3ValueLabel, self.DetailBoxLayout)

        # add in the fourth detail labels
        self.Detail4ValueLabel = QLabel("Detail Placeholder")
        self.createlabelpair("DETAIL4:", 160, 18, self.Detail4ValueLabel, self.DetailBoxLayout)
        
        # populate the technology layout with the add technology text box and button
        self.TechnologyAddTextField = QLineEdit()
        self.TechnologyAddButton = QPushButton("+")
        self.TechnologyAddButton.clicked.connect(self.add_technology_lineItem)
        self.TechnologyAddTextField.setFixedSize(160, 18)
        self.TechnologyAddButton.setFixedSize(160, 18)
        self.TechnologyAddButton.setEnabled(False) #disable the technology add button till you have loaded a session
        self.addwidgetpairtolayout(self.TechnologyAddTextField, self.TechnologyAddButton, self.DetailBoxLayout)

        #---------------------------------
        # clustering tab UI elements
        #---------------------------------
        self.clusteringtoplevellayout = QHBoxLayout()
        self.clusteringtextbox = QPlainTextEdit()
        self.clusteringcontrolslayout = QVBoxLayout()
        self.clusteringtechnologieslayout = QVBoxLayout()
        self.addtablayoutelements(self.clusteringtoplevellayout, self.clusteringtextbox, self.clusteringcontrolslayout, self.clusteringtechnologieslayout)

        # features that have less than the minimum row count will not be added into the clustering algorithm
        self.minimumrowcount = QLineEdit()
        self.createlabeltextboxpair("min rows per tech:", 160, 18, self.minimumrowcount, "3", self.clusteringcontrolslayout)
        
        # the number of clusters that will be created during each iteration of the clustering algorithm
        self.numberofclusters = QLineEdit()
        self.createlabeltextboxpair("# clusters:", 160, 18, self.numberofclusters, "7", self.clusteringcontrolslayout)

        # minimum instances that are found by the clustering algorithm for a class to be considered
        self.minimumclasssize = QLineEdit()
        self.createlabeltextboxpair("min class size:", 160, 18, self.minimumclasssize, "5", self.clusteringcontrolslayout)

        # number of iterations to run the clustering algorithm to create the master classes
        self.clusteringiterations = QLineEdit()
        self.createlabeltextboxpair("# clustering iterations:", 160, 18, self.clusteringiterations, "50", self.clusteringcontrolslayout)
        
        # add a button to start the clustering process
        self.startclustering = QPushButton("start clustering")
        self.addlargebuttontolayout(self.startclustering, self.cluster, False, self.clusteringcontrolslayout)

        #---------------------------------
        # reporting tab UI elements
        #---------------------------------
        self.reportingtoplevellayout = QHBoxLayout()
        self.reportingtextbox = QPlainTextEdit()
        self.reportingcontrolslayout = QVBoxLayout()
        self.reportingtechnologieslayout = QVBoxLayout()
        self.addtablayoutelements(self.reportingtoplevellayout, self.reportingtextbox, self.reportingcontrolslayout, self.reportingtechnologieslayout)

        # number of top technologies related to the chosen technologies to add to the report
        self.numberoftoptechnologies = QLineEdit()
        self.createlabeltextboxpair("Top # associated tech:", 160, 18, self.numberoftoptechnologies, "15", self.reportingcontrolslayout)
        # thickest edge width
        self.thickestedgewidth = QLineEdit()
        self.createlabeltextboxpair("Max edge thickness:", 160, 18, self.thickestedgewidth, "15", self.reportingcontrolslayout)
        # largest node size
        self.largestnode = QLineEdit()
        self.createlabeltextboxpair("Largest node:", 160, 18, self.largestnode, "100", self.reportingcontrolslayout)
        # add a button to start the clustering process
        self.runreport = QPushButton("run single tech report")
        self.addlargebuttontolayout(self.runreport, self.springreportontech, False, self.reportingcontrolslayout)
        # add a label to indicate the function of the tickboxes below
        self.addlargelabeltolayout("select technology to report on", self.reportingcontrolslayout)

        #---------------------------------
        # Top level tab UI elements
        #---------------------------------
        
        self.window = QWidget()
        self.window.setLayout(self.TopLevelLayout)

        self.clusteringwindowtab = QWidget()
        self.clusteringwindowtab.setLayout(self.clusteringtoplevellayout)

        self.reportingwindowtab = QWidget()
        self.reportingwindowtab.setLayout(self.reportingtoplevellayout)

        self.WindowTabWidget = QTabWidget()
        self.WindowTabWidget.addTab(self.window, "tagging")
        self.WindowTabWidget.addTab(self.clusteringwindowtab, "clustering")
        self.WindowTabWidget.addTab(self.reportingwindowtab, "reporting")
        self.windowFrame.setCentralWidget(self.WindowTabWidget)


        self.windowFrame.show()
        #self.window.show()
        self.app.exec_()

    def addtablayoutelements(self, toplevellayout, textbox, detaillayout, technologieslayout):
        leftsidelayout = QVBoxLayout()
        # populate the top level layout with the left side layout and the text box
        textbox.setMinimumWidth(750)
        textbox.setMinimumHeight(800)
        toplevellayout.addLayout(leftsidelayout)
        toplevellayout.addWidget(textbox)

        detaillayout.setContentsMargins(0,0,0,0)
        detaillayout.setSpacing(0)
        detaillayout.setSizeConstraint(QLayout.SetFixedSize)
        detaillayout.setAlignment( QtCore.Qt.AlignTop)
        technologieslayout.setContentsMargins(0,0,20,0)
        technologieslayout.setSpacing(0)
        technologieslayout.setAlignment(QtCore.Qt.AlignTop)
        
        detailwidget = QWidget()
        detailwidget.setLayout(detaillayout)
        detailwidget.setMaximumHeight(300)
        technologiesboxwidget = QWidget()
        technologiesboxwidget.setLayout(technologieslayout)
        technologiesscrollarea = QScrollArea()
        technologiesscrollarea.setWidget(technologiesboxwidget)
        technologiesscrollarea.setWidgetResizable(True)
        technologiesscrollarea.horizontalScrollBar().setEnabled(False)
        technologiesscrollarea.horizontalScrollBar().setVisible(False)
        technologiesscrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        leftsidelayout.addWidget(detailwidget)
        leftsidelayout.addWidget(technologiesscrollarea)

    def addmenuitem(self, actionname, functionname, shortcut):
        itemtoadd = QAction(actionname)
        if shortcut:
            itemtoadd.setShortcut(shortcut)
        itemtoadd.triggered.connect(functionname)
        return itemtoadd
    
    def addwidgetpairtolayout(self, leftwidget, rightwidget, layout, optionalwidget = None):
        layoutbox = QHBoxLayout()
        layoutbox.setSpacing(0)
        layoutbox.setContentsMargins(0,0,0,0)
        layoutbox.addWidget(leftwidget)
        layoutbox.addWidget(rightwidget)
        if optionalwidget is not None:
            layoutbox.addWidget(optionalwidget)
        layout.addLayout(layoutbox)

    def addlargebuttontolayout(self, button, funcpointer, enabledstate, layouttoaddto):
        button.setFixedSize(320, 18)
        button.clicked.connect(funcpointer)
        button.setEnabled(enabledstate)
        layouttoaddto.addWidget(button)

    def addlargelabeltolayout(self, text, layouttoaddto):
        label = QLabel(text)
        label.setFixedSize(320, 18)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layouttoaddto.addWidget(label)

    def createlabeltextboxpair(self, labeltitle, width, height, textfield, textfieldtext, detailboxlayout):
        keylabel = QLabel(labeltitle)
        textfield.setText(textfieldtext)
        keylabel.setFixedSize(width, height)
        textfield.setFixedSize(width, height)
        textfield.setAlignment(QtCore.Qt.AlignRight)
        self.addwidgetpairtolayout(keylabel, textfield, detailboxlayout)

    def createlabelpair(self, labeltitle, width, height, valuelabel, detailboxlayout):
        keylabel = QLabel(labeltitle)
        # self.TitleValueLabel = QLabel("Placeholder Title")
        keylabel.setFixedSize(width, height)
        valuelabel.setFixedSize(width, height)
        valuelabel.setAlignment(QtCore.Qt.AlignRight)
        self.addwidgetpairtolayout(keylabel, valuelabel, detailboxlayout)

    def show_open_file_dialog(self):
        path = QFileDialog.getOpenFileName(self.windowFrame, "Open")[0]
        if path:
            self.path_to_scrape_session = path
            self.load_session()

    def saveSession(self):
        if self.path_to_coding_session:
            # where technologies have been deactivated delete them
            for technology in self.technologies:
                if not technology.active:
                    if technology.name in self.codingSessionData:
                        self.codingSessionData.drop(columns=technology.name, inplace=True)
            sessionFile = open(self.path_to_coding_session, 'wb') # write binary
            pickle.dump(self.codingSessionData, sessionFile)
            sessionFile.close()
            self.windowFrame.clean()

    def remove_listing(self):
        self.codingSessionData.drop(self.listingNumber, inplace=True)
        currentIndex = self.listingNumber
        checkforindex = self.listingNumber + 1
        foundANextIndex = False
        while checkforindex < len(self.scrapeSessionData):
            if checkforindex in self.codingSessionData.index:
                currentIndex = checkforindex
                foundANextIndex = True
                break
            else:
                checkforindex = checkforindex + 1
        if foundANextIndex:
            self.listingNumber = currentIndex
            self.load_listing(self.listingNumber)
            self.windowFrame.dirty()
            print("drop listing")
        else:
            self.previous_listing()

    def previous_listing(self):
        currentIndex = self.listingNumber
        checkforindex = self.listingNumber - 1
        while checkforindex >= 0:
            if checkforindex in self.codingSessionData.index:
                currentIndex = checkforindex
                break
            else:
                checkforindex = checkforindex -1
        self.listingNumber = currentIndex
        self.load_listing(self.listingNumber)        
        print("previous listing")

    def next_listing(self):
        self.codingSessionData.at[self.listingNumber, 'Coded'] = True
        currentIndex = self.listingNumber
        checkforindex = self.listingNumber + 1
        while checkforindex < len(self.scrapeSessionData):
            if checkforindex in self.codingSessionData.index:
                currentIndex = checkforindex
                break
            else:
                checkforindex = checkforindex + 1
        self.listingNumber = currentIndex
        self.load_listing(self.listingNumber)
        self.windowFrame.dirty()
        print("next listing")

    def cluster(self):
        head, tail = os.path.split(self.path_to_scrape_session)
        session = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        pathToDumpReports = head + f'/clustering_{session}'
        textresult = clusterAveKMeans(self.clusteringiterations.text(), 
                        self.codingSessionData, 
                        self.technologies, 
                        self.minimumrowcount.text(), 
                        self.numberofclusters.text(), 
                        self.minimumclasssize.text(), 
                        pathToDumpReports)
        self.clusteringtextbox.setPlainText(textresult)

    def springreportontech(self):
        # each of the technologies selected must be represented in each row. for each that is selected on in the report remove all rows where it is not 1
        numberoftoptechnologies = int(self.numberoftoptechnologies.text())
        thickestedgewidth = int(self.thickestedgewidth.text())
        largestcircle = int(self.largestnode.text())
        reportingdataframe= self.codingSessionData.copy()
        reportingdataframe = reportingdataframe[reportingdataframe.Coded != False]
        reportingdataframe = reportingdataframe.drop(columns=['ID', 'Coded'])
        for technology in self.technologies:
            if technology.reporton:
                reportingdataframe = reportingdataframe[reportingdataframe[technology.name].isin([1])]
        # now that the rows have been deleted, delete columns where there are no 1s
        columnstodrop = []
        columnswithsum = []
        for column in reportingdataframe:
            colsum = reportingdataframe[column].sum()
            if colsum == 0:
                columnstodrop.append(column)
            else:
                columnswithsum.append((column, colsum))
        # removing the empty columns
        reportingdataframe = reportingdataframe.drop(columns=columnstodrop)
        #print(columnswithsum)
        # removing the columns that are not in the top X number
        toptechnologies = sorted(columnswithsum, key=lambda kv: kv[1], reverse=True) [:numberoftoptechnologies]
        columnstodrop = list(reportingdataframe.columns)
        for toptech in toptechnologies:
            columnstodrop.remove(toptech[0])
        reportingdataframe = reportingdataframe.drop(columns=columnstodrop)

        #print(reportingdataframe)
        createtechnologyassociationgraph(reportingdataframe, thickestedgewidth, largestcircle)

    def plot(self):
        # you can plot either the recreated frame or the original coded data as a plot
        clusterdataframe = self.codingSessionData.copy()
        clusterdataframe = clusterdataframe[clusterdataframe.Coded != False]
        clusterdataframe = clusterdataframe.drop(columns=['ID', 'Coded'])
        create_analytics_graph(clusterdataframe, int(self.GraphFilterText.text()), 'circular', self.technologies)
        create_analytics_graph(clusterdataframe, int(self.GraphFilterText.text()), 'spring', self.technologies)
    
    def load_session(self):
        print("load session")
        head, tail = os.path.split(self.path_to_scrape_session)
        print(head)
        print(tail)
        secondaryScrapeReadfile = open(self.path_to_scrape_session, 'rb')
        self.scrapeSessionData = pickle.load(secondaryScrapeReadfile)
        secondaryScrapeReadfile.close()
        # in the same directory, check if there is already coding session file. if not, create one.
        if os.path.isfile(head+'/codingSession'):
            self.path_to_coding_session = head+'/codingSession'
            codingSessionFile = open(self.path_to_coding_session, 'rb')
            self.codingSessionData = pickle.load(codingSessionFile)
            codingSessionFile.close()
        else:
            # build a dataframe line for line from the scraped data
            self.codingSessionData = pd.DataFrame(columns=['ID', 'Coded'])
            for listing in self.scrapeSessionData:
                self.codingSessionData.loc[len(self.codingSessionData)] = [listing.id, False]
            self.path_to_coding_session = head+'/codingSession'
            self.saveSession()
        #testing quick
        testFile = open(self.path_to_coding_session, 'rb')
        testData = pickle.load(testFile)
        testFile.close()
        print(testData)
        #enable the technology add button so you can now add technologies
        self.TechnologyAddButton.setEnabled(True)
        self.BackButton.setEnabled(True)
        self.FwdButton.setEnabled(True)
        self.removeListingButton.setEnabled(True)
        self.startclustering.setEnabled(True)
        self.runreport.setEnabled(True)
        self.load_technology_columns()
        self.listingNumber = 0
        lastIndex = 0
        foundIndex = False
        # todo - check for the first listing in the session that hasn't been coded
        for index, row in self.codingSessionData.iterrows():
            lastIndex = index
            if self.codingSessionData.at[index, 'Coded'] == False:
                foundIndex = True
                self.listingNumber = index
                break
        # if all of the indexes have been coded then load the last index found
        if not foundIndex:
            self.listingNumber = lastIndex
        self.load_listing(self.listingNumber)
    
    def load_technology_columns(self):
        # load in the columns from the session as button groups
        print("load technologies")
        index = 0
        for column in self.codingSessionData.columns:
            if column != 'ID' and column != 'Coded':
                self.add_technolgy(column, index, False)
                index = index + 1
        self.reorder_technologies()
        self.technologyCounter = index

    def load_listing(self, number):
        if len(self.scrapeSessionData) > number:
            listing = self.scrapeSessionData[number]
            self.IdValueLabel.setText(listing.id)
            self.TitleValueLabel.setText(listing.title)
            self.CompanyValueLabel.setText(listing.company)
            self.Detail1ValueLabel.setText("")
            self.Detail2ValueLabel.setText("")
            self.Detail3ValueLabel.setText("")
            self.Detail4ValueLabel.setText("")
            if len(listing.details) > 1:
                self.Detail1ValueLabel.setText(listing.details[0][1])
            if len(listing.details) > 2:
                self.Detail2ValueLabel.setText(listing.details[1][1])
            if len(listing.details) > 3:
                self.Detail3ValueLabel.setText(listing.details[2][1])
            if len(listing.details) > 4:
                self.Detail4ValueLabel.setText(listing.details[3][1])
            self.TextBox.setPlainText(listing.title + "\n" + listing.text)
            # loop over the technologies and set the radio buttons to match
            for technology in self.technologies:
                if technology.active:
                    if self.codingSessionData.at[self.listingNumber, technology.name] == 1.0:
                        technology.setPresent()
                    else:
                        technology.setNotPresent()

    def yes_function(self, technology):
        self.codingSessionData.at[self.listingNumber, technology] = 1.0
        self.windowFrame.dirty()
        print(f'{technology}: yes')

    def no_function(self, technology):
        self.codingSessionData.at[self.listingNumber, technology] = 0.0
        self.windowFrame.dirty()
        print(f'{technology}: no')
    
    def filterfunction(self, technologyfiltercheckbox, technologyLineItem):
        if technologyfiltercheckbox.isChecked():
            technologyLineItem.enablefilter()
        else:
            technologyLineItem.disablefilter()

    def reportselectfunction(self, reportselectcheckbox, technologyLineItem):
        if reportselectcheckbox.isChecked():
            technologyLineItem.enablereporton()
        else:
            technologyLineItem.disablereporton()

    def add_technolgy(self, techName, techNumber, startSelected):
        # add the technology group to the tagging tab
        technologyLineLayout = QHBoxLayout()
        technologyLineLayout.setContentsMargins(0,0,0,0)
        technologyLineLayout.setSpacing(0)
        technologyLabel = QLabel(techName)
        technologyLabel.setMinimumWidth(150)
        technologyPresent = QRadioButton("yes")
        technologyNotPresent = QRadioButton("no")
        if startSelected:
            technologyPresent.setChecked(True)
        else:
            technologyNotPresent.setChecked(True)
        deleteTechnology = QPushButton("-")
        technologyLineLayout.addWidget(technologyLabel)
        technologyLineLayout.addWidget(technologyPresent)
        technologyLineLayout.addWidget(technologyNotPresent)
        technologyLineLayout.addWidget(deleteTechnology)
        yesFunction= lambda: self.yes_function(techName)
        noFunction= lambda: self.no_function(techName)
        technologyPresent.clicked.connect(yesFunction)
        technologyNotPresent.clicked.connect(noFunction)
        groupBox = QGroupBox()
        groupBox.setLayout(technologyLineLayout)
        groupBox.setMaximumHeight(35)
        technologyfilterline = QWidget()
        reportselectline = QWidget()
        technologyLineItem = TechnologyLineItem(techName, groupBox, yesFunction, noFunction, self.technologyCounter, technologyPresent, technologyNotPresent, technologyfilterline, reportselectline)
        deleteTechnology.clicked.connect(technologyLineItem.deactivate)
        deleteTechnology.clicked.connect(self.reorder_technologies)
        self.technologies.append(technologyLineItem)
        self.TechnologiesBoxLayout.addWidget(groupBox) 
        #add the filter controls
        technologyfilterlinelayout = QHBoxLayout()
        technologyfilterlinelayout.setContentsMargins(0,0,0,0)
        technologyfilterlinelayout.setSpacing(0)
        technologyfilterlabel = QLabel(techName)
        technologyfilterlabel.setMinimumWidth(150)
        technologyfiltercheckbox = QCheckBox()
        filtercheckfunction = lambda: self.filterfunction(technologyfiltercheckbox, technologyLineItem)
        technologyfiltercheckbox.stateChanged.connect(filtercheckfunction)
        technologyfilterlinelayout.addWidget(technologyfilterlabel)
        technologyfilterlinelayout.addWidget(technologyfiltercheckbox)
        technologyfilterline.setLayout(technologyfilterlinelayout)
        self.clusteringtechnologieslayout.addWidget(technologyfilterline) 
        # add the report controls
        reportselectlinelayout = QHBoxLayout()
        reportselectlinelayout.setContentsMargins(0,0,0,0)
        reportselectlinelayout.setSpacing(0)
        reportselectlabel = QLabel(techName)
        reportselectlabel.setMinimumWidth(150)
        reportselectcheckbox = QCheckBox()
        reportselectfunction = lambda: self.reportselectfunction(reportselectcheckbox, technologyLineItem)
        reportselectcheckbox.stateChanged.connect(reportselectfunction)
        reportselectlinelayout.addWidget(reportselectlabel)
        reportselectlinelayout.addWidget(reportselectcheckbox)
        reportselectline.setLayout(reportselectlinelayout)
        self.reportingtechnologieslayout.addWidget(reportselectline) 
        
    def reorder_technologies(self):
         # remove all of the line items you had except for the technology add line, sort them by name, and re-add them
        for technology in self.technologies:
            self.TechnologiesBoxLayout.removeWidget(technology.groupBox)
            self.clusteringtechnologieslayout.removeWidget(technology.filterwidget)
            self.reportingtechnologieslayout.removeWidget(technology.reportingwidget)
        self.technologies.sort(key= lambda x: x.name.lower()) 
        self.technologies.sort(key= lambda x: x.active, reverse=True) # move deactivated items to the end of the list
        for technology in self.technologies:
            self.TechnologiesBoxLayout.addWidget(technology.groupBox)
            self.clusteringtechnologieslayout.addWidget(technology.filterwidget) 
            self.reportingtechnologieslayout.addWidget(technology.reportingwidget)
            if not technology.active:
                technology.groupBox.setEnabled(False)

    def add_technology_lineItem(self):
        found = False
        for technology in self.technologies:
            if technology.name.lower() == self.TechnologyAddTextField.text().lower():
                self.codingSessionData.at[self.listingNumber, technology.name] = 1.0
                self.windowFrame.dirty()
                technology.setPresent()
                found = True
        if not found:
            self.add_technolgy(self.TechnologyAddTextField.text(), self.technologyCounter, True)
            self.technologyCounter = self.technologyCounter + 1
            self.codingSessionData[self.TechnologyAddTextField.text()] = np.zeros(len(self.codingSessionData))
            self.reorder_technologies()
            self.codingSessionData.at[self.listingNumber, self.TechnologyAddTextField.text()] = 1.0
            self.TechnologyAddTextField.setText("")
            self.windowFrame.dirty()
            print(f"Added {self.TechnologyAddTextField.text()} technology")
            print(self.codingSessionData)

if __name__ == "__main__":
    # execute only if run as a script
    GUI = CodingApp()