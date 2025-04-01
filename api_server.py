from flask import Flask, request, jsonify
from node_manager import NodeManager

app = Flask(__name__)
node_manager = NodeManager()

cluster = {"nodes": []}

@app.route("/add_node", methods=["POST"])
def add_node():
    try:
        data = request.get_json()
        cpu_cores = data.get("cpu_cores", None)
        if cpu_cores is None:
            return jsonify({"error": "CPU cores must be specified."}), 400
        
        node = node_manager.add_node(cpu_cores)
        cluster["nodes"].append(node)
        
        return jsonify({"message": "Node added successfully", "node": node}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/list_nodes", methods=["GET"])
def list_nodes():
    return jsonify({"nodes": cluster["nodes"]}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5002)

