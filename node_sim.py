import requests
import time
import threading

# Change if your server is running elsewhere
API_SERVER_URL = "http://localhost:5002"

class SimulatedNode:
    def __init__(self, cpu_cores=4):
        self.cpu_cores = cpu_cores
        self.node_id = None

    def register_node(self):
        print("[INFO] Registering node...")
        response = requests.post(f"{API_SERVER_URL}/add_node", json={"cpu_cores": self.cpu_cores})
        if response.status_code == 200:
            self.node_id = response.json()['node_id']
            print(f"[SUCCESS] Node registered with ID: {self.node_id}")
        else:
            print(f"[ERROR] Failed to register node: {response.text}")

    def send_heartbeat(self):
        while True:
            if self.node_id:
                response = requests.post(f"{API_SERVER_URL}/heartbeat", json={"node_id": self.node_id})
                if response.status_code == 200:
                    print(f"[HEARTBEAT] Sent from {self.node_id}")
                else:
                    print(f"[ERROR] Heartbeat failed: {response.text}")
            time.sleep(5)  # Send heartbeat every 5 seconds

    def start(self):
        self.register_node()
        if self.node_id:
            t = threading.Thread(target=self.send_heartbeat)
            t.start()

if __name__ == "__main__":
    cpu_cores = int(input("Enter CPU cores for this node: "))
    node = SimulatedNode(cpu_cores=cpu_cores)
    node.start()
