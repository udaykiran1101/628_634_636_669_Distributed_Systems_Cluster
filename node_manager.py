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
                name="node_{}_cores".format(cpu_cores),
                environment={"CPU_CORES": str(cpu_cores)},  # Simulate CPU core environment
            )
            print("Node launched with container ID: {}".format(container.id))
            return container.id
        except Exception as e:
            print("Error launching node: {}".format(e))
            return None

    def add_node(self, cpu_cores):
        container_id = self.launch_node(cpu_cores)
        if container_id:
            node = {
                "id": container_id,
                "cpu_cores": cpu_cores,
                "health": "healthy"
            }
            print("Node added: {}".format(node))
            return node
        return None
