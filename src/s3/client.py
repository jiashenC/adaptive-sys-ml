import time
from threading import Thread
import os

import avro.ipc as ipc
import avro.protocol as protocol
import numpy as np

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

# data packet format definition
PROTOCOL = protocol.parse(open(DIR_PATH + '/resource/message/message.avpr').read())
DEVICES = ['192.168.1.14', '192.168.1.15']


def send_request(frame, id, ip):
    client = ipc.HTTPTransceiver(ip, 12345)
    requestor = ipc.Requestor(PROTOCOL, client)

    data = dict()
    data['input'] = frame.astype(np.float32).tobytes()
    data['identifier'] = id

    requestor.request('forward', data)
    client.close()


def master():
    data = np.random.random_sample([100])
    for i in range(100):
        Thread(target=send_request, args=(data, i, DEVICES[i % 2])).start()
        time.sleep(0.03)


def main():
    master()


if __name__ == '__main__':
    main()
