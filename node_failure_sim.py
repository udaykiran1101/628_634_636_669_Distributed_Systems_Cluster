import requests
import time
import random
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('node_failure_sim')

# API Server URL
API_SERVER_URL = "http://localhost:5002"

class NodeFailureSimulator:
    def __init__(self, api_url, failure_probability=0.2, recovery_probability=0.3):
        """
        Initialize a node failure simulator
        
        Args:
            api_url: URL of the API server
            failure_probability: Probability of a node failing during each check (0.0 to 1.0)
            recovery_probability: Probability of a failed node recovering (0.0 to 1.0)
        """
        self.api_url = api_url
        self.failure_probability = failure_probability
        self.recovery_probability = recovery_probability
        self.failed_nodes = set()  # Set of nodes that are currently failed
        
    def get_nodes(self):
        """Get the list of nodes from the API server"""
        try:
            response = requests.get(f"{self.api_url}/list_nodes")
            if response.status_code == 200:
                return response.json().get("nodes", [])
            else:
                logger.error(f"Failed to get nodes: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting nodes: {e}")
            return []
            
    def simulate_node_failure(self, node_id):
        """
        Simulate a node failure by stopping heartbeats
        
        Args:
            node_id: ID of the node to fail
        """
        if node_id in self.failed_nodes:
            logger.info(f"Node {node_id} is already failed")
            return
            
        logger.info(f"Simulating failure of node {node_id}")
        self.failed_nodes.add(node_id)
        
    def simulate_node_recovery(self, node_id):
        """
        Simulate a node recovery by resuming heartbeats
        
        Args:
            node_id: ID of the node to recover
        """
        if node_id not in self.failed_nodes:
            logger.info(f"Node {node_id} is not failed")
            return
            
        logger.info(f"Simulating recovery of node {node_id}")
        
        # Send a heartbeat to simulate the node coming back online
        try:
            response = requests.post(f"{self.api_url}/heartbeat", json={"node_id": node_id})
            if response.status_code == 200:
                self.failed_nodes.remove(node_id)
                logger.info(f"Node {node_id} has recovered")
            else:
                logger.error(f"Failed to recover node {node_id}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error recovering node {node_id}: {e}")
    
    def run_simulation(self, duration_seconds):
        """
        Run the failure simulation for a specified duration
        
        Args:
            duration_seconds: How long to run the simulation
        """
        logger.info(f"Starting node failure simulation for {duration_seconds} seconds")
        
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            # Get the current list of nodes
            nodes = self.get_nodes()
            
            if not nodes:
                logger.warning("No nodes found in the cluster")
                time.sleep(5)
                continue
            
            # First, check if any failed nodes should recover
            for node_id in list(self.failed_nodes):  # Use list to avoid modifying during iteration
                if random.random() < self.recovery_probability:
                    self.simulate_node_recovery(node_id)
            
            # Then, check if any healthy nodes should fail
            for node in nodes:
                node_id = node["id"]
                if node["status"] == "Healthy" and node_id not in self.failed_nodes:
                    if random.random() < self.failure_probability:
                        self.simulate_node_failure(node_id)
            
            # Sleep for a bit before the next iteration
            time.sleep(5)
        
        logger.info("Simulation complete")

def main():
    parser = argparse.ArgumentParser(description="Simulate node failures in the cluster")
    parser.add_argument("--server", default="http://localhost:5002", help="API server URL")
    parser.add_argument("--duration", type=int, default=300, help="Simulation duration in seconds")
    parser.add_argument("--failure-prob", type=float, default=0.2, help="Node failure probability (0.0 to 1.0)")
    parser.add_argument("--recovery-prob", type=float, default=0.3, help="Node recovery probability (0.0 to 1.0)")
    
    args = parser.parse_args()
    
    simulator = NodeFailureSimulator(
        args.server,
        failure_probability=args.failure_prob,
        recovery_probability=args.recovery_prob
    )
    
    simulator.run_simulation(args.duration)

if __name__ == "__main__":
    main()
