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
from bmdcluster import * 

#from clustering import clusterusingbmdtextoutput,clusterusingbmdpercentageoutput, clusterAveKMeans
from clustering import clusterAveKMeans

import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import random
import math
import time
from datetime import datetime

class TechnologyLineItem:
    def __init__(self, name, groupBox, presentFunction, notPresentFunction, columnNumber, technologyPresent, technologyNotPresent, filterlayout):
        self.name = name
        self.groupBox = groupBox
        self.presentFunction = presentFunction
        self.notPresentFunction = notPresentFunction
        self.columnNumber = columnNumber
        self.active = True
        self.technologyPresent = technologyPresent
        self.technologyNotPresent = technologyNotPresent
        self.filtered = False
        self.filterwidget = filterlayout
    
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
        self.LeftSideLayout = QVBoxLayout()

        # populate the top level layout in the tagging tab
        self.TextBox = QPlainTextEdit()
        self.TextBox.setMinimumWidth(750)
        self.TextBox.setMinimumHeight(800)
        self.TopLevelLayout.addLayout(self.LeftSideLayout)
        self.TopLevelLayout.addWidget(self.TextBox)

        self.DetailBoxLayout = QVBoxLayout()
        self.DetailBoxLayout.setContentsMargins(0,0,0,0)
        self.DetailBoxLayout.setSpacing(0)
        self.DetailBoxLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.DetailBoxLayout.setAlignment( QtCore.Qt.AlignTop)
        self.TechnologiesBoxLayout = QVBoxLayout()
        self.TechnologiesBoxLayout.setContentsMargins(0,0,20,0)
        self.TechnologiesBoxLayout.setSpacing(0)
        self.TechnologiesBoxLayout.setAlignment( QtCore.Qt.AlignTop)
        
        self.DetailWidget = QWidget()
        self.DetailWidget.setLayout(self.DetailBoxLayout)
        self.DetailWidget.setMaximumHeight(300)
        self.TechnologiesBoxWidget = QWidget()
        self.TechnologiesBoxWidget.setLayout(self.TechnologiesBoxLayout)
        self.TechnologiesScrollArea = QScrollArea()
        self.TechnologiesScrollArea.setWidget(self.TechnologiesBoxWidget)
        self.TechnologiesScrollArea.setWidgetResizable(True)
        self.TechnologiesScrollArea.horizontalScrollBar().setEnabled(False)
        self.TechnologiesScrollArea.horizontalScrollBar().setVisible(False)
        self.TechnologiesScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.LeftSideLayout.addWidget(self.DetailWidget)
        self.LeftSideLayout.addWidget(self.TechnologiesScrollArea)
        
        # add a button that allows for the removal of a listing if it is not relevant
        self.removeListingButton = QPushButton("Remove Listing")
        self.removeListingButton.setFixedSize(320, 18)
        self.removeListingButton.clicked.connect(self.remove_listing)
        self.removeListingButton.setEnabled(False)
        self.DetailBoxLayout.addWidget(self.removeListingButton)

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
        self.clusteringleftsidelayout = QVBoxLayout()

        # populate the top level layout in the clustering tab
        self.clusteringtextbox = QPlainTextEdit()
        self.clusteringtextbox.setMinimumWidth(750)
        self.clusteringtextbox.setMinimumHeight(800)
        self.clusteringtoplevellayout.addLayout(self.clusteringleftsidelayout)
        self.clusteringtoplevellayout.addWidget(self.clusteringtextbox)

        self.clusteringcontrolslayout = QVBoxLayout()
        self.clusteringcontrolslayout.setContentsMargins(0,0,0,0)
        self.clusteringcontrolslayout.setSpacing(0)
        self.clusteringcontrolslayout.setSizeConstraint(QLayout.SetFixedSize)
        self.clusteringcontrolslayout.setAlignment( QtCore.Qt.AlignTop)
        self.clusteringtechnologieslayout = QVBoxLayout()
        self.clusteringtechnologieslayout.setContentsMargins(0,0,20,0)
        self.clusteringtechnologieslayout.setSpacing(0)
        self.clusteringtechnologieslayout.setAlignment( QtCore.Qt.AlignTop)

        self.clusteringcontrols = QWidget()
        self.clusteringcontrols.setLayout(self.clusteringcontrolslayout)
        self.clusteringcontrols.setMaximumHeight(300)
        
        self.clusteringtechnologies = QWidget()
        self.clusteringtechnologies.setLayout(self.clusteringtechnologieslayout)
        self.clusteringtechnologiesscrollarea = QScrollArea()
        self.clusteringtechnologiesscrollarea.setWidget(self.clusteringtechnologies)
        self.clusteringtechnologiesscrollarea.setWidgetResizable(True)
        self.clusteringtechnologiesscrollarea.horizontalScrollBar().setEnabled(False)
        self.clusteringtechnologiesscrollarea.horizontalScrollBar().setVisible(False)
        self.clusteringtechnologiesscrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.clusteringleftsidelayout.addWidget(self.clusteringcontrols)
        self.clusteringleftsidelayout.addWidget(self.clusteringtechnologiesscrollarea)

        # features that have less than the minimum row count will not be added into the clustering algorithm
        self.minimumrowcount = QLineEdit()
        self.createlabeltextboxpair("min rows per tech:", 160, 18, self.minimumrowcount, "3", self.clusteringcontrolslayout)
        
        # the number of clusters that will be created during each iteration of the clustering algorithm
        self.numberofclusters = QLineEdit()
        self.createlabeltextboxpair("# clusters:", 160, 18, self.numberofclusters, "7", self.clusteringcontrolslayout)

        # max technologies considered in a class - only the top most relevant technologies are used to define the class characteristics
        # self.numberoftechnologies = QLineEdit()
        # self.createlabeltextboxpair("max # tech per class:", 160, 18, self.numberoftechnologies, "10", self.clusteringcontrolslayout)
        
        # minimum percentage of members of class that have the technology for it to be considered
        # self.minimumpercentage = QLineEdit()
        # self.createlabeltextboxpair("min tech % representation:", 160, 18, self.minimumpercentage, "50", self.clusteringcontrolslayout)
        
        # minimum instances that are found by the clustering algorithm for a class to be considered
        self.minimumclasssize = QLineEdit()
        self.createlabeltextboxpair("min class size:", 160, 18, self.minimumclasssize, "5", self.clusteringcontrolslayout)

        # number of iterations to run the clustering algorithm to create the master classes
        self.clusteringiterations = QLineEdit()
        self.createlabeltextboxpair("# clustering iterations:", 160, 18, self.clusteringiterations, "50", self.clusteringcontrolslayout)
        
        # add a button to start the clustering process
        self.startclustering = QPushButton("start clustering")
        self.startclustering.setFixedSize(320, 18)
        self.startclustering.clicked.connect(self.cluster)
        self.startclustering.setEnabled(False)
        self.clusteringcontrolslayout.addWidget(self.startclustering)

        #---------------------------------
        # Top level tab UI elements
        #---------------------------------
        
        self.window = QWidget()
        self.window.setLayout(self.TopLevelLayout)

        self.clusteringwindowtab = QWidget()
        self.clusteringwindowtab.setLayout(self.clusteringtoplevellayout)

        self.WindowTabWidget = QTabWidget()
        self.WindowTabWidget.addTab(self.window, "tagging")
        self.WindowTabWidget.addTab(self.clusteringwindowtab, "clustering")
        self.windowFrame.setCentralWidget(self.WindowTabWidget)


        self.windowFrame.show()
        #self.window.show()
        self.app.exec_()

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

    def plot(self):
        # you can plot either the recreated frame or the original coded data as a plot
        clusterdataframe = self.codingSessionData.copy()
        clusterdataframe = clusterdataframe[clusterdataframe.Coded != False]
        clusterdataframe = clusterdataframe.drop(columns=['ID', 'Coded'])
        self.create_analytics_graph(clusterdataframe, int(self.GraphFilterText.text()), 'circular')
        self.create_analytics_graph(clusterdataframe, int(self.GraphFilterText.text()), 'spring')
    
    def create_analytics_graph(self, recreatedFrame, sizeFilter, layoutType):
        G = nx.Graph()
        # reset a counter for each technology
        for technology in self.technologies:
            technology.counter = 0
        for index, row in recreatedFrame.iterrows():
            # each technology that is in the row needs a edge to each other technology in the row - just grab their names for now
            technologyNames = []
            for technology in self.technologies:
                if recreatedFrame.at[index, technology.name] == 1:
                        technology.counter = technology.counter + 1
                        if technology.counter >= sizeFilter:
                            technologyNames.append(technology.name)
            # if only one technology is chosen, it will have no edges, so pop first. 
            if len(technologyNames) > 0:
                currentName = technologyNames.pop()
                while len(technologyNames) > 0:
                    for name in technologyNames:
                        if G.has_edge(currentName, name):
                            G[currentName][name]['count'] = G[currentName][name]['count'] + 1
                        else:
                            G.add_edge(currentName, name)
                            G[currentName][name]['count'] = 1
                    currentName = technologyNames.pop()
        # only add nodes for technologies with at least 1 connection
        self.technologies.sort(key= lambda x: x.counter, reverse=True) 

        for technology in self.technologies:
            if technology.counter >= sizeFilter:
                G.add_node(technology.name)
                #G.nodes[technology.name]['pos'] = (random.randint(0,800),random.randint(0,800))
                G.nodes[technology.name]['name'] = technology.name

        if layoutType == 'circular':
            positions = nx.circular_layout(G)
        else:
            positions = nx.spring_layout(G)
        #print(positions)

        for position in positions:
            G.nodes[position]['pos'] = (positions[position][0],positions[position][1])

        for technology in self.technologies:
            print(f"{technology.name}: {technology.counter}")
        self.reorder_technologies()

        traces = []
        print('creating edges')
        for edge in G.edges():
            #print(f'creating edge {edge[0]} to {edge[1]}')
            x0, y0 = G.node[edge[0]]['pos']
            x1, y1 = G.node[edge[1]]['pos']
            if x1 > x0 and y1 > y0:
                x2 = x0 + (x1 - x0)/2 
                y2 = y0 + (y1 - y0)/2
            if x1 < x0 and y1 > y0:
                x2 = x1 + (x0 - x1)/2 
                y2 = y0 + (y1 - y0)/2
            if x1 < x0 and y1 < y0:
                x2 = x1 + (x0 - x1)/2 
                y2 = y1 + (y0 - y1)/2
            if x1 > x0 and y1 < y0:
                x2 = x0 + (x1 - x0)/2 
                y2 = y1 + (y0 - y1)/2
            linelength = math.sqrt((x0-x1)*(x0-x1) + (y0-y1)*(y0-y1))
            z = linelength * random.randint(10,20)/100
            if x2 <= 0 and y2 <= 0:
                x2 = x2 + z
                y2 = y2 + z
                colorSel = "rgba(255, 0, 0, 1)"
            elif x2 >= 0 and y2 <= 0:
                x2 = x2 - z
                y2 = y2 + z
                colorSel = "rgba(0, 255, 0, 1)"
            elif x2 <= 0 and y2 >= 0:
                x2 = x2 + z
                y2 = y2 - z
                colorSel = "rgba(0, 0, 255, 1)"
            else:
                x2 = x2 - z
                y2 = y2 - z
                colorSel = "rgba(100, 100, 100, 1)"
            widthCount = G[edge[0]][edge[1]]['count']/2
            traces.append(go.Scatter(
                x=(x0,x2,x1),
                y=(y0,y2,y1),
                line=dict(width = widthCount, color=colorSel, shape = 'spline'),
                hoverinfo='none',
                mode='lines'
            ))


        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = G.node[node]['pos']
            node_x.append(x)
            node_y.append(y)
            node_text.append(G.node[node]['name'])
            #node_text.append(f"{G.node[node]['name']} : {G.node[node]['pos']}")
        
        print(f'creating node trace')
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            marker_color = 'rgba(158, 0, 0, 1)',
            opacity=1,
            textfont=dict(size=18),
            marker=dict(
                showscale=True,
                # colorscale options
                #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
                #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
                #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
                colorscale='Reds',
                reversescale=True,
                color='Black',
                opacity=1,
                size=30,
                colorbar=dict(
                    thickness=15,
                    title='Node Connections',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2))

        node_adjacencies = []
        for node, adjacencies in enumerate(G.adjacency()):
            node_adjacencies.append(len(adjacencies[1])*2)

        node_trace.marker.size = node_adjacencies
        node_trace.text = node_text

        traces.append(node_trace)
        print('creating plot')
        fig = go.Figure(data=traces,
             layout=go.Layout(
                title='<br>Technology Relationship Graph',
                titlefont_size=16,
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Python code: <a href='https://plot.ly/ipython-notebooks/network-graphs/'> https://plot.ly/ipython-notebooks/network-graphs/</a>",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
        fig.update_traces(textposition='top center')
        print('showing plot')
        fig.show()

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
        technologyLineItem = TechnologyLineItem(techName, groupBox, yesFunction, noFunction, self.technologyCounter, technologyPresent, technologyNotPresent, technologyfilterline)
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
        


    def reorder_technologies(self):
         # remove all of the line items you had except for the technology add line, sort them by name, and re-add them
        for technology in self.technologies:
            self.TechnologiesBoxLayout.removeWidget(technology.groupBox)
            self.clusteringtechnologieslayout.removeWidget(technology.filterwidget)
        self.technologies.sort(key= lambda x: x.name.lower()) 
        self.technologies.sort(key= lambda x: x.active, reverse=True) # move deactivated items to the end of the list
        for technology in self.technologies:
            self.TechnologiesBoxLayout.addWidget(technology.groupBox)
            self.clusteringtechnologieslayout.addWidget(technology.filterwidget) 
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