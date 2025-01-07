from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

# Initialize Display for logging
display = Display()

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        # Execute the custom module
        result = self._execute_module(
            module_name="check_oc_client",
            module_args=self._task.args,
            task_vars=task_vars,
            tmp=tmp,
        )
        display.banner("hi")
        print("h1")
        return result
