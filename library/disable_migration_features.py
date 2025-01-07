#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import time


def run_command_with_retries(command, retries, delay):
    """Run a shell command with retries on failure."""
    for attempt in range(retries):
        try:
            result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, f"Command failed after {retries} attempts: {e.stderr.strip()}"
    return None, "Unknown error"


def disable_migration(network_type, retries, delay, egress_ip=None, egress_firewall=None, multicast=None):
    """Disable automatic migration of OpenShift SDN features based on network type."""
    # Set default values if features are not provided
    if egress_ip is None:
        egress_ip = True
    if egress_firewall is None:
        egress_firewall = True
    if multicast is None:
        multicast = True

    patch = {
        "spec": {
            "migration": {
                "networkType": network_type,
                "features": {
                    "egressIP": egress_ip,
                    "egressFirewall": egress_firewall,
                    "multicast": multicast
                }
            }
        }
    }

    patch_command = f"oc patch Network.operator.openshift.io cluster --type='merge' --patch '{json.dumps(patch)}'"

    # Run the command to disable migration features
    stdout, error = run_command_with_retries(patch_command, retries, delay)

    if error:
        return None, error

    return stdout, None


def main():
    module_args = dict(
        networkType=dict(type="str", required=True),
        retries=dict(type="int", default=3),
        delay=dict(type="int", default=5),
        egressIP=dict(type="bool", required=False, default=None),
        egressFirewall=dict(type="bool", required=False, default=None),
        multicast=dict(type="bool", required=False, default=None),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    network_type = module.params["networkType"]
    egress_ip = module.params["egressIP"]
    egress_firewall = module.params["egressFirewall"]
    multicast = module.params["multicast"]
    retries = module.params["retries"]
    delay = module.params["delay"]

    # Disable migration of features for the specified network type
    stdout, error = disable_migration(network_type, retries, delay, egress_ip, egress_firewall, multicast)

    if error:
        module.fail_json(msg=error)

    module.exit_json(changed=True, msg="Migration features disabled successfully", output=stdout)


if __name__ == "__main__":
    main()
