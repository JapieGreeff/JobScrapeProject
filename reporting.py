import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import math
import random

def createsplinelines(G, thickestedge, maxedgewidth):
    traces = []
    divider = thickestedge / maxedgewidth
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
            colorSel = "rgba(100, 100, 100, 0.4)"
        elif x2 >= 0 and y2 <= 0:
            x2 = x2 - z
            y2 = y2 + z
            colorSel = "rgba(100, 100, 100, 0.4)"
        elif x2 <= 0 and y2 >= 0:
            x2 = x2 + z
            y2 = y2 - z
            colorSel = "rgba(100, 100, 100, 0.4)"
        else:
            x2 = x2 - z
            y2 = y2 - z
            colorSel = "rgba(100, 100, 100, 0.4)"
        widthCount = max(G[edge[0]][edge[1]]['count']/divider, 1)
        traces.append(go.Scatter(
            x=(x0,x2,x1),
            y=(y0,y2,y1),
            line=dict(width = widthCount, color=colorSel, shape = 'spline'),
            hoverinfo='none',
            mode='lines'
        ))
    return traces

def createtechnologyassociationgraph(dataframe, maxedgewidth, maxnodesize):
    G = nx.Graph()
    thickestedge = 0
    for index, row in dataframe.iterrows():
        technologyNames = []
        for col in dataframe.columns:
            if dataframe.at[index, col] == 1:
                technologyNames.append(col)
        if len(technologyNames) > 0:
            currentName = technologyNames.pop()
            while len(technologyNames) > 0:
                for name in technologyNames:
                    if G.has_edge(currentName, name):
                        G[currentName][name]['count'] = G[currentName][name]['count'] + 1
                    else:
                        G.add_edge(currentName, name)
                        G[currentName][name]['count'] = 1
                    if G[currentName][name]['count'] > thickestedge:
                        thickestedge = G[currentName][name]['count']
                currentName = technologyNames.pop()
    # add in the nodes for the graph
    for col in dataframe.columns:
        G.add_node(col)
        G.nodes[col]['name'] = col
    # use a spring layout
    # positions = nx.spring_layout(G)
    positions = nx.circular_layout(G)
    for position in positions:
	    G.nodes[position]['pos'] = (positions[position][0],positions[position][1])
    # make all the traces splines 
    traces = createsplinelines(G, thickestedge, maxedgewidth)
    
    node_x = []
    node_y = []
    node_size = []
    node_text = []
    dataframenumrows = len(dataframe.index)
    divider = dataframenumrows / maxnodesize
    for node in G.nodes():
        x, y = G.node[node]['pos']
        node_x.append(x)
        node_y.append(y)
        node_size.append(max(dataframe[G.node[node]['name']].sum()/divider, 1))
        node_text.append(f"{G.node[node]['name']} ({round(100*int(dataframe[G.node[node]['name']].sum())/dataframenumrows)}%)")
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

    # node_adjacencies = []
    # for node, adjacencies in enumerate(G.adjacency()):
    #     #node_adjacencies.append(len(adjacencies[1])*2)
    #     colsum = dataframe[node['name']].sum()
    #     node_adjacencies.append(colsum)

    #node_trace.marker.size = node_adjacencies
    node_trace.marker.size = node_size
    node_trace.text = node_text

    traces.append(node_trace)
    print('creating plot')
    fig = go.Figure(data=traces,
            layout=go.Layout(
            title=f'<br>Technology Relationship Graph n = {dataframenumrows}',
            titlefont_size=16,
            showlegend=False,
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


def create_analytics_graph(recreatedFrame, sizeFilter, layoutType, technologies):
        G = nx.Graph()
        # reset a counter for each technology
        for technology in technologies:
            technology.counter = 0
        for index, row in recreatedFrame.iterrows():
            # each technology that is in the row needs a edge to each other technology in the row - just grab their names for now
            technologyNames = []
            for technology in technologies:
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
        technologies.sort(key= lambda x: x.counter, reverse=True) 

        for technology in technologies:
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
