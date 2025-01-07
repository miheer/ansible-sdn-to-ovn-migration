from ansible.module_utils.basic import AnsibleModule
import subprocess
import time
import json


def run_command_with_retries(command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, f"Command failed after {retries} attempts: {e.stderr.strip()}"
    return None, "Unknown error"


def run_oc_command(command, retries=3, delay=5):
    """Run an oc command with retries."""
    for attempt in range(retries):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        time.sleep(delay)
    raise RuntimeError(f"Command failed after {retries} attempts: {result.stderr}")


def main():
    #patch_command = ""
    module = AnsibleModule(
        argument_spec={
            "network_type": {"type": "str", "choices": ["OVNKubernetes", "OpenShiftSDN"], "required": True},
            "mtu": {"type": "int", "required": False},
            "geneve_port": {"type": "int", "required": False},
            "ipv4_subnet": {"type": "str", "required": False},
            "retries": {"type": "int", "default": 3},
            "delay": {"type": "int", "default": 5},
            "vxlanPort": {"type": "int", "required": False},
        },
        supports_check_mode=True,
    )

    network_type = module.params["network_type"]
    mtu = module.params["mtu"]
    geneve_port = module.params["geneve_port"]
    ipv4_subnet = module.params["ipv4_subnet"]
    retries = module.params["retries"]
    delay = module.params["delay"]
    vxlanPort = module.params["vxlanPort"]

    # Build the patch payload
    patch_data = {"spec": {"defaultNetwork": {f"{network_type}Config": {}}}}

    if network_type == "OVNKubernetes":
        if mtu:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["mtu"] = mtu
        if geneve_port:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["genevePort"] = geneve_port
        if ipv4_subnet:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["v4InternalSubnet"] = ipv4_subnet
       #if mtu or geneve_port or ipv4_subnet:
            #patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"

    if network_type == "OpenShiftSDN":
        if mtu:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["mtu"] = mtu
        if vxlanPort:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["vxlanPort"] = vxlanPort
        #if mtu or vxlanPort:
            #patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"

    patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"
    print(f"patch_command {patch_command}")

    if module.check_mode:
        module.exit_json(
            changed=True, msg="Check mode: Patch command prepared", command=patch_command
        )

    try:
        output, error = run_command_with_retries(patch_command, retries=retries, delay=delay)
        if not error:
            module.exit_json(changed=True, msg="Network configuration patched successfully.", output=output)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
