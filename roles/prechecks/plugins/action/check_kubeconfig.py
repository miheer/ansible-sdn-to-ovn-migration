from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        # Execute the custom module
        result = self._execute_module(
            module_name="check_kubeconfig",
            module_args=self._task.args,
            task_vars=task_vars,
            tmp=tmp,
        )
        print("under action/checkkubeconfig")
        return result