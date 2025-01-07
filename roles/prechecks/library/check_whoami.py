#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()


def run_module():
    module = AnsibleModule(argument_spec={})
    try:
        start_time = time.time()
        # TODO: use sdn_migration_timeout
        while time.time() - start_time < 120:
            command = "oc whoami"
            result, error = run_command(command)
            if not error:
                if "system:admin" in result:
                    module.exit_json(changed=False, message="Logged in as `system:admin`.")
            if error:
                    module.fail_json(msg="Not logged in as `system:admin`. Please switch to `system:admin`.")
            time.sleep(3)
    except subprocess.CalledProcessError:
        module.fail_json(msg="Failed to execute `oc whoami`. Ensure `oc` client is configured correctly.")


if __name__ == "__main__":
    run_module()
