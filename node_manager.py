import docker
from time import sleep

class NodeManager:
    def __init__(self):
        self.client = docker.from_env()

    def launch_node(self, cpu_cores):
        try:
            # Simulate node launch by starting a Docker container
            container = self.client.containers.run(
                "ubuntu",  # Using a basic Ubuntu image for simulation
                command="sleep infinity",  # Keep the container running
                detach=True,
                name=f"node_{cpu_cores}_cores",
                environment={"CPU_CORES": str(cpu_cores)},  # Simulate CPU core environment
            )
            print(f"Node launched with container ID: {container.id}")
            return container.id
        except Exception as e:
            print(f"Error launching node: {e}")
            return None

    def add_node(self, cpu_cores):
        container_id = self.launch_node(cpu_cores)
        if container_id:
            node = {
                "id": container_id,
                "cpu_cores": cpu_cores,
                "health": "healthy"
            }
            print(f"Node added: {node}")
            return node
        return None

