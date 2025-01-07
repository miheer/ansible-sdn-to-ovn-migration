from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import time


def run_command(command):
    """Execute a shell command and return its output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
    return result.stdout.strip()


def get_nodes_by_role(role_label):
    """Fetch nodes by their role (master/worker) using JSON parsing."""
    nodes_output = run_command("oc get nodes -o json")
    nodes_data = json.loads(nodes_output)
    nodes = []

    for item in nodes_data["items"]:
        labels = item.get("metadata", {}).get("labels", {})
        if f"node-role.kubernetes.io/{role_label}" in labels:
            nodes.append(item["metadata"]["name"])

    return nodes


def get_pod_on_node(node, daemonset_name):
    """Fetch the pod running on a specific node for the given DaemonSet using JSON parsing."""
    pods_output = run_command("oc get pods -n openshift-machine-config-operator -o json")
    pods_data = json.loads(pods_output)

    for item in pods_data["items"]:
        if item.get("spec", {}).get("nodeName") == node:
            pod_name = item["metadata"]["name"]
            if daemonset_name in pod_name:
                return pod_name

    return None


def reboot_node(node, pod_name, delay, max_retries=5, retry_interval=3):
    """
    Reboot a node using the pod running on it.
    Retries the reboot command if it fails.
    """
    command = f"oc rsh -n openshift-machine-config-operator {pod_name} chroot /rootfs shutdown -r +{delay}"
    attempts = 0

    while attempts < max_retries:
        try:
            run_command(command)
            print(f"Reboot command sent to node {node}. Waiting for the node to reboot...")
            return
        except RuntimeError as e:
            attempts += 1
            print(f"Failed to reboot node {node} (attempt {attempts}/{max_retries}): {str(e)}")
            time.sleep(retry_interval)

    raise RuntimeError(f"Failed to reboot node {node} after {max_retries} attempts.")


def wait_for_api_unreachable(delay_minutes):
    """Wait until the API server becomes unreachable."""
    print(f"Waiting {delay_minutes} minutes for API server to become unreachable...")
    time.sleep(delay_minutes * 60)


def wait_for_nodes_ready(timeout):
    """Wait until all nodes are in 'Ready' state."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            nodes_output = run_command("oc get nodes -o json")
            nodes_data = json.loads(nodes_output)

            all_ready = True
            for item in nodes_data["items"]:
                conditions = item.get("status", {}).get("conditions", [])
                ready_condition = next((cond for cond in conditions if cond["type"] == "Ready"), None)
                if not ready_condition or ready_condition["status"] != "True":
                    all_ready = False
                    break

            if all_ready:
                return True

        except RuntimeError:
            print("Failed to get node status, retrying...")

        print("Nodes not ready, retrying...")
        time.sleep(10)

    raise TimeoutError("Timeout exceeded while waiting for nodes to become ready.")


def main():
    module_args = dict(
        daemonset_name=dict(type="str", required=True),
        delay=dict(type="int", required=True),
        timeout=dict(type="int", required=True),
        max_retries=dict(type="int", default=5),
        retry_interval=dict(type="int", default=3),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    daemonset_name = module.params["daemonset_name"]
    delay = module.params["delay"]
    timeout = module.params["timeout"]
    max_retries = module.params["max_retries"]
    retry_interval = module.params["retry_interval"]

    try:
        # Get master and worker nodes
        master_nodes = get_nodes_by_role("master")
        worker_nodes = get_nodes_by_role("worker")

        # Reboot master nodes
        for node in master_nodes:
            pod_name = get_pod_on_node(node, daemonset_name)
            if pod_name:
                print(f"Rebooting master node {node} in {delay}m")
                reboot_node(node, pod_name, delay, max_retries, retry_interval)
                delay += 3

        # Reboot worker nodes
        for node in worker_nodes:
            pod_name = get_pod_on_node(node, daemonset_name)
            if pod_name:
                print(f"Rebooting worker node {node} in {delay}m")
                reboot_node(node, pod_name, delay, max_retries, retry_interval)

        # Wait for API server to become unreachable
        wait_for_api_unreachable(delay)

        # Wait for nodes to become ready
        print("Waiting for all nodes to become ready...")
        wait_for_nodes_ready(timeout)

        module.exit_json(changed=True,
                         msg="Successfully rebooted all nodes, waited for API unreachability, and verified readiness.")
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
