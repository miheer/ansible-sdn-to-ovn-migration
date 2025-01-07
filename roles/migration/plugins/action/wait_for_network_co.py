from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()

        # Execute the wait_for_network_co module
        result = self._execute_module(
            module_name="wait_for_network_co",
            module_args=module_args,
            task_vars=task_vars,
            tmp=tmp,
        )

        return result
