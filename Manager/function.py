

class Function:

    def __init__(self, name, repo, repo_owner, repo_name,
                 path, runtime, runtime_version, dependencies,
                 memory, authenticated, json_param_name):
        self.name = name
        self.repo = repo
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.path = path
        self.runtime = runtime
        self.runtime_version = runtime_version
        self.dependencies = dependencies
        self.memory = memory
        self.authenticated = authenticated
        self.json_param_name = json_param_name