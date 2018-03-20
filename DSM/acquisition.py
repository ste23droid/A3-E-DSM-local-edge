import threading
import time
import os
import shutil
from socket import *
from subprocess import call

class Acquisition:

    SERVICE_OK_MSG = 'OK'
    SERVICE_FAILED_MSG = 'FAILED'
    LOCAL_IP = '127.0.0.1'
    UNICAST_PORT = 12341
    ALL_IP = '0.0.0.0'

    LOG_FILE = 'acquisition_time.csv'
    start_time = 0
    stop_time = 0

    RESULT_INSTALLED = 'installed'
    RESULT_UPDATED = 'updated'
    RESULT_FAILED = 'failed'

    def __init__(self, unicast_port):
        self.UNICAST_PORT = unicast_port
        self.unicast_socket=socket(AF_INET, SOCK_DGRAM)
        #self.unicast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.unicast_socket.bind((Acquisition.ALL_IP,Acquisition.UNICAST_PORT))

    def start(self):
        print 'Starting Domain Acquisition'
        self.recv_t = threading.Thread(target=self.__unicast_recv)
        self.recv_t.daemon = True
        self.recv_t.start()

    def stop(self):
        print 'Stopping Domain Acquisition'
        self.unicast_socket.close()
        self.recv_t.do_run = False
        #self.recv_t.join()

    def __unicast_recv(self):
        print 'Domain Unicast Receiver Started'
        self.__clearFolder('example-lambda')
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            data, rcvr = self.unicast_socket.recvfrom(1024)
            print "Domain Receiver: message received ", data
            if self.SERVICE_FAILED_MSG not in data:
                 print 'Client Discovered'
                 print 'Acquisition URL: ' + data
                 print 'Client IP: ' + rcvr[0]
                 self.__startTimer()
                 acquisition_request = self.__parse_service_request(data, rcvr[0])
                 result = self.__checkAcquisition(acquisition_request)
                 self.__stopTimer()
                 self.__logResult(result)
                 self.__clearFolder(acquisition_request[2])

    def __startTimer(self):
        self.start_time = time.time()

    def __stopTimer(self):
        self.stop_time = time.time()

    def __logResult(self, result):
        acquisition_time = str(self.stop_time - self.start_time)
        with open(self.LOG_FILE, "a") as log_file:
            log_file.write(acquisition_time + '\t' + result + '\n')

    def __clearFolder(self, repo_name):
        shutil.rmtree(repo_name)

    def __parse_service_request(self, data, client_ip):
        fields = data.rsplit(';', 1)
        repo_url = fields[0]
        service_name = fields[1]
        service_name = service_name.rsplit(';', 1)[0]
        repo_name = repo_url.rsplit('/', 1)[-1]
        return (service_name, repo_url, repo_name, client_ip)

    def __checkAcquisition(self, acquisition_request):
        service_name = acquisition_request[0]
        repo_url = acquisition_request[1]
        repo_name = acquisition_request[2]
        client_ip = acquisition_request[3]
        print 'Checking Acquisition of ' + repo_url

        path_exists = os.path.exists(repo_name)
        if not path_exists:
            print 'Acquisition result: ', self.__cloneRepo(repo_url)
        else:
            print repo_url + ' already acquired, checking for updates'
            print 'Update result: ', self.__updateRepo(repo_url, repo_name)

        result = self.__checkFunctionsInRepo(repo_name, service_name)
        if result != self.RESULT_FAILED:
            reply_msg = Acquisition.SERVICE_OK_MSG + ';' + service_name
            self.unicast_socket.sendto(reply_msg,(client_ip, Acquisition.UNICAST_PORT))
            return result
        else:
            reply_msg = Acquisition.SERVICE_FAILED_MSG + ';' + service_name
            self.unicast_socket.sendto(reply_msg,(client_ip, Acquisition.UNICAST_PORT))
            return result

    def __cloneRepo(self, repo_url):
        print 'Cloning repo ' + repo_url
        return call("git clone " + repo_url, shell=True)

    def __updateRepo(self, repo_url, repo_name):
        print 'Updating repo ' + repo_url
        return call("cd " + repo_name + ";git pull origin master", shell=True)


    def __checkFunctionsInRepo(self, repo_name, service_name):
        print 'Checking for JS functions in repo ' + repo_name
        for function_file in os.listdir(repo_name):
            if function_file.endswith("Function.js"):
                # print(os.path.join(directory, filename))
                return self.__performInstallation(repo_name, service_name, function_file)
            else:
                continue
        return False

    def __performInstallation(self, repo_name, action_name, actionSourceFile):
        print 'Installing function ' + action_name + ' as ' + actionSourceFile
        add_function_cmd = 'wsk action create ' + action_name + ' ' + actionSourceFile + ' --web yes'
        install_cmd = "cd " + repo_name + '; ' + add_function_cmd
        install_result = call(install_cmd, shell=True)
        if install_result != 0:
            print 'Updating function ' + action_name + ' as ' + actionSourceFile
            update_function_cmd = 'wsk action update ' + action_name + ' ' + actionSourceFile + ' --web yes'
            update_cmd = "cd " + repo_name + '; ' + update_function_cmd
            if call(update_cmd, shell=True) == 0:
                return self.RESULT_UPDATED
            else:
                return self.RESULT_FAILED
        else:
            return self.RESULT_INSTALLED
