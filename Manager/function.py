

class Function:

    def __init__(self, name, repo, path, runtime, version, dependencies, memory, authenticated, json_param_name):
        self.name = name
        self.repo = repo
        self.path = path
        self.runtime = runtime
        self.runtimeVersion = version
        self.dependencies = dependencies
        self.memory = memory
        self.authenticated = authenticated
        self.json_param_name = json_param_name