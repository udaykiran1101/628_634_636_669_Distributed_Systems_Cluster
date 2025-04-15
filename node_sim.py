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
        response = requests.post("{}/add_node".format(API_SERVER_URL), json={"cpu_cores": self.cpu_cores})
        if response.status_code == 200:
            self.node_id = response.json()['node_id']
            print("[SUCCESS] Node registered with ID: {}".format(self.node_id))
        else:
            print("[ERROR] Failed to register node: {}".format(response.text))

    def send_heartbeat(self):
        while True:
            if self.node_id:
                response = requests.post("{}/heartbeat".format(API_SERVER_URL), json={"node_id": self.node_id})
                if response.status_code == 200:
                    print("[HEARTBEAT] Sent from {}".format(self.node_id))
                else:
                    print("[ERROR] Heartbeat failed: {}".format(response.text))
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
