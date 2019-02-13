import re
from subprocess import call, check_output
import config
import requests


class Allocation:

    def __init__(self):
        self.INSTALL_FAILED = "install_failed"
        self.INSTALL_DONE = "install_done"
        requests.packages.urllib3.disable_warnings()

    def __get_runtimes(self):
        known_runtimes = []
        get_list_runtimes = requests.get("{}/{}/_all_docs".format(config.COUCH_DB_BASE, config.DB_RUNTIMES_NAME))
        if get_list_runtimes.status_code == 200:
            list_runtimes = get_list_runtimes.json()
            # print(type(list_runtimes))
            for elem in list_runtimes["rows"]:
                get_runtime = requests.get("{}/{}/{}".format(config.COUCH_DB_BASE,
                                                             config.DB_RUNTIMES_NAME,
                                                             elem["id"]))
                if get_runtime.status_code == 200:
                    known_runtimes.append(get_runtime.json())
        else:
            print("Error, unable to get any runtime!!!")
        assert len(known_runtimes) > 0
        return known_runtimes

    def __is_function_installed__(self, parsed_function):
        raw_actions_list = check_output("{} action list -i".format(config.WSK_PATH), shell=True).splitlines()[1:]
        parsed_action_list = []
        for raw_action_name in raw_actions_list:
            parsed_action_list.append(raw_action_name.split()[0].decode("utf-8"))
        installed_func_name = "/{}/{}/{}".format(config.WHISK_NAMESPACE, parsed_function.repo_owner, parsed_function.name)
        if installed_func_name in parsed_action_list:
            print(f"Function {installed_func_name} is already installed!!!")
            return True
        return False

    def __satisfies_dependencies(self, runtime, function):

        if runtime["language"] == function.runtime and runtime["languageVersion"] == function.runtime_version:
            runtime_libs_set = set(dependency["lib"] for dependency in runtime["dependencies"])
            function_libs_set = set(dependency["lib"] for dependency in function.dependencies)

            # runtime may have exact same dependencies or more dependencies than the function
            if runtime_libs_set.issuperset(function_libs_set):
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

    def __perform_installation__(self, func):
        print("Installing (creating or updating) function {} from repo {}".format(func.name, func.repo))

        # create database to hold metrics for this function, called "metrics-repowner-reponame"
        # http://docs.couchdb.org/en/2.3.0/api/database/common.html#put--db
        create_db_response = requests.put("{}/{}-{}-{}".format(config.COUCH_DB_BASE,
                                                               config.DB_METRICS_NAME,
                                                               func.repo_owner.lower(),
                                                               func.name.lower()))
        if create_db_response.status_code == 201:
            print("Function metrics db created successfully")
        elif create_db_response.status_code == 412:
            print("Function metrics db already exists, no creation needed")
        else:
            print(create_db_response.content)
            print("Error creating function metrics db, code {}".format(create_db_response.status_code))
            return self.INSTALL_FAILED

        # select a known suitable runtime
        chosen_runtime = None
        runtimes = self.__get_runtimes()
        if len(runtimes) == 1:
            chosen_runtime = runtimes[0]
        else:
            # find the first suitable runtime for the function
            for runtime in runtimes:
                if self.__satisfies_dependencies(runtime, func):
                    chosen_runtime = runtime
                    break

        if chosen_runtime is None:
            print(f"No runtime satisfies the dependencies of function {func.name}, cannot install function!!!")
            return self.INSTALL_FAILED

        # name of the runtime identifies a docker hub image, thus a custom runtime
        hub_runtime_name = chosen_runtime["name"]

        # Each action is created with the following name: repoOwner/functionName
        if not func.authenticated:
            # NOT AUTHENTICATED, is an OPEN WHISK WEB ACTION
            # https://github.com/apache/incubator-openwhisk/blob/master/docs/webactions.md
            #  wsk package update --- update an existing package, or create a package if it does not exist
            call('{} package update {} --insecure'.format(config.WSK_PATH, func.repo_owner), shell=True)
            #  wsk action update --- update an existing action, or create an action if it does not exist
            update_function_cmd = '{} action update {}/{} --docker \
                                        {} {} --web True -m {} --insecure'.format(config.WSK_PATH,
                                                                                  func.repo_owner,
                                                                                  func.name,
                                                                                  hub_runtime_name,
                                                                                  func.path,
                                                                                  func.memory)
        else:
            # authenticated, is a OPEN WHISK ACTION
            # https://github.com/apache/incubator-openwhisk/blob/master/docs/rest_api.md
            update_function_cmd = '{} action update {}/{} --docker \
                                        {} {} -m {} --insecure'.format(config.WSK_PATH,
                                                                       func.repo_owner,
                                                                       func.name,
                                                                       hub_runtime_name,
                                                                       func.path,
                                                                       func.memory)
        if call(update_function_cmd, shell=True) != 0:
            print("wsk was not able to create the action, install failed!!!")
            return self.INSTALL_FAILED
        return self.INSTALL_DONE
