import socket
import time
from threading import Thread
from stubSDK.httpServerStub import HttpStub
import json
import requests
from stubSDK.stubStatusCheck import server_check


class StubOperator:
    def __init__(self, stub_port):
        self.stub_port = stub_port
        self.server_socket = None
        self.client_addr = None

    def start_stub(self, channel_recv_timeout=2):
        """桩启动"""
        # socket服务端启动，给当前python客户端提供和桩的通信方法
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp
        server_address = ('0.0.0.0', 0)
        self.server_socket.bind(server_address)
        socket_server_port = self.server_socket.getsockname()[1]

        # 在flask app下进行socket客户端启动，以及桩启动
        t = Thread(target=HttpStub(self.stub_port, socket_server_port, channel_recv_timeout=channel_recv_timeout).server_run)
        t.start()

        server_check('stubServer')
        time.sleep(1)

    def receive(self):
        """桩消息接收"""
        data, self.client_addr = self.server_socket.recvfrom(1024)
        return json.loads(data.decode('utf-8'))

    def send(self, data):
        """桩消息返回"""
        data = json.dumps(data)
        self.server_socket.sendto(data.encode('utf-8'), self.client_addr)

    def stub_stop(self):
        """桩下线方法"""
        requests.post(url=f"http://127.0.0.1:{self.stub_port}/shutdown", timeout=30)
