import os
import json
from subprocess import call, check_output
from function import Function
import config
import requests
from os.path import dirname, abspath, join


class Acquisition:

    def __init__(self, allocation):
        self.INSTALL_FAILED = "install_failed"
        self.INSTALL_DONE = "install_done"
        self.allocation = allocation
        requests.packages.urllib3.disable_warnings()

    def __parse_request__(self, json_content):
        functions = json_content['functions']
        identifications = []
        for func_repo in set(functions):
            identifications.append(self.__acquire__(func_repo))
        return {
                "identifications": identifications,
                "monitoringEndpoint": "http://{}:{}/monitoring".format(config.PUBLIC_HOST_IP, config.FLASK_PORT),
                "websocketEndpoint": "ws://{}:{}/".format(config.PUBLIC_HOST_IP, config.WEBSOCKET_PORT)
               }

    def __acquire__(self, func_repo):
        splits = func_repo.split('/')
        # https://github.com/ste23droid/A3E-OpenWhisk-face-detection
        repo_owner = splits[3]
        repo_name = splits[4]
        #print('Checking Acquisition of {}'.format(func_repo))

        if not self.__repo_blacklisted(func_repo):
            path_exists = os.path.exists("{}/{}/{}".format(config.REPOS_PATH, repo_owner, repo_name))
            if not path_exists:
                print('Acquisition result: ', self.__clone_repo(repo_owner, func_repo))
                git_repo_has_changed = True
            else:
                print(func_repo + ' already acquired, checking for updates')
                git_repo_has_changed = self.__need_update_repo(repo_owner, repo_name, func_repo)

            # check config
            parsed_function = self.__parse_config__(repo_owner, repo_name, func_repo)

            if parsed_function is not None and self.__is_compatible_with_domain(parsed_function):

                 if git_repo_has_changed or not self.allocation.__is_function_installed__(parsed_function):
                     # update function on wsk
                     install_result = self.allocation.__perform_installation__(parsed_function)
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

    def __repo_blacklisted(self, repo):
        # todo: improve in future release
        return False

    def __is_compatible_with_domain(self, parsed_function):
        # TODO: for compatiblity we need to think about GPU support for example
        # TODO: compatibility should be inserted in the a3e config file
        return True

    def __clone_repo(self, repo_owner, repo_url):
        print('Cloning repo {}'.format(repo_url))
        return call("mkdir -p {}/{}; ".format(config.REPOS_PATH, repo_owner) +
                    "cd {}/{}; ".format(config.REPOS_PATH, repo_owner) +
                    "git clone {} ".format(repo_url), shell=True)

    def __need_update_repo(self, repo_owner, repo_name, repo_url):
        #print('Check if we need to update repo {}'.format(repo_url))

        result = check_output("cd {}/{}/{}; ".format(config.REPOS_PATH, repo_owner, repo_name) +
                              "git pull origin master ", shell=True).splitlines()[0]
        # b'Already up to date.' in python 3.6, or use the method .decode("utf-8")
        if result.decode("utf-8") == 'Already up to date.':
            #print(f'{repo_url} already up to date')
            return False
        return True

    def __parse_config__(self, repo_owner, repo_name, func_repo):
        # print('Checking for A3E config file in repo')
        # print os.path.dirname(os.path.abspath(__file__))
        repositories_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repositories")
        repo_directory = os.path.join(os.path.join(repositories_directory, repo_owner), repo_name)
        # print(repo_directory)

        for file_name in os.listdir(repo_directory):
            if file_name == config.CONFIG_FILE_NAME:
                file_path = os.path.join(repo_directory, file_name)
                # print(file_path)
                func_dependencies = []
                with open(file_path, mode='r') as f:
                    json_content = json.load(f)
                    func_name = json_content["functionName"]
                    runtime = json_content["runtime"]
                    runtime_version = json_content["runtimeVersion"]
                    memory = json_content["memory"]
                    authenticated = json_content["authenticated"]
                    for dependency in json_content["dependencies"]:
                        func_dependencies.append(dependency)
                    func_path = os.path.join(repo_directory, json_content["path"])

                    # todo: move this after installation of the action, map microservice's repository url to wsk action name in couch db
                    self.__check_mapping(repo_owner, func_name, func_repo)

                    return Function(func_name, func_repo, repo_owner, repo_name, func_path, runtime, runtime_version,
                                    func_dependencies, memory, authenticated)

        print("Error... no config file found!!!")
        return None

    # todo: move inside allocation__perform_installation__
    def __check_mapping(self, repo_owner, func_name, func_repo):
        # https://github.com/apache/incubator-openwhisk/blob/master/docs/rest_api.md
        #
        # WEB ACTIONS
        # URL: https://192.168.1.214/api/v1/web/guest/ste23droid/faceDetection
        # ACTION NAME: /guest/ste23droid/faceDetection                                        private blackbox

        # NORMAL ACTIONS
        # URL: https://192.168.1.214/api/v1/namespaces/guest/actions/ste23droid/faceDetection
        # ACTION NAME: /guest/ste23droid/faceDetection                                        private blackbox



        # check if mapping already exists, POST /{db}/_find
        check_mapping_request = requests.post("{}/{}/_find".format(config.COUCH_DB_BASE, config.DB_MAPPINGS_NAME),
                                              data=json.dumps({"selector": {"repo": func_repo}}),
                                              verify=False,
                                              headers=config.APPLICATION_JSON_HEADER)
        print(check_mapping_request.json())
        if check_mapping_request.status_code == 200:
            json_result = check_mapping_request.json()
            if len(json_result["docs"]) > 0:
                doc_id = json_result["docs"][0]["_id"]
                doc_revision = json_result["docs"][0]["_rev"]

                # mapping = {
                #     "actionName": "/{}/{}/{}".format(config.WHISK_NAMESPACE, repo_owner, func_name),
                #     "repo": func_repo,
                #     "_rev": doc_revision
                # }

                mapping = {
                    "actionName": "{}/{}".format(repo_owner, func_name),
                    "repo": func_repo,
                    "_rev": doc_revision
                }

                # update existing mapping, PUT /{db}/{docid}
                update_mapping_request = requests.put(
                    "{}/{}/{}".format(config.COUCH_DB_BASE, config.DB_MAPPINGS_NAME, doc_id),
                    data=json.dumps(mapping),
                    verify=False,
                    headers=config.APPLICATION_JSON_HEADER)
                print(update_mapping_request.json())
                if update_mapping_request.status_code == 201:
                    print("Mapping repo {} to action name updated!!!".format(func_repo))
                else:
                    print("Unable to update mapping for repo {}".format(func_repo))


            else:
                print("No mapping to an action found for repo {}, creating it...".format(func_repo))

                # mapping = {
                #     "actionName": "/{}/{}/{}".format(config.WHISK_NAMESPACE, repo_owner, func_name),
                #     "repo": func_repo
                # }

                mapping = {
                    "actionName": "{}/{}".format(repo_owner, func_name),
                    "repo": func_repo
                }

                post_mapping_request = requests.post("{}/{}".format(config.COUCH_DB_BASE, config.DB_MAPPINGS_NAME),
                                                     data=json.dumps(mapping),
                                                     verify=False,
                                                     headers=config.APPLICATION_JSON_HEADER)

                if post_mapping_request.status_code == 201:
                    print("Mapping for repo {} has been created!!!".format(func_repo))

                else:
                    print("Error creating mapping for repo {}".format(func_repo))

        else:
            print("Unable to query mappings!!!")