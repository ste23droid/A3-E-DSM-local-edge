import time
from awareness import Awareness
from acquisition import Acquisition
from flask import Flask, request, jsonify

DEFAULT_EXECUTION_TIME = 10000 #seconds
HEARBEAT_INTERVAL = 60 #seconds
BROADCAST_IP = '10.79.11.255'
BROADCAST_PORT = 12345
app = Flask(__name__)
awareness = Awareness(BROADCAST_IP, BROADCAST_PORT, HEARBEAT_INTERVAL)
acquisition = Acquisition()


@app.route('/')
def entry():
    return 'Entry Point!'


@app.route('/identification', methods=['POST'])
def identification():
    content = request.json
    client_ip = request.remote_addr
    response_json = acquisition.__parse_request__(content)
    return jsonify(response_json)


@app.route('/monitoring')
def monitoring():
    return 'Hello World!'


if __name__ == "__main__":
    # awareness.start()
    # app.run(debug=True)
    app.run()
    #  time.sleep(DEFAULT_EXECUTION_TIME)
    # awareness.stop()
    # acquisition.stop()

