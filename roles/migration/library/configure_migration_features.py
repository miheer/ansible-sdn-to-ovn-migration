from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import time


def run_command(command):
    """Run a shell command and return its output or raise an error."""
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as err:
        return None, Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def get_openshift_version(module, timeout):
    """Retrieve the OpenShift version using the oc CLI."""
    command = "oc get clusterversion version -o json"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(command)
            if error:
                module.warn(changed=True, msg=f"Retrying.... Failed to get OpenShift version: {output.stderr}")
                time.sleep(3)
        except Exception as ex:
            module.fail_json(msg=str(ex))
    return output


def parse_version(version_json):
    """Parse the OpenShift version from the JSON output."""
    version_data = json.loads(version_json)
    history = version_data.get("status", {}).get("history", [])
    if not history:
        raise ValueError("No version history found in OpenShift cluster configuration.")
    current_version = history[0].get("version", "")
    major, minor = map(int, current_version.split(".")[:2])
    return major, minor


def patch_network_config(module, timeout, features):
    """Patch the network configuration to disable automatic migration."""
    patch_data = {
        "spec": {
            "migration": {
                "networkType": "OVNKubernetes",
                "features": features,
            }
        }
    }
    patch_command = f"oc patch Network.operator.openshift.io cluster --type='merge' --patch '{json.dumps(patch_data)}'"
    output, error = run_command(patch_command)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(patch_command)
            if error:
                module.warn(f"Retrying as got an error: {error}")
            time.sleep(3)
        except Exception as ex:
            module.fail_json(msg=str(ex))
    return output


def main():
    module = AnsibleModule(
        argument_spec={
            "egressIP": {"type": "bool", "default": True},
            "egressFirewall": {"type": "bool", "default": True},
            "multicast": {"type": "bool", "default": True},
            "timeout": {"type": "int", "default": 120},  # Timeout in seconds
        },
        supports_check_mode=True,
    )

    egressIP = module.params["egressIP"]
    egressFirewall = module.params["egressFirewall"]
    multicast = module.params["multicast"]
    timeout = module.params["timeout"]

    try:
        version_json = get_openshift_version(module, timeout)
        major, minor = parse_version(version_json)

        if major == 4 and minor >= 12:
            features = {
                "egressIP": egressIP,
                "egressFirewall": egressFirewall,
                "multicast": multicast,
            }
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="This will patch the network configuration to disable automatic migration of features.",
                    patch=features,
                )
            patch_output = patch_network_config(module, timeout, features)
            module.exit_json(changed=True, msg="Network configuration patched successfully.", output=patch_output)
        else:
            module.exit_json(
                changed=False,
                msg="The OpenShift version is less than 4.12. No action will be performed as disabling feature is available from version 4.12",
            )
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
