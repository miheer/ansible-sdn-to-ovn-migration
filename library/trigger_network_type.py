#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command(command):
    """Run a shell command and return its output or raise an error."""
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as err:
        raise Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def patch_network_config(network_type):
    """Patch the network configuration to trigger OVN-Kubernetes deployment."""
    command = f'oc patch Network.config.openshift.io cluster --type=merge --patch "{{\\"spec\\":{{\\"networkType\\":\\"{network_type}\\"}}}}"'
    run_command(command)

def main():
    module_args = dict(
        network_type=dict(type="str", required=True),  # Target network type
        timeout=dict(type="int", required=False, default=60),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    network_type = module.params["network_type"]

    try:
        output = patch_network_config(network_type)
        module.exit_json(changed=True, msg=f"Successfully triggered {network_type} deployment.", output=output)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
