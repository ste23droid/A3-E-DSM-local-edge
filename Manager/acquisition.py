import os
import json
import re
from subprocess import call, check_output
from function import Function
import config
import requests
from os.path import dirname, abspath, join


class Acquisition:

    def __init__(self, runtimes):
        self.INSTALL_FAILED = "install_failed"
        self.INSTALL_DONE = "install_done"
        self.runtimes = runtimes
        self.map_repo_to_action_name = {}
        requests.packages.urllib3.disable_warnings()

    # def __is_compatible(self, func_repo):
    #     # TODO: for compatiblity we need to add open whisk about GPU support, and ram,
    #     # TODO: compatibility should be inserted in the config a3e file defined in the app
    #     return True

    def __parse_request__(self, json_content):
        functions = json_content['functions']
        identifications = []
        for func_repo in set(functions):
            identifications.append(self.__acquire__(func_repo))
        return {
                "identifications": identifications,
                "monitoringEndpoint": config.FLASK_MONITORING_URL,
                "websocketEndpoint": "ws://{}:{}".format(config.WEBSOCKET_HOST, config.WEBSOCKET_PORT)
               }

    def __acquire__(self, func_repo):
        splits = func_repo.split('/')
        # https://github.com/ste23droid/A3E-OpenWhisk-face-detection
        repo_owner = splits[3]
        repo_name = splits[4]
        print('Checking Acquisition of {}'.format(func_repo))

        path_exists = os.path.exists("{}/{}/{}".format(config.REPOS_PATH, repo_owner, repo_name))
        if not path_exists:
            print('Acquisition result: ', self.__clone_repo(repo_owner, func_repo))
            git_repo_has_changed = True
        else:
            print(func_repo + ' already acquired, checking for updates')
            git_repo_has_changed = self.__need_update_repo(repo_owner, repo_name, func_repo)

        # check config
        parsed_function = self.__parse_config__(repo_owner, repo_name, func_repo)
        if parsed_function is not None:

             if git_repo_has_changed or not self.__is_function_installed(parsed_function):
                 # update function on wsk
                 install_result = self.__perform_installation(parsed_function)
                 if install_result != self.INSTALL_FAILED:
                     return {
                         "function": parsed_function.repo,
                         "compatible": True,
                         "name": "{}/{}".format(parsed_function.repo_owner, parsed_function.name)
                     }
                 else:
                     # install failed, remove repository folder
                     repositories_parent_dir = dirname(abspath(__file__))
                     repo_dir = join(join(repositories_parent_dir, "repositories"),
                                     "{}/{}".format(parsed_function.repo_owner, parsed_function.repo_name))
                     call(f"rm -rf {repo_dir}", shell=True)

             else:
                 # just return function
                 return {
                     "function": parsed_function.repo,
                     "compatible": True,
                     "name": "{}/{}".format(parsed_function.repo_owner, parsed_function.name)
                 }

        return {
                  "function": func_repo,
                  "compatible": False
               }

    def __clone_repo(self, repo_owner, repo_url):
        print('Cloning repo {}'.format(repo_url))
        return call("mkdir -p {}/{}; ".format(config.REPOS_PATH, repo_owner) +
                    "cd {}/{}; ".format(config.REPOS_PATH, repo_owner) +
                    "git clone {} ".format(repo_url), shell=True)

    def __is_function_installed(self, parsed_function):
        raw_actions_list = check_output("{} action list -i".format(config.WSK_PATH), shell=True).splitlines()[1:]
        parsed_action_list = []
        for raw_action_name in raw_actions_list:
            parsed_action_list.append(raw_action_name.split()[0].decode("utf-8"))
        installed_func_name = "/{}/{}/{}".format(config.WHISK_NAMESPACE, parsed_function.repo_owner, parsed_function.name)
        if installed_func_name in parsed_action_list:
            print(f"Function {installed_func_name} is already installed!!!")
            return True
        return False

    def __need_update_repo(self, repo_owner, repo_name, repo_url):
        # TODO mettere cartelle per namespace utente
        print('Updating repo {}'.format(repo_url))

        result = check_output("cd {}/{}/{}; ".format(config.REPOS_PATH, repo_owner, repo_name) +
                              "git pull origin master ", shell=True).splitlines()[0]
        # b'Already up to date.' in python 3.6
        if result.decode("utf-8") == 'Already up to date.':
            print('Already up to date.')
            return False
        return True

    def __parse_config__(self, repo_owner, repo_name, func_repo):
        print('Checking for A3E config file in repo')
        # print os.path.dirname(os.path.abspath(__file__))
        repositories_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repositories")
        repo_directory = os.path.join(os.path.join(repositories_directory, repo_owner), repo_name)
        print(repo_directory)

        # print project_dir
        for file_name in os.listdir(repo_directory):
            if file_name == config.CONFIG_FILE_NAME:
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

                    # save mapping repo to action name
                    self.map_repo_to_action_name[func_repo] = "/{}/{}/{}".format(config.WHISK_NAMESPACE, repo_owner, func_name)

                    return Function(func_name, func_repo, repo_owner, repo_name, func_path, runtime, runtime_version,
                                    func_dependencies, memory, authenticated, func_json_param_name)
        print("Error... no config file found!!!")
        return None

    def __satisfies_dependencies(self, runtime, function):

        if runtime["language"] == function.runtime and runtime["languageVersion"] == function.runtime_version:
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

    def __perform_installation(self, func):
        print("Installing (creating or updating) function {} from repo {}".format(func.name, func.repo))

        # # create database to hold metrics for this function
        # # http://docs.couchdb.org/en/2.3.0/api/database/common.html#put--db
        # create_db_response = requests.put("{}/{}_{}_{}".format(config.COUCH_DB_BASE,
        #                                                        config.DB_METRICS_BASE_NAME,
        #                                                        func.repo_owner.lower(),
        #                                                        func.name.lower()))
        # if create_db_response.status_code == 201:
        #     print("Function metrics db created successfully")
        # elif create_db_response.status_code == 412:
        #     print("Function metrics db already exists, no creation needed")
        # else:
        #     print(create_db_response.content)
        #     print("Error creating function metrics db, code {}".format(create_db_response.status_code))

        # select a known suitable runtime
        chosen_runtime = None
        if len(self.runtimes) == 1:
            chosen_runtime = self.runtimes[0]
        else:
            # find the first suitable runtime for the function
            for runtime in self.runtimes:
                if self.__satisfies_dependencies(runtime, func):
                    chosen_runtime = runtime
                    break

        # docker hub name of the runtime identifies a custom runtime
        hub_runtime_name = chosen_runtime["name"]

        # Each action is created with the following name: repoOwner_functionName
        if not func.authenticated:
            # https://github.com/apache/incubator-openwhisk/blob/master/docs/webactions.md
            #  wsk package update --- update an existing package, or create a package if it does not exist
            call('{} package update {} --insecure'.format(config.WSK_PATH, func.repo_owner), shell=True)
            #  wsk action update --- update an existing action, or create an action if it does not exist
            update_function_cmd = '{} action update {}/{} --docker \
                                   {} {} --web true -m {} --insecure'.format(config.WSK_PATH,
                                                                            func.repo_owner,
                                                                            func.name,
                                                                            hub_runtime_name,
                                                                            func.path,
                                                                            func.memory)
        else:
            # https://github.com/apache/incubator-openwhisk/blob/master/docs/rest_api.md
            update_function_cmd = '{} action update {}/{} --docker \
                                   {} {} -m {} --insecure'.format(config.WSK_PATH,
                                                                  func.repo_owner,
                                                                  func.name,
                                                                  hub_runtime_name,
                                                                  func.path,
                                                                  func.memory)
        if call(update_function_cmd, shell=True) != 0:
                return self.INSTALL_FAILED
        return self.INSTALL_DONE

    def __get_function_endpoint(self, func):
        # https://github.com/apache/incubator-openwhisk/blob/master/docs/rest_api.md
        if not func.authenticated:
          return "https://{}/api/{}/web/{}/{}/{}".format(config.WHISK_API_HOST,
                                                         config.WHISK_API_VERSION,
                                                         config.WHISK_NAMESPACE,
                                                         func.repo_owner,
                                                         func.name)

        return "https://{}/api/{}/namespaces/{}/actions/{}/{}".format(config.WHISK_API_HOST,
                                                                      config.WHISK_API_VERSION,
                                                                      config.WHISK_NAMESPACE,
                                                                      func.repo_owner,
                                                                      func.name)
