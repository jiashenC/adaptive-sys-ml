import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import avro.ipc as ipc
import avro.protocol as protocol
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

# read data packet format.
PROTOCOL = protocol.parse(open(DIR_PATH + '/resource/message/message.avpr').read())


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
        stats = Stats.create()
        try:
            id = int(req['identifier'])
            stats.incoming_frame(id)
            return False
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


class Stats:
    instance = None

    @classmethod
    def create(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    def __init__(self):
        self.start_time = 0.0
        self.data_log = {i: 0 for i in range(100)}
        self.frame_count = 0

    def incoming_frame(self, id):
        if self.start_time == 0.0:
            self.start_time = time.time()
        self.data_log[id] += 1
        self.frame_count += 1
        self.log()

    def log(self):
        print 'coverage:{:.3f} %, frame rate:{:.3f} f/s'.format(sum(self.data_log.values()) * 1.0,
                                                              self.frame_count / (time.time() - self.start_time))


def main():
    server = ThreadedHTTPServer(('0.0.0.0', 12345), Handler)
    server.allow_reuse_address = True
    server.serve_forever()


if __name__ == '__main__':
    main()
