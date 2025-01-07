from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        # Execute the custom module
        result = self._execute_module(
            module_name="check_whoami",
            module_args=self._task.args,
            task_vars=task_vars,
            tmp=tmp,
        )
        print("action whoami")
        return result
