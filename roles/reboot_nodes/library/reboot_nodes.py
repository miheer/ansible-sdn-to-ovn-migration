from ansible.module_utils.basic import AnsibleModule
import subprocess
import json


def run_command(command):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()


def main():
    module_args = dict(
        node_type=dict(type="str", required=True, choices=["master", "worker"]),
        daemonset_name=dict(type="str", required=True),
        namespace=dict(type="str", required=True),
        delay=dict(type="int", default=1)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    node_type = module.params["node_type"]
    daemonset_name = module.params["daemonset_name"]
    namespace = module.params["namespace"]
    delay = module.params["delay"]

    # Fetch the nodes based on type
    node_label = f"node-role.kubernetes.io/{node_type}"
    cmd_nodes = f"oc get nodes -o json"
    nodes_output, error = run_command(cmd_nodes)
    if error:
        module.fail_json(msg=f"Failed to fetch nodes: {error}")

    try:
        nodes = json.loads(nodes_output).get("items", [])
        target_nodes = [
            node["metadata"]["name"]
            for node in nodes
            if node_label in node.get("metadata", {}).get("labels", {})
        ]
    except Exception as e:
        module.fail_json(msg=f"Error processing nodes data: {str(e)}")

    for node in target_nodes:
        # Fetch the pod on the current node
        cmd_pods_on_node = f"oc get pods -n {namespace} -o json -l k8s-app={daemonset_name}"
        pods_output, error = run_command(cmd_pods_on_node)
        if error:
            module.fail_json(msg=f"Failed to get pods for node {node}: {error}")

        try:
            pods = json.loads(pods_output).get("items", [])
            pod_name = next(
                (pod["metadata"]["name"] for pod in pods if pod["spec"]["nodeName"] == node),
                None
            )
        except Exception as e:
            module.fail_json(msg=f"Error processing pods data for node {node}: {str(e)}")

        if pod_name:
            # Attempt to reboot the node via the pod
            reboot_command = f"oc rsh -n {namespace} {pod_name} chroot /rootfs shutdown -r +{delay}"
            while True:
                _, error = run_command(reboot_command)
                if not error:
                    break
                run_command("sleep 3")
            delay += 3
        else:
            module.fail_json(msg=f"No matching pod found on node {node}.")

    module.exit_json(changed=True, msg=f"{node_type.capitalize()} nodes rebooted successfully.")


if __name__ == "__main__":
    main()
