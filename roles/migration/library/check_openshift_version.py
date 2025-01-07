from ansible.module_utils.basic import AnsibleModule
import subprocess
import re
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
                module.warn(f"Retrying as got an error: {error}")
            time.sleep(3)
        except Exception as ex:
            module.fail_json(msg=str(ex))
    return output


def parse_version(version_json):
    """Parse the OpenShift version from the JSON output."""
    import json
    version_data = json.loads(version_json)
    history = version_data.get("status", {}).get("history", [])
    if not history:
        raise ValueError("No version history found in OpenShift cluster configuration.")

    current_version = history[0].get("version", "")
    match = re.match(r"^(\d+)\.(\d+)", current_version)
    if match:
        major, minor = map(int, match.groups())
        return major, minor
    else:
        raise ValueError("Failed to parse OpenShift version.")


def main():
    module = AnsibleModule(
        argument_spec={"timeout": {"type": "int", "default": 120}, },
        supports_check_mode=True,
    )
    timeout = module.params["timeout"]
    try:
        version_json = get_openshift_version(module, timeout)
        major, minor = parse_version(version_json)

        if major == 4 and minor >= 12:
            module.exit_json(
                changed=False,
                msg="The OpenShift version is 4.12 or greater. EgressIP, EgressFirewall, and multicast features of SDN will be automatically migrated in OVNKubernetes."
            )
        elif major == 4 and minor <= 11:
            module.exit_json(
                changed=False,
                msg="The OpenShift version is 4.11 or less. EgressIP, EgressFirewall, and multicast features of SDN won't be automatically migrated in OVNKubernetes. You need to manually configure them."
            )
        else:
            module.fail_json(msg="Unexpected version format or unsupported version.")
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
