import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from multiprocessing import Queue
from threading import Thread
import tensorflow as tf
from keras.layers import Dense, Input
from keras.models import Model
import avro.ipc as ipc
import avro.protocol as protocol
import numpy as np
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

# read data packet format.
PROTOCOL = protocol.parse(open(DIR_PATH + '/resource/message/message.avpr').read())
SIZE = 10


class Responder(ipc.Responder):
    """ Responder called by handler when got request. """

    def __init__(self):
        ipc.Responder.__init__(self, PROTOCOL)

    def invoke(self, msg, req):
        """
            This function is invoked by do_POST to handle the request. Invoke handles
            the request and get response for the request. This is the key of each node.
            All models forwarding and output redirect are done here. Because the invoke
            method of initializer only needs to receive the data packet, it does not do
            anything in the function and return None.
            Because this is a node class, it has all necessary code here for handling
            different inputs. Basically the logic is load model as the previous layer
            request and run model inference. And it will send the current layer output
            to next layer. We write different model's code all here for the sake of
            convenience. In order to avoid long waiting time of model reloading, we
            make sure each node is assigned to a unique job each time, so it does not
            need to reload the model.
            Args:
                msg: Meta data.
                req: Contains data packet.
            Returns:
                None: It just acts as confirmation for sender.
            Raises:
                AvroException: if the data does not have correct syntac defined in Schema
        """
        node = Node.create()
        try:
            id, data = int(req['identifier']), req['input']
            if not node.queue.full():
                data = np.fromstring(data, np.float32).reshape([2000])
                node.queue.put((id, data))
                return False
            else:
                return True
        except Exception, e:
            print 'Message exception'


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """
            do_POST is automatically called by ThreadedHTTPServer. It creates a new
            responder for each request. The responder generates response and write
            response to data sent back.
        """
        self.responder = Responder()
        call_request_reader = ipc.FramedReader(self.rfile)
        call_request = call_request_reader.read_framed_message()
        resp_body = self.responder.respond(call_request)
        self.send_response(200)
        self.send_header('Content-Type', 'avro/binary')
        self.end_headers()
        resp_writer = ipc.FramedWriter(self.wfile)
        resp_writer.write_framed_message(resp_body)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Handle requests in separate thread. """


class Node:
    instance = None

    @classmethod
    def create(cls):
        if cls.instance is None:
            cls.instance = cls()

            data = np.random.random_sample([2000])
            img_input = Input([2000])
            slow = Dense(2000)(img_input)
            model = Model(img_input, slow)
            model.predict(np.array([data]))

            cls.instance.model = model
            Thread(target=cls.instance.inference, args=()).start()

        return cls.instance

    def __init__(self):
        self.graph = tf.get_default_graph()
        self.model = None
        self.queue = Queue(maxsize=SIZE)

    def inference(self):
        while True:
            while self.queue.empty():
                time.sleep(0.001)

            id, data = self.queue.get()
            with self.graph.as_default():
                output = self.model.predict(np.array([data]))
            Thread(target=self.send, args=(output, id)).start()

    def send(self, output, id):
        client = ipc.HTTPTransceiver('192.168.1.16', 12345)
        requestor = ipc.Requestor(PROTOCOL, client)

        data = dict()
        data['input'] = output.astype(np.float32).tobytes()
        data['identifier'] = id

        requestor.request('forward', data)


def main():
    node = Node.create()

    server = ThreadedHTTPServer(('0.0.0.0', 12345), Handler)
    server.allow_reuse_address = True
    server.serve_forever()


if __name__ == '__main__':
    main()
