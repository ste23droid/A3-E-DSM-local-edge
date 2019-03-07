import config
import requests
import time
import os
import numpy
import cv2
import base64
import json
import re


class LoaderSimulator:

    def __init__(self):
        self.iterations = 0
        self.start_time = time.time()

    def start(self):
        print("Start Loader")
        self.__loader()

    def __loader(self):
        print('Load Simulator starting load')

        # TO CONFIGURE
        FUNC = "ste23droid/imageRecognition"
        # TO CONFIGURE

        test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testing")
        if FUNC == "ste23droid/faceDetection":
            images_dir = os.path.join(test_images_dir, "faceDetection")
        elif FUNC == "ste23droid/imageRecognition":
            images_dir = os.path.join(test_images_dir, "imageRecognition")
        else:
            images_dir = os.path.join(test_images_dir, "neuralTransfer")

        images_path = [os.path.join(images_dir, f) for f in os.listdir(images_dir)]

        # prepare base 64 encodings
        base64_list = []
        for image_path in images_path:
            npimg = numpy.fromfile(image_path, numpy.uint8)
            img = cv2.imdecode(npimg, 1)
            # maximum quality as we have on mobiles
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
            retval, buffer = cv2.imencode('.jpg', img, encode_param)
            base_64_encoded = base64.b64encode(buffer)
            base_64_string = base_64_encoded.decode("utf-8", "ignore")
            base64_list.append(base_64_string)

        while True:
            # images selected with rotation, no randomicity
            base_64_image_selected = base64_list[self.iterations % len(base64_list)]

            if FUNC != "ste23droid/neuralTransfer":
                a3e_request = {
                    "image": base_64_image_selected
                }
            else:
                a3e_request = {
                    "image": base_64_image_selected,
                    "style": 0
                }

            ### make the load request
            json_string_payload = json.dumps(a3e_request)
            start_request = time.time()
            post_request = requests.post("http://{}:8888/api/v1/web/guest/{}?blocking=true&result=true".format(config.PRIVATE_HOST_IP, FUNC),
                          data=json_string_payload,
                          verify=False,
                          headers=config.APPLICATION_JSON_HEADER)
            delta_seconds = time.time() - start_request
            print("Time to make load request sec {}".format(delta_seconds))
            #print(post_request.json())


            ## save the load request to metrics db
            # function_name is for example ste23droid/faceDetection
            func_name_for_db = re.sub("/", "-", FUNC).lower()
            # db name is for example metrics-ste23droid-facedetection
            post_db_request = requests.post("{}/{}-{}".format(config.COUCH_DB_BASE,
                                                              config.DB_METRICS_NAME,
                                                              func_name_for_db),
                                            data=json.dumps({"execTimeSec": delta_seconds,
                                                             "payloadBytes": len(json_string_payload),
                                                             "requestTime": time.time()}),
                                            verify=False,
                                            headers=config.APPLICATION_JSON_HEADER)
            #print("Post loader exec metrics to db, response code: {}".format(post_db_request))

            #sleep before next iteration
            deltaSec = time.time() - self.start_time

            # VERY LIGHT: 5 sec
            # LIGHT: 3 sec
            # MED: 1 sec
            # HIGH 0.7 sec
            # VERY HIGH 0.4

            if deltaSec < 480:
                time.sleep(2)
            elif deltaSec < 480*2:
                time.sleep(1)
            elif deltaSec < 480*3:
                time.sleep(1.5)
            elif deltaSec < 480*4:
                time.sleep(0.7)
            else:
                time.sleep(3.5)

            self.iterations = self.iterations + 1

