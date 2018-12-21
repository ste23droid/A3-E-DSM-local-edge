from __future__ import print_function
import os
import json
import re
# open whisk cli
from subprocess import call
from function import Function

class Acquisition:

    def __init__(self, runtimes):
        self.whisk_namespace = "https://whisknamespace/"
        self.ws_endpoint = "wss://whisknamespace/"
        self.CONFIG_FILE_NAME = "a3e_config.json"
        self.INSTALL_FAILED = "install_failed"
        self.INSTALL_DONE = "install_done"
        self.REPOS_PATH = "./repositories"
        self.RUNTIMES = runtimes

    def __is_compatible(self, func_repo):
        # TODO: for compatiblity we need to add open whisk about GPU support, and ram,
        # TODO: compatibility should be inserted in the config a3e file defined in the app
        return True

    def __get_func_http_endpoint(self, func_name):
        return self.whisk_namespace + "/" + func_name

    def __parse_request__(self, json_content):
        functions = json_content['functions']
        identifications = []
        for func_repo in set(functions):
            identifications.append(self.__acquire__(func_repo))
        return {
            "identifications": identifications,
            "monitoring_endpoint": self.whisk_namespace + "monitoring",
            "websocket_endpoint": self.ws_endpoint
            }

    def __acquire__(self, func_repo):
        # return True
        splits = func_repo.split('/')
        # https://github.com/ste23droid/A3E-AWS-face-detection
        repo_owner = splits[3]
        repo_name = splits[4]
        print('Checking Acquisition of {}'.format(func_repo))

        path_exists = os.path.exists("{}/{}/{}".format(self.REPOS_PATH, repo_owner, repo_name))
        if not path_exists:
            print('Acquisition result: ', self.__clone_repo(repo_owner, func_repo))
        else:
            print(func_repo + ' already acquired, checking for updates')
            print('Update result: ', self.__update_repo(repo_owner, repo_name, func_repo))

        # check config
        parsed_function = self.__parse_config__(repo_owner, repo_name, func_repo)
        if parsed_function is not None:
             # try to create function on openwhisk
             install_result = self.__perform_installation(parsed_function)
             if install_result != self.INSTALL_FAILED:
                 return {
                     "function": func_repo,
                     "compatible": True,
                     "endpoint": self.__get_function_endpoint(func_repo)
                 }
        return {
                  "function": func_repo,
                  "compatible": False
               }

    def __clone_repo(self, repo_owner, repo_url):
        print('Cloning repo {}'.format(repo_url))
        return call("mkdir -p {}/{}; ".format(self.REPOS_PATH, repo_owner) +
                    "cd {}/{}; ".format(self.REPOS_PATH, repo_owner) +
                    "git clone {} ".format(repo_url), shell=True)


    def __update_repo(self, repo_owner, repo_name, repo_url):
        # TODO mettere cartelle per namespace utente
        print('Updating repo {}'.format(repo_url))
        return call("cd {}/{}/{}; ".format(self.REPOS_PATH, repo_owner, repo_name) +
                    "git pull origin master ", shell=True)

    def __parse_config__(self, repo_owner, repo_name, func_repo):
        print('Checking for A3E config file in repo')
        # print os.path.dirname(os.path.abspath(__file__))
        repositories_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repositories")
        repo_directory = os.path.join(os.path.join(repositories_directory, repo_owner), repo_name)
        print(repo_directory)

        # print project_dir
        for file_name in os.listdir(repo_directory):
            if file_name == self.CONFIG_FILE_NAME:
                file_path = os.path.join(repo_directory, file_name)
                print(file_path)
                func_dependencies = []
                with open(file_path, mode='r') as f:
                    json_content = json.load(f)
                    func_name = json_content["functionName"]
                    runtime = json_content["runtime"]
                    runtime_version = json_content["runtimeVersion"]
                    memory = json_content["memory"]
                    authenticated = json_content["authenticated"]
                    func_json_param_name = json_content["paramName"]
                    for dependency in json_content["dependencies"]:
                        func_dependencies.append(dependency)
                    func_path = os.path.join(repo_directory, json_content["path"])
                    return Function(func_name, func_repo, func_path, runtime, runtime_version,
                                    func_dependencies, memory, authenticated, func_json_param_name)
        return None

    def __satisfies_dependencies(self, runtime, function):

        if runtime["language"] == function.runtime and runtime["languageVersion"] == function.runtimeVersion:
            runtime_libs_set = set(dependency["lib"] for dependency in runtime["dependencies"])
            function_libs_set = set(dependency["lib"] for dependency in function.dependencies)
            diff_set = [lib for lib in runtime_libs_set if lib not in function_libs_set]

            if len(diff_set) >= 0:
                # runtime may have exact same dependencies or more dependencies than the function
                for f_dep in function.dependencies:
                    f_lib_version = f_dep["version"]
                    # requirement can be >= or ==
                    f_lib_requirement = f_lib_version[:2]
                    f_lib_num_version = int(re.sub(".", "", f_lib_version[2:]))
                    r_lib_num_version = \
                        [dependency["version"] for dependency in runtime["dependencies"] if
                         dependency["lib"] == f_dep["lib"]][0]
                    if (f_lib_requirement == ">=" and r_lib_num_version < f_lib_num_version) or \
                            (f_lib_requirement == "==" and r_lib_num_version != f_lib_num_version):
                        return False
                return True

        return False

    def __perform_installation(self, function):
        print("Installing (creating or updating) function {} from repo {}".format(function.name, function.repo))

        # select a known suitable runtime
        chosen_runtime = None
        if len(self.RUNTIMES == 1):
            chosen_runtime = self.RUNTIMES[0]
        else:
            # find the first suitable runtime for the function
            for runtime in self.RUNTIMES:
                if self.__satisfies_dependencies(runtime, function):
                    chosen_runtime = runtime
                    break

        # docker hub name of the runtime identifies a custom runtime
        hub_runtime_name = chosen_runtime["name"]

        # wsk update can also create an action if it does not exist! see docs
        if not function.authenticated:
            update_function_cmd = 'wsk action update {} --docker \
                                   {} {} --web yes -m {} --insecure'.format(function.name,
                                                                            hub_runtime_name,
                                                                            function.path,
                                                                            function.memory)
        else:
            update_function_cmd = 'wsk action update {} --docker \
                                   {} {} -m {} --insecure'.format(function.name,
                                                                  hub_runtime_name,
                                                                  function.path,
                                                                  function.memory)

        if call(update_function_cmd, shell=True) != 0:
                return self.INSTALL_FAILED
        return self.INSTALL_DONE

    def __get_function_endpoint(self, func_repo):
        pass
