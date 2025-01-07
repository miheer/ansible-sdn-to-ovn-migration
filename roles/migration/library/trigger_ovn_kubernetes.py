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


def wait_for_network_operator(timeout):
    """Wait for the network cluster operator to transition to PROGRESSING=True."""
    start_time = time.time()
    interval = 10

    while time.time() - start_time < timeout:
        try:
            run_command("oc wait co network --for='condition=PROGRESSING=True' --timeout=10s")
            return True
        except Exception as e:
            print(f"Retrying due to error: {str(e)}")
        time.sleep(interval)

    # Timeout reached
    return False


def main():
    module_args = dict(
        network_type=dict(type="str", required=True),  # Target network type
        timeout=dict(type="int", required=False, default=60),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    network_type = module.params["network_type"]
    #timeout = module.params["timeout"]


    try:
        output = patch_network_config(network_type)
        module.exit_json(changed=True, msg="Successfully triggered ovn-kubernetes deployment.", output=output)
    except Exception as e:
        module.fail_json(msg=str(e))
'''
    try:
        patch_network_config(network_type)
        if wait_for_network_operator(timeout):
            module.exit_json(changed=True, msg="OVN-Kubernetes deployment triggered successfully.")
        else:
            module.fail_json(msg="Timeout reached while waiting for network operator to progress.")
    except Exception as ex:
        #module.fail_json(msg=str(ex))
'''

if __name__ == "__main__":
    main()
