import requests
import time
import argparse
import os
import sys

# API server URL
API_SERVER_URL = "http://localhost:5002"

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 50)
    print(title.center(50))
    print("=" * 50 + "\n")

def make_request(endpoint, method="GET", data=None, verbose=True):
    """
    Make a request to the API server
    
    Args:
        endpoint: API endpoint to call
        method: HTTP method (GET, POST)
        data: Data to send with the request
        verbose: Whether to print error messages
    
    Returns:
        Response JSON or None if request failed
    """
    url = "{}{}".format(API_SERVER_URL, endpoint)
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            if verbose:
                print("Unsupported method: {}".format(method))
            return None
            
        # Check if response is successful
        if response.status_code >= 400:
            if verbose:
                print("Error: {} - {}".format(response.status_code, response.text))
            return None
            
        # Try to parse JSON, handle case where response might not be JSON
        try:
            return response.json()
        except ValueError:
            if verbose:
                print("Warning: Response is not valid JSON: {}".format(response.text))
            return {"message": response.text}
        
    except requests.exceptions.ConnectionError:
        if verbose:
            print("Connection error: Could not connect to the API server at {}".format(API_SERVER_URL))
            print("Make sure the server is running and the URL is correct.")
        return None
    except requests.exceptions.Timeout:
        if verbose:
            print("Timeout error: The API server took too long to respond.")
        return None
    except requests.exceptions.RequestException as e:
        if verbose:
            print("Request failed: {}".format(e))
        return None

def show_cluster_status():
    """Display overall cluster status"""
    print_header("Cluster Status")
    
    response = make_request("/list_nodes")
    if not response:
        print("Failed to get cluster status.")
        return
    
    nodes = response.get('nodes', [])
    
    # Nodes section
    total_nodes = len(nodes)
    healthy_nodes = sum(1 for node in nodes if node.get('status') == 'Healthy')
    
    print("Nodes: {} total, {} healthy, {} unhealthy".format(
        total_nodes, healthy_nodes, total_nodes - healthy_nodes))
    
    # Resources section
    total_cores = sum(node.get('cpu_cores', 0) for node in nodes)
    available_cores = sum(node.get('available_cores', 0) for node in nodes)
    used_cores = total_cores - available_cores
    utilization = (used_cores / total_cores * 100) if total_cores > 0 else 0
    
    print("CPU Resources: {}/{} cores used ({:.1f}% utilization)".format(
        used_cores, total_cores, utilization))
    
    print("\nFetch complete cluster information with 'list nodes'")

def add_node():
    """Add a node to the cluster"""
    print_header("Add Node")
    
    cpu_cores = 4  # Default value
    try:
        cpu_input = input("Enter CPU cores for the node (or press Enter for default 4): ")
        if cpu_input.strip():  # If the input is not empty
            cpu_cores = int(cpu_input)
        
        if cpu_cores <= 0:
            print("CPU cores must be a positive integer. Using default value of 4.")
            cpu_cores = 4
    except ValueError:
        print("Invalid input. Using default value of 4 CPU cores.")
    
    print("Adding node with {} CPU cores...".format(cpu_cores))
    response = make_request("/add_node", "POST", {"cpu_cores": cpu_cores})
    
    if response:
        print("Node added successfully with ID: {}".format(response.get('node_id', 'unknown')))
    else:
        print("Failed to add node.")

def list_nodes():
    """List all nodes in the cluster"""
    print_header("Cluster Nodes")
    
    response = make_request("/list_nodes")
    if not response:
        print("Failed to get node list.")
        return
    
    nodes = response.get('nodes', [])
    if not nodes:
        print("No nodes found in the cluster.")
        return
    
    # Print as a simple table
    print(" {:<15} {:<10} {:<15} {:<10}".format(
        "NODE ID", "STATUS", "AVAILABLE/TOTAL", "PODS"))
    print("-" * 55)
    
    for node in nodes:
        available = node.get('available_cores', 0)
        total = available + sum(1 for _ in node.get('pods', []))  # Estimate total based on available + used
        status = node.get('status', 'Unknown')
        
        print(" {:<15} {:<10} {:<15} {:<10}".format(
            node.get('id', 'unknown'),
            status,
            "{}/{}".format(available, total),
            len(node.get('pods', []))
        ))
    
    print("\nTotal: {} nodes, {} healthy".format(
        len(nodes), 
        sum(1 for node in nodes if node.get('status') == 'Healthy')
    ))

def launch_pod():
    """Launch a pod in the cluster"""
    print_header("Launch Pod")
    
    cpu_cores = 1  # Default value
    try:
        cpu_input = input("Enter CPU cores required for the pod (or press Enter for default 1): ")
        if cpu_input.strip():  # If the input is not empty
            cpu_cores = int(cpu_input)
        
        if cpu_cores <= 0:
            print("CPU cores must be a positive integer. Using default value of 1.")
            cpu_cores = 1
    except ValueError:
        print("Invalid input. Using default value of 1 CPU core.")
    
    print("Launching pod requiring {} CPU cores...".format(cpu_cores))
    response = make_request("/launch_pod", "POST", {"cpu_cores": cpu_cores})
    
    if response:
        pod = response.get('pod', {})
        print("Pod launched successfully with ID: {}".format(pod.get('id', 'unknown')))
        print("Assigned to node: {}".format(pod.get('assigned_node', 'unknown')))
    else:
        print("Failed to launch pod. No suitable node may be available.")

def main_menu():
    """Display the main menu and handle user input"""
    options = {
        "1": ("Show cluster status", show_cluster_status),
        "2": ("Add a node", add_node),
        "3": ("List all nodes", list_nodes),
        "4": ("Launch a pod", launch_pod),
        "q": ("Quit", None)
    }
    
    while True:
        clear_screen()
        print_header("Kubernetes-like Cluster Manager")
        
        # Check server connectivity
        if not make_request("/", verbose=False):
            print("WARNING: Cannot connect to API server at {}".format(API_SERVER_URL))
            print("Make sure the server is running with:")
            print("    python api_server_compatible.py")
            print("\nPress Enter to retry or 'q' to quit...")
            if input().lower() == 'q':
                return
            continue
        
        # Display options
        for key, (desc, _) in options.items():
            print("{}. {}".format(key, desc))
        
        choice = input("\nEnter your choice: ").lower()
        
        if choice == "q":
            print("Exiting...")
            break
            
        if choice in options:
            clear_screen()
            options[choice][1]()  # Call the selected function
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kubernetes-like Cluster Client")
    parser.add_argument("--server", help="API server URL", default="http://localhost:5002")
    args = parser.parse_args()
    
    # Set the API server URL
    API_SERVER_URL = args.server
    
    # Start the client
    main_menu()
