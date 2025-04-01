from flask import Flask, request, jsonify

app = Flask(__name__)

nodes = []  # This is where the nodes will be stored.

@app.route('/')
def home():
    return "Welcome to the Node Manager API"

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.get_json()
    cpu_cores = data.get('cpu_cores')
    
    if cpu_cores is None:
        return jsonify({"message": "CPU cores must be provided"}), 400

    # Add the node data to the list
    node = {
        "cpu_cores": cpu_cores
    }
    nodes.append(node)  # Save the node to the list

    return jsonify({"message": "Node added successfully", "node": node}), 200

@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    return jsonify({"nodes": nodes}), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)

