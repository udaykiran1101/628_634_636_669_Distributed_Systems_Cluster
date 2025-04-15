from flask import Flask, request, jsonify
import time

app = Flask(__name__)

nodes = []  # List of all registered nodes
pods = []   # List of all pods launched
node_heartbeat = {}  # Track heartbeats: {node_id: last_seen_timestamp}
node_id_counter = 1
pod_id_counter = 1

@app.route('/')
def home():
    return "Welcome to the Cluster API Server"

@app.route('/add_node', methods=['POST'])
def add_node():
    global node_id_counter
    data = request.get_json()
    cpu_cores = data.get('cpu_cores')

    if cpu_cores is None:
        return jsonify({"message": "CPU cores must be provided"}), 400

    node = {
        "id": "node-{}".format(node_id_counter),
        "cpu_cores": cpu_cores,
        "available_cores": cpu_cores,
        "pods": []
    }
    node_id_counter += 1
    nodes.append(node)
    node_heartbeat[node["id"]] = time.time()  # Initialize heartbeat

    return jsonify({"message": "Node added successfully", "node_id": node["id"]}), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    node_id = data.get("node_id")
    if node_id not in node_heartbeat:
        return jsonify({"message": "Node not found"}), 404

    node_heartbeat[node_id] = time.time()
    return jsonify({"message": "Heartbeat received"}), 200

@app.route('/launch_pod', methods=['POST'])
def launch_pod():
    global pod_id_counter
    data = request.get_json()
    cpu_req = data.get("cpu_cores")

    if cpu_req is None:
        return jsonify({"message": "CPU cores required for pod"}), 400

    # First-fit scheduler: find first node with enough CPU
    for node in nodes:
        if node["available_cores"] >= cpu_req:
            pod = {
                "id": "pod-{}".format(pod_id_counter),
                "cpu_cores": cpu_req,
                "assigned_node": node["id"]
            }
            node["available_cores"] -= cpu_req
            node["pods"].append(pod["id"])
            pods.append(pod)
            pod_id_counter += 1
            return jsonify({"message": "Pod launched", "pod": pod}), 200

    return jsonify({"message": "No suitable node available"}), 503

@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    node_info = []
    for node in nodes:
        status = "Healthy" if time.time() - node_heartbeat[node["id"]] <= 10 else "Unhealthy"
        node_info.append({
            "id": node["id"],
            "available_cores": node["available_cores"],
            "pods": node["pods"],
            "status": status
        })
    return jsonify({"nodes": node_info}), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)
