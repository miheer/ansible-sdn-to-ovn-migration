from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        timeout = self._task.args.get("timeout", 1200)
        interval = self._task.args.get("interval", 10)

        display.vvv(f"Running custom action plugin: timeout={timeout}, interval={interval}")

        # Call the custom module
        result.update(
            self._execute_module(
                module_name="check_cluster_operators",
                module_args=dict(timeout=timeout, interval=interval),
                task_vars=task_vars
            )
        )

        # Display the cluster operators in the output
        if "operators" in result:
            display.display(f"Cluster Operators:\n{result['operators']}")

        return result
