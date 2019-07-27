# coding=utf-8

import sys
import zmq

# communicator의 ip and port
server_ip = "tcp://127.0.0.1:%s"
port = "5556"

if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(server_ip % port)

    # sys.argv[1] 시간
    # sys.argv[2] 전시홀 에뮬레이션 결과
    bcvtb_message = sys.argv[1] + "|" + sys.argv[2]
    socket.send(bcvtb_message)
    del bcvtb_message
    message = socket.recv()
    # socket.close()
    print message

