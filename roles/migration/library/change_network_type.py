#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess


def run_command(command):
    """Run a shell command and return its output or raise an error."""
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as err:
        raise Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def main():
    module_args = dict(
        network_type=dict(type="str", required=True),  # Target network type
    )

    module = AnsibleModule(argument_spec=module_args)

    network_type = module.params["network_type"]

    try:
        # Construct the patch command
        patch_command = (
            f"oc patch Network.operator.openshift.io cluster --type='merge' "
            f"--patch '{{\"spec\":{{\"migration\":{{\"networkType\":\"{network_type}\"}}}}}}'"
        )

        # Execute the command
        run_command(patch_command)

        module.exit_json(changed=True, msg=f"Network type changed to {network_type}.")
    except Exception as ex:
        module.fail_json(msg=str(ex))


if __name__ == "__main__":
    main()
