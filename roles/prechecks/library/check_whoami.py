#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import subprocess


def run_module():
    module = AnsibleModule(argument_spec={})
    print("custom module whoami")
    try:
        result = subprocess.run("oc whoami", shell=True, check=True, text=True, capture_output=True)
        if "system:admin" in result.stdout:
            module.exit_json(changed=False, message="Logged in as `system:admin`.")
        else:
            module.fail_json(msg="Not logged in as `system:admin`. Please switch to `system:admin`.")
    except subprocess.CalledProcessError:
        module.fail_json(msg="Failed to execute `oc whoami`. Ensure `oc` client is configured correctly.")


if __name__ == "__main__":
    run_module()
