

class Function:

    def __init__(self, name, path, runtime, version, dependencies, memory, authenticated, json_param_name):
        self.name = name
        self.path = path
        self.runtime = runtime
        self.runtimeVersion = version
        self.dependencies = dependencies
        self.memory = memory
        self.authenticated = authenticated
        self.json_param_name = json_param_name

    def __get_name__(self):
        return self.name

    def __get_path__(self):
        return self.path

    def __get_runtime__(self):
        return self.runtime

    def __get_runtime_version__(self):
        return self.runtimeVersion

    def __get_dependencies__(self):
        return self.dependencies

    def __get_memory__(self):
        return self.memory

    def __is_authenticated__(self):
        return self.authenticated

    def __get_json_param_name__(self):
        return self.json_param_name
