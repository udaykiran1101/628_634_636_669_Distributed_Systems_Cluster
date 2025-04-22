import time
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('health_monitor')

class HealthMonitor:
    def __init__(self, nodes, node_heartbeat, pods, heartbeat_timeout=15):
        """
        Initialize the health monitor
        
        Args:
            nodes: List of nodes in the cluster
            node_heartbeat: Dictionary tracking last heartbeat time for each node
            pods: List of all pods in the cluster
            heartbeat_timeout: Time in seconds after which a node is considered unhealthy
        """
        self.nodes = nodes
        self.node_heartbeat = node_heartbeat
        self.pods = pods
        self.heartbeat_timeout = heartbeat_timeout
        self.running = False
        self.thread = None
        self.failed_nodes = set()  # Track nodes that have failed
        
    def start(self):
        """Start the health monitoring thread"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_health)
        self.thread.daemon = True  # Thread will exit when main program exits
        self.thread.start()
        logger.info("Health monitor started")
        
    def stop(self):
        """Stop the health monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)  # Wait for thread to finish
        logger.info("Health monitor stopped")
        
    def _monitor_health(self):
        """Continuously monitor node health and handle failures"""
        while self.running:
            current_time = time.time()
            
            # Check each node's heartbeat status
            for node in list(self.nodes):  # Create a copy of the list for safe iteration
                node_id = node["id"]
                
                # If no heartbeat or too old, mark as unhealthy
                if node_id not in self.node_heartbeat or current_time - self.node_heartbeat[node_id] > self.heartbeat_timeout:
                    if node_id not in self.failed_nodes:
                        logger.warning(f"Node {node_id} has failed! Last heartbeat: {self.node_heartbeat.get(node_id, 'None')}")
                        self.failed_nodes.add(node_id)
                        self._handle_node_failure(node)
                else:
                    # If node was previously failed but is now healthy, remove from failed set
                    if node_id in self.failed_nodes:
                        logger.info(f"Node {node_id} has recovered!")
                        self.failed_nodes.remove(node_id)
            
            # Sleep for a while before next check
            time.sleep(5)
    
    def _handle_node_failure(self, failed_node):
        """
        Handle a node failure by rescheduling its pods to other healthy nodes
        
        Args:
            failed_node: The node that has failed
        """
        logger.info(f"Handling failure of node {failed_node['id']}")
        
        # Get all pods assigned to the failed node
        pods_to_reschedule = [pod for pod in self.pods if pod["assigned_node"] == failed_node["id"]]
        
        if not pods_to_reschedule:
            logger.info(f"No pods to reschedule from failed node {failed_node['id']}")
            return
        
        logger.info(f"Found {len(pods_to_reschedule)} pods to reschedule from node {failed_node['id']}")
        
        # Try to reschedule each pod
        for pod in pods_to_reschedule:
            self._reschedule_pod(pod, failed_node)
    
    def _reschedule_pod(self, pod, failed_node):
        """
        Reschedule a pod from a failed node to a healthy node
        
        Args:
            pod: The pod to reschedule
            failed_node: The node that failed
        """
        cpu_req = pod["cpu_cores"]
        pod_id = pod["id"]
        
        logger.info(f"Attempting to reschedule pod {pod_id} requiring {cpu_req} CPU cores")
        
        # Find a healthy node with enough capacity
        for node in self.nodes:
            # Skip the failed node and any other unhealthy nodes
            if node["id"] == failed_node["id"] or node["id"] in self.failed_nodes:
                continue
                
            # If node has enough capacity, schedule the pod there
            if node["available_cores"] >= cpu_req:
                logger.info(f"Rescheduling pod {pod_id} to node {node['id']}")
                
                # Update pod assignment
                pod["assigned_node"] = node["id"]
                
                # Update node resources
                node["available_cores"] -= cpu_req
                node["pods"].append(pod_id)
                
                # Remove pod from failed node's list (even though the node is down,
                # we keep the data structure clean)
                if pod_id in failed_node["pods"]:
                    failed_node["pods"].remove(pod_id)
                
                logger.info(f"Successfully rescheduled pod {pod_id} to node {node['id']}")
                return
        
        # If we get here, we couldn't reschedule the pod
        logger.warning(f"Failed to reschedule pod {pod_id} - no suitable node available")
        # We'll keep the pod in the list so we can try to reschedule it later when new nodes join
