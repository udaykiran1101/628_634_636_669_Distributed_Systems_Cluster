import requests
import json
import time

def list_nodes():
    while True:  # Infinite loop
        try:
            response = requests.get('http://localhost:5002/list_nodes')
            if response.status_code == 200:
                data = response.json()
                # Clear screen (optional, makes it feel more dynamic)
                print("\033c", end="")  # Works on most terminals
                print("Cluster Node Status:\n")
                print(json.dumps(data, indent=4))  # Pretty print the nodes
            else:
                print(f"Failed to fetch nodes. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error: {str(e)}")

        time.sleep(1)  

if __name__ == "__main__":
    list_nodes()
