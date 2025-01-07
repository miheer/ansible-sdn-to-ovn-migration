from ansible.module_utils.basic import AnsibleModule
import subprocess


def run_command(command):
    """Run a shell command and return its output or error."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()


def main():
    module_args = dict(
        pool_name=dict(type="str", required=True),
        paused=dict(type="bool", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    pool_name = module.params["pool_name"]
    paused = module.params["paused"]

    # Build the patch command
    paused_value = "true" if paused else "false"
    patch_command = (
        f"oc patch MachineConfigPool {pool_name} --type='merge' "
        f"--patch '{{\"spec\":{{\"paused\":{paused_value}}}}}'"
    )

    # Execute the command
    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would patch {pool_name} with paused={paused_value}.")

    _, error = run_command(patch_command)
    if error:
        module.fail_json(msg=f"Failed to patch {pool_name}: {error}")

    module.exit_json(changed=True, msg=f"Successfully patched {pool_name} with paused={paused_value}.")


if __name__ == "__main__":
    main()
