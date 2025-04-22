from flask import Flask, request, jsonify
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_server')

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
    
    try:
        cpu_cores = int(cpu_cores)
    except ValueError:
        return jsonify({"message": "CPU cores must be an integer"}), 400

    node = {
        "id": "node-{}".format(node_id_counter),
        "cpu_cores": cpu_cores,
        "available_cores": cpu_cores,
        "pods": []
    }
    node_id_counter += 1
    nodes.append(node)
    node_heartbeat[node["id"]] = time.time()  # Initialize heartbeat

    logger.info("Node added: {} with {} CPU cores".format(node["id"], cpu_cores))
    return jsonify({"message": "Node added successfully", "node_id": node["id"]}), 200

@app.route('/remove_node', methods=['POST'])
def remove_node():
    data = request.get_json()
    node_id = data.get("node_id")
    
    if not node_id:
        return jsonify({"message": "Node ID must be provided"}), 400
    
    # Find the node to remove
    node_to_remove = None
    for node in nodes:
        if node["id"] == node_id:
            node_to_remove = node
            break
    
    if not node_to_remove:
        return jsonify({"message": "Node not found"}), 404
    
    # Check if the node has pods
    if node_to_remove["pods"]:
        force = data.get("force", False)
        if not force:
            return jsonify({
                "message": "Node has pods. Use force=true to remove anyway.",
                "pods": node_to_remove["pods"]
            }), 409
        
        # Handle pods on the node being removed
        for pod_id in node_to_remove["pods"]:
            # Find the pod
            pod_to_reschedule = None
            for pod in pods:
                if pod["id"] == pod_id:
                    pod_to_reschedule = pod
                    break
            
            if pod_to_reschedule:
                # Try to reschedule the pod
                rescheduled = False
                for other_node in nodes:
                    # Skip the node being removed
                    if other_node["id"] == node_id:
                        continue
                    
                    # If the node has enough resources, reschedule the pod
                    if other_node["available_cores"] >= pod_to_reschedule["cpu_cores"]:
                        # Update pod assignment
                        pod_to_reschedule["assigned_node"] = other_node["id"]
                        
                        # Update node resources
                        other_node["available_cores"] -= pod_to_reschedule["cpu_cores"]
                        other_node["pods"].append(pod_id)
                        
                        rescheduled = True
                        logger.info("Pod {} rescheduled from node {} to node {}".format(
                            pod_id, node_id, other_node["id"]))
                        break
                
                # If pod couldn't be rescheduled, remove it
                if not rescheduled:
                    pods.remove(pod_to_reschedule)
                    logger.warning("Pod {} removed because no suitable node available".format(pod_id))
    
    # Remove the node
    nodes.remove(node_to_remove)
    if node_id in node_heartbeat:
        del node_heartbeat[node_id]
    
    logger.info("Node {} removed from the cluster".format(node_id))
    return jsonify({"message": "Node removed successfully"}), 200

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
    
    try:
        cpu_req = int(cpu_req)
    except ValueError:
        return jsonify({"message": "CPU cores must be an integer"}), 400

    # First-fit scheduler: find first node with enough CPU
    for node in nodes:
        # Skip unhealthy nodes
        if node["id"] not in node_heartbeat or time.time() - node_heartbeat[node["id"]] > 15:
            continue
            
        if node["available_cores"] >= cpu_req:
            pod = {
                "id": "pod-{}".format(pod_id_counter),
                "cpu_cores": cpu_req,
                "assigned_node": node["id"],
                "creation_time": time.time()
            }
            node["available_cores"] -= cpu_req
            node["pods"].append(pod["id"])
            pods.append(pod)
            pod_id_counter += 1
            
            logger.info("Pod {} scheduled on node {}".format(pod["id"], node["id"]))
            return jsonify({"message": "Pod launched", "pod": pod}), 200

    return jsonify({"message": "No suitable node available"}), 503

@app.route('/remove_pod', methods=['POST'])
def remove_pod():
    data = request.get_json()
    pod_id = data.get("pod_id")

    if not pod_id:
        return jsonify({"message": "Pod ID must be provided"}), 400

    # Find the pod
    pod_to_remove = None
    for pod in pods:
        if pod["id"] == pod_id:
            pod_to_remove = pod
            break

    if not pod_to_remove:
        return jsonify({"message": "Pod not found"}), 404

    # Free up CPU on the assigned node
    assigned_node_id = pod_to_remove["assigned_node"]
    node = next((n for n in nodes if n["id"] == assigned_node_id), None)
    
    if node:
        node["available_cores"] += pod_to_remove["cpu_cores"]
        if pod_id in node["pods"]:
            node["pods"].remove(pod_id)

    pods.remove(pod_to_remove)

    logger.info("Pod {} removed from node {}".format(pod_id, assigned_node_id))
    return jsonify({"message": "Pod removed successfully"}), 200

@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    current_time = time.time()
    node_info = []
    
    for node in nodes:
        # Calculate node health status
        if node["id"] not in node_heartbeat:
            status = "Unknown"
        elif current_time - node_heartbeat[node["id"]] <= 15:
            status = "Healthy"
        else:
            status = "Unhealthy"
        
        node_info.append({
            "id": node["id"],
            "cpu_cores": node["cpu_cores"],
            "available_cores": node["available_cores"],
            "pods": node["pods"],
            "status": status
        })
    
    return jsonify({
        "nodes": node_info,
        "total_nodes": len(nodes),
        "healthy_nodes": sum(1 for n in node_info if n["status"] == "Healthy")
    }), 200

@app.route('/list_pods', methods=['GET'])
def list_pods():
    pod_info = []
    
    for pod in pods:
        # Find the node this pod is assigned to
        node = next((n for n in nodes if n["id"] == pod["assigned_node"]), None)
        
        # Calculate pod age
        age_seconds = time.time() - pod.get("creation_time", time.time())
        
        pod_info.append({
            "id": pod["id"],
            "cpu_cores": pod["cpu_cores"],
            "assigned_node": pod["assigned_node"],
            "node_status": "Unknown" if not node else 
                           "Healthy" if time.time() - node_heartbeat.get(node["id"], 0) <= 15 else 
                           "Unhealthy",
            "age": "{}m {}s".format(int(age_seconds / 60), int(age_seconds % 60))
        })
    
    return jsonify({
        "pods": pod_info,
        "total_pods": len(pods)
    }), 200

if __name__ == '__main__':
    logger.info("Starting API Server...")
    app.run(debug=True, host="0.0.0.0", port=5002)
