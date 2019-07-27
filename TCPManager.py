import zmq


# CLASS for TCP communication ------------------------------------------------------------------------------------------
class TCPManager:
    context = None
    socket = None
    message = None

    def __init__(self):
        self.context = zmq.Context()

    def set_server(self, port_address_parameter):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % port_address_parameter)

    def set_message(self, message_parameter):
        self.message = message_parameter

    def receive(self):
        self.message = self.socket.recv()

    def send(self, message_parameter):
        self.socket.send(message_parameter)

    def return_message(self):
        return self.message
# ----------------------------------------------------------------------------------------------------------------------

# MAIN------------------------------------------------------------------------------------------------------------------
#tcp_manager = TCPManager()
#tcp_manager.set_server("5556")
#tcp_manager.receive()
#print "Recieved message is ", tcp_manager.return_message()
#message = 21.0
#tcp_manager.send(str(message))
# ----------------------------------------------------------------------------------------------------------------------