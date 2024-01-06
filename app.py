
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import os
import io
import base64

class TrieNode:
    def __init__(self):
        self.children = {}
        self.passenger_details = None

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, name, details):
        node = self.root
        for char in name:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.passenger_details = details

    def search(self, name):
        node = self.root
        for char in name:
            if char not in node.children:
                return None
            node = node.children[char]
        return node.passenger_details

app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nivetha@1065'
app.config['MYSQL_DB'] = 'nivi'

mysql = MySQL(app)

flight_queues = {
    'Emirates ': [],
    'Air India': [],
    'Indigo': []
}

graph = {
    'Emirates ': ['D1', 'D2'],
    'Air India': ['D3', 'D4'],
    'Indigo': ['D5', 'D6']
}

passenger_trie = Trie()  

@app.route('/')
def home():
    return render_template('home.html', flights=flight_queues.keys())

@app.route('/add_passenger', methods=['POST'])
def add_passenger():
    name = request.form['name']
    flight_name = request.form['flight_name']
    reason = request.form['reason']
    destination = request.form['destination']

    if reason == 'medical':
        priority = 1
    elif reason == 'business':
        priority = 2
    elif reason == 'personal':
        priority = 3
    elif reason == 'studies':
        priority = 4
    else:
        return "Invalid reason"

    passenger = (priority, name, reason, destination)

    if flight_name not in flight_queues:
        flight_queues[flight_name] = []

    heapq.heappush(flight_queues[flight_name], passenger)
    passenger_trie.insert(name, passenger) 
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO passengers (name, flight_name, reason, destination, priority) VALUES (%s, %s, %s, %s, %s)",
                (name, flight_name, reason, destination, priority))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('home'))

@app.route('/view_tables')
def view_tables():
    sorted_flight_queues = {flight: sorted(passengers) for flight, passengers in flight_queues.items()}
    return render_template('view_tables.html', flight_queues=sorted_flight_queues)

@app.route('/graph')
def view_graph():
    G = nx.Graph()

    
    for flight in graph.keys():
        G.add_node(flight, type='flight')

    
    for destinations in graph.values():
        for destination in destinations:
            G.add_node(destination, type='destination')

    
    for flight, destinations in graph.items():
        for destination in destinations:
            G.add_edge(flight, destination)

    
    for flight, passengers in flight_queues.items():
        for priority, name, reason, destination in passengers:
            G.add_node(name, type='passenger', priority=priority)
            G.add_edge(flight, name)
            G.add_edge(name, destination)

    pos = nx.spring_layout(G)

    
    plt.switch_backend('Agg')

    node_colors = {
        'flight': 'lightblue',
        'destination': 'lightgreen',
        'passenger': 'red'
    }

   
    colors = {node: node_colors[data.get('type', 'flight')] for node, data in G.nodes(data=True)}

   
    for node, data in G.nodes(data=True):
        if data.get('type') == 'destination':
            colors[node] = 'lightgreen'

    nx.draw(G, pos, with_labels=True, font_weight='bold', node_color=list(colors.values()), node_size=350, font_size=10, arrowsize=250)

   
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.clf()

    
    buffer.seek(0)

   
    image_data = base64.b64encode(buffer.read()).decode('utf-8')

    return render_template('graph.html', graph_image=f"data:image/png;base64,{image_data}")

@app.route('/search', methods=['POST'])
def search_passenger():
    search_name = request.form['search_name']
    passenger_details = passenger_trie.search(search_name)
    
    if passenger_details:
        return render_template('search_result.html', passenger_details=passenger_details)
    else:
        return render_template('search_result.html', passenger_details=None)

if __name__ == '__main__':
    app.run(debug=True)
