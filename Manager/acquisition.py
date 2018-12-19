from __future__ import print_function
import os
import json
# open whisk cli
from subprocess import call
from function import Function

class Acquisition:

    def __init__(self, runtimes):
        self.whisk_namespace = "https://whisknamespace/"
        self.ws_endpoint = "wss://whisknamespace/"
        self.CONFIG_FILE_NAME = "a3e_config.json"
        self.INSTALL_UPDATED = "install_updated"
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
            identifications.append(self.__acquire(func_repo))
        return {
            "identifications": identifications,
            "monitoring_endpoint": self.whisk_namespace + "monitoring",
            "websocket_endpoint": self.ws_endpoint
            }

    def __acquire(self, func_repo):
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
        parsed_function = self.__parse_config__(repo_owner, repo_name)
        if parsed_function is not None:
             # try to create function on openwhisk
             install_result = self.__perform_installation(repo_name, parsed_function)
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

    def __parse_config__(self, repo_owner, repo_name):
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
                    return Function(func_name, func_path, runtime, runtime_version,
                                    func_dependencies, memory, authenticated, func_json_param_name)
        return None

    def __perform_installation(self, repo_name, parse_result):
        func_name = parse_result[0]
        print(func_name)
        func_file_path = parse_result[1]
        print(func_file_path)
        runtime = parse_result[2]
        print(runtime)
        runtime_version = parse_result[3]
        print(runtime_version)
        memory = parse_result[4]
        dependencies = parse_result[5]
        print('Installing function ' + func_name + ' as ' + func_file_path)
        add_function_cmd = 'wsk action create ' + func_name + ' ' + func_file_path + ' --web yes --insecure'
        install_cmd = "cd " + repo_name + '; ' + add_function_cmd
        install_result = call(install_cmd, shell=True)
        if install_result != 0:
            print('Updating function ' + func_name + ' as ' + func_file_path)
            update_function_cmd = 'wsk action update ' + func_name + ' ' + func_file_path + ' --web yes --insecure'
            update_cmd = "cd " + repo_name + '; ' + update_function_cmd
            if call(update_cmd, shell=True) == 0:
                return self.INSTALL_UPDATED
            else:
                return self.INSTALL_FAILED
        else:
            return self.INSTALL_DONE

    def __get_function_endpoint(self, func_repo):
        pass
