# Distributed Systems Cluster Simulation Framework

This project implements a lightweight simulation-based distributed system that mimics core Kubernetes cluster management functionalities. The system provides a simplified yet comprehensive platform for demonstrating key distributed computing concepts.

## Architecture

The system consists of the following components:

### API Server (Central Control Unit)

The API Server manages the overall cluster operation and contains three key components:

1. **Node Manager**: Tracks registered nodes and their statuses. Maintains information about node resources (CPU cores) and availability.
2. **Pod Scheduler**: Assigns pods to available nodes based on scheduling policies and resource requirements.
3. **Health Monitor**: Receives health signals from nodes and detects failures to ensure system reliability.

### Nodes

Nodes are computing units that host pods:

- When adding a new node to the system, a new container is launched to simulate a physical node in the cluster.
- Each node maintains a list of pod IDs it hosts to simulate pod deployment.
- Nodes periodically send heartbeat signals to the API server.

### Pods

Pods are the smallest deployable units, scheduled on nodes:

- Each pod requires specific CPU resources.
- Pods are simulated through entries in the node's pod ID array list.

## Features

- **Node Management**: Add nodes to the cluster, specifying CPU cores.
- **Pod Scheduling**: Launch pods with specific CPU requirements. The system includes multiple scheduling strategies:
  - First-Fit: Allocate to the first node with sufficient resources
  - Best-Fit: Allocate to the node with the least remaining capacity after allocation
  - Worst-Fit: Allocate to the node with the most remaining capacity after allocation
- **Health Monitoring**: Detects node failures through missed heartbeats.
- **Fault Tolerance**: Automatically reschedules pods from failed nodes to healthy ones.
- **Node Failure Simulation**: Includes a tool to simulate random node failures and recoveries.

## Installation
   Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Start the API Server

```bash
python api_server.py
```

This will start the API server at http://localhost:5002.

### Launch Simulated Nodes

You can launch multiple nodes with different CPU capacities:

```bash
python node_sim.py
# Enter CPU cores when prompted
```

### Use the Client Interface

The client interface provides a user-friendly way to interact with the cluster:

```bash
python client.py
```

This will display a menu with options to:
- Show cluster status
- Add nodes
- List nodes and their health status
- List pods
- Launch pods
- Change scheduling strategy

### Simulate Node Failures

To test the fault tolerance features:

```bash
python node_failure_sim.py --duration 300 --failure-prob 0.2 --recovery-prob 0.3
```

This will randomly simulate node failures and recoveries over the specified duration.

## File Structure

- `api_server.py` - The main API server that includes node management, pod scheduling, and health monitoring
- `health_monitor.py` - Component responsible for monitoring node health and rescheduling pods
- `node_sim.py` - Simulates a cluster node that sends heartbeats to the API server
- `node_manager.py` - Handles Docker containers to simulate physical nodes
- `client.py` - Command-line interface to interact with the cluster
- `node_failure_sim.py` - Tool to simulate random node failures and recoveries

## Requirements

- Python 3.6+
- Flask
- Docker (for node simulation)
- Requests
- Tabulate (for the client interface)

## Advanced Features

- **Health Monitoring**: The system detects node failures through missed heartbeats and marks nodes as unhealthy after a configured timeout.
- **Pod Rescheduling**: When a node fails, the system automatically reschedules its pods to healthy nodes with available capacity.
- **Multiple Scheduling Strategies**: Choose different strategies for pod placement based on your resource optimization goals.
- **Client Interface**: A user-friendly command-line interface for interacting with the cluster.
- **Node Failure Simulation**: Tools to simulate failures and test the system's fault tolerance.

## Future Enhancements

- Implement auto-scaling for nodes based on cluster load.
- Add pod resource usage monitoring.
- Add network policy simulation for pod communication control.
