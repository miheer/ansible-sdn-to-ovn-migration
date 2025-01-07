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
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as err:
        return None, Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def wait_for_mco(timeout):
    """Wait until MCO conditions are satisfied or timeout."""
    start_time = time.time()
    interval = 10

    while time.time() - start_time < timeout:
        try:
            # Check MCP conditions
            _, _ = run_command("oc wait mcp --all --for='condition=UPDATED=True' --timeout=60s")
            _, _ = run_command("oc wait mcp --all --for='condition=UPDATING=False' --timeout=60s")
            _, _ = run_command("oc wait mcp --all --for='condition=DEGRADED=False' --timeout=60s")

            # If all conditions are met, return success
            return True
        except Exception as e:
            # Log the error and retry
            print(f"Retrying due to error: {str(e)}")

        # Wait before retrying
        time.sleep(interval)

    # Timeout reached
    return False


def main():
    module_args = dict(
        timeout=dict(type="int", required=False, default=2700),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    timeout = module.params["timeout"]

    try:
        if wait_for_mco(timeout):
            module.exit_json(changed=False, msg="MCO finished successfully.")
        else:
            module.fail_json(msg="Timeout reached while waiting for MCO to finish.")
    except Exception as ex:
        module.fail_json(msg=str(ex))


if __name__ == "__main__":
    main()
