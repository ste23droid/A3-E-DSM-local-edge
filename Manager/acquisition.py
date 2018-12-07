import os
import json
# open whisk cli
from subprocess import call


class Acquisition:

    def __init__(self):
        self.whisk_namespace = "https://whisknamespace/"
        self.ws_endpoint = "wss://whisknamespace/"
        self.CONFIG_FILE_NAME = "a3e_config.json"
        self.INSTALL_UPDATED = "install_updated"
        self.INSTALL_FAILED = "install_failed"
        self.INSTALL_DONE = "install_done"
        self.CONFIG_PARSE_FAIL = "config_parse_fail"

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
            is_compatible = self.__is_compatible("requirements")

            if is_compatible:
                self.__check_acquisition(func_repo)

                identification = {
                                   "function": func_repo,
                                   "compatible": True,
                                   "endpoint": self.__get_func_http_endpoint(func_repo)
                                 }
            else:
                identification = {
                                  "function": func_repo,
                                  "compatible": False,
                                 }
            identifications.append(identification)
        return {
            "identifications": identifications,
            "monitoring_endpoint": self.whisk_namespace + "monitoring",
            "websocket_endpoint": self.ws_endpoint
        }

    def __check_acquisition(self, func_repo):
        splits = func_repo.split('/')
        repo_name = splits[4]
        print 'Checking Acquisition of ' + func_repo

        path_exists = os.path.exists(repo_name)
        if not path_exists:
            print 'Acquisition result: ', self.__clone_repo(func_repo)
        else:
            print func_repo + ' already acquired, checking for updates'
            print 'Update result: ', self.__update_repo(func_repo, repo_name)

        parse_result = self.__parse_config(repo_name)
        if parse_result != self.CONFIG_PARSE_FAIL:
            install_result = self.__perform_installation(repo_name, parse_result)
            print install_result


    def __clone_repo(self, func_repo):
        print 'Cloning repo ' + func_repo
        return call("git clone " + func_repo, shell=True)

    def __update_repo(self, func_repo, repo_name):
        # TODO mettere cartelle per namespace utente
        print 'Updating repo ' + func_repo
        return call("cd " + repo_name + "; git pull origin master", shell=True)

    def __parse_config(self, repo_name):
        print 'Checking for A3E config file in repo'
        # print os.path.dirname(os.path.abspath(__file__))
        repo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), repo_name)
        # print project_dir
        for file_name in os.listdir(repo_dir):
            if file_name == "a3e_config.json":
                file_path = os.path.join(repo_dir, file_name)
                # print file_path
                with open(file_path, mode='r') as f:
                    json_content = json.load(f)
                    runtime = json_content["runtime"]
                    runtime_version = json_content["version"]
                    func_file_path = os.path.join(repo_dir, json_content["path"])
                    func_name = json_content["name"]
                    return func_name, func_file_path, runtime, runtime_version
        return self.CONFIG_PARSE_FAIL

    def __perform_installation(self, repo_name, parse_result):
        func_name = parse_result[0]
        print func_name
        func_file_path = parse_result[1]
        print func_file_path
        runtime = parse_result[2]
        print runtime
        runtime_version = parse_result[3]
        print runtime_version
        print 'Installing function ' + func_name + ' as ' + func_file_path
        add_function_cmd = 'wsk action create ' + func_name + ' ' + func_file_path + ' --web yes'
        install_cmd = "cd " + repo_name + '; ' + add_function_cmd
        install_result = call(install_cmd, shell=True)
        if install_result != 0:
            print 'Updating function ' + func_name + ' as ' + func_file_path
            update_function_cmd = 'wsk action update ' + func_name + ' ' + func_file_path + ' --web yes'
            update_cmd = "cd " + repo_name + '; ' + update_function_cmd
            if call(update_cmd, shell=True) == 0:
                return self.INSTALL_UPDATED
            else:
                return self.INSTALL_FAILED
        else:
            return self.INSTALL_DONE
