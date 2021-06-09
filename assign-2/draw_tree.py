# sudo python3 -m pip install networkx
# sudo python3 -m pip install pydot
# sudo python3 -m pip install graphviz
# sudo apt-get install graphviz libgraphviz-dev pkg-config
# sudo python3 -m pip install pygraphviz

import sys
import matplotlib.pyplot as plt
import networkx as nx
import sqlite3

if len(sys.argv) != 2:
    print("ERROR: Usage: python3 draw_tree.py <dbname>")
    exit(1)
db_file = sys.argv[1]
tablename = "Test"
conn=sqlite3.connect(db_file)
cursor = conn.execute("SELECT previous_hash, current_hash from "+str(tablename))
nodes = set()
edges = [(row[0], row[1]) for row in cursor]
edges.remove(('0', '9e1c'))
for edge in edges:
    nodes.add(edge[0])
    nodes.add(edge[1])
nodes = list(nodes)
g = nx.DiGraph()
g.add_edges_from(edges)
g.add_nodes_from(nodes)

nx.nx_pydot.write_dot(g,'DiGraph.dot')
pos = nx.drawing.nx_agraph.graphviz_layout(g, prog='dot')
nx.draw_networkx_nodes(g,pos,node_size=500, nodelist=nodes, node_shape='s', node_color='b')
nx.draw_networkx_labels(g,pos,font_size=10,font_family='sans-serif')
nx.draw_networkx_edges(g,pos,edgelist=edges)
plt.show()