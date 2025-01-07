from ansible.module_utils.basic import AnsibleModule
import subprocess
import json


def run_oc_command(command, retries=5, delay=5):
    """Run an oc command with retries."""
    for attempt in range(retries):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        if attempt < retries - 1:
            import time
            time.sleep(delay)
    raise RuntimeError(f"Failed to execute command after {retries} attempts: {result.stderr}")


def get_openshift_version():
    """Retrieve the OpenShift version using the oc CLI."""
    command = "oc get clusterversion version -o json"
    version_output = run_oc_command(command)
    version_data = json.loads(version_output)
    history = version_data.get("status", {}).get("history", [])
    if not history:
        raise ValueError("No version history found in OpenShift cluster configuration.")
    current_version = history[0].get("version", "")
    major, minor = map(int, current_version.split(".")[:2])
    return major, minor


def patch_network_config(ovn_config):
    """Patch the network configuration for OVN-Kubernetes."""
    patch_data = {
        "spec": {
            "defaultNetwork": {
                "ovnKubernetesConfig": ovn_config,
            }
        }
    }
    patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"
    return run_oc_command(patch_command)


def main():
    module = AnsibleModule(
        argument_spec={
            "mtu": {"type": "int", "required": False},
            "genevePort": {"type": "int", "required": False},
            "v4InternalSubnet": {"type": "str", "required": False},
            "retries": {"type": "int", "default": 5},
            "delay": {"type": "int", "default": 5},
        },
        supports_check_mode=True,
    )

    mtu = module.params["mtu"]
    geneve_port = module.params["genevePort"]
    v4_internal_subnet = module.params["v4InternalSubnet"]
    retries = module.params["retries"]
    delay = module.params["delay"]

    try:
        major, minor = get_openshift_version()
        if major == 4 and minor >= 12:
            ovn_config = {}
            if mtu is not None:
                ovn_config["mtu"] = mtu
            if geneve_port is not None:
                ovn_config["genevePort"] = geneve_port
            if v4_internal_subnet is not None:
                ovn_config["v4InternalSubnet"] = v4_internal_subnet

            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="This will patch the network configuration for OVN-Kubernetes.",
                    patch=ovn_config,
                )

            patch_output = patch_network_config(ovn_config)
            module.exit_json(changed=True, msg="Network configuration patched successfully.", output=patch_output)
        else:
            module.exit_json(
                changed=False,
                msg="The OpenShift version is less than 4.12. Customization of OVN-Kubernetes settings is not supported.",
            )
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
