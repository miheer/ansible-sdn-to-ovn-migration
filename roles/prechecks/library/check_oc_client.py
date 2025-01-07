#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import shutil


def is_oc_binary_present():
    """Check if the oc binary exists in the system's PATH."""
    return shutil.which("oc") is not None


def get_oc_version():
    """Check if the oc command is functional and return its version."""
    try:
        result = subprocess.run(
            ["oc", "version", "--client"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def main():
    module = AnsibleModule(argument_spec={})

    # Check if the binary exists
    if not is_oc_binary_present():
        module.fail_json(msg="The oc binary is not present in the system's PATH.")

    # Check if the binary works and get its version
    is_installed, message = get_oc_version()

    if is_installed:
        module.exit_json(changed=False, version=message)
    else:
        module.fail_json(msg=f"The oc binary is present but not functional: {message}")


if __name__ == "__main__":
    main()
