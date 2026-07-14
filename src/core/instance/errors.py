class InstanceAlreadyRunningError(RuntimeError):
    def __init__(self, instance_name: str) -> None:
        self.instance_name = instance_name
        super().__init__(f"Instance '{instance_name}' is already running. Close Minecraft before launching this instance again.")
