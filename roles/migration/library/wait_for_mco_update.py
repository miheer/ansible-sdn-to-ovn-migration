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
        timeout=dict(type="str", required=False, default="300s"),  # Timeout for the wait
    )

    module = AnsibleModule(argument_spec=module_args)

    timeout = module.params["timeout"]

    try:
        # Construct the wait command
        wait_command = (
            f"oc wait mcp --all --for='condition=UPDATING=True' --timeout={timeout}"
        )

        # Execute the command
        run_command(wait_command)

        module.exit_json(
            changed=False, msg=f"MCO started applying new configurations within {timeout}."
        )
    except Exception as ex:
        module.fail_json(msg=str(ex))


if __name__ == "__main__":
    main()
