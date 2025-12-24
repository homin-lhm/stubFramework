import time

from flask import Flask, request, jsonify
from waitress import serve
import socket
import json
import os
import signal
from stubSDK.stubStatusCheck import serverStartStatus


class HttpStub:
    def __init__(self, stub_port, socket_server_port, channel_recv_timeout):
        self.stub_port = stub_port
        self.client_socket = None
        self.socket_server_port = socket_server_port
        self.channel_recv_timeout = channel_recv_timeout
        self.app = Flask(__name__)
        self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])(self.common_route)

    def socket_client(self):
        """create socket channel client"""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 套接字：1  ==》 udp传输协议

    def common_route(self, path):
        """桩通用性路由处理逻辑"""
        self.client_socket.settimeout(None)

        # 实现桩服务下线方法
        if path == 'shutdown':
            os.kill(os.getpid(), signal.SIGINT)
            return 'Server shutting down...', 200

        # 打包被测服务请求三方服务（桩）的协议
        msg = {
            'path': '/' + path,
            'method': request.method,
            'headers': dict(request.headers),
            'cookies': dict(request.cookies),
            'params': dict(request.args) or None,
            'data': request.data.decode('utf-8') or None
        }
        server_address = ('127.0.0.1', int(self.socket_server_port))
        self.client_socket.sendto(json.dumps(msg).encode('utf-8'), server_address)
        try:
            self.client_socket.settimeout(self.channel_recv_timeout)
            data = self.client_socket.recv(1024).decode('utf-8')
        except TimeoutError:
            return {'msg': 'stub recv data timeout!'}, 500
        recv_data = json.loads(data)
        if 'timeout' in recv_data.keys():
            time.sleep(recv_data['timeout'])
        response = recv_data['response']
        response_code = recv_data['status_code']
        return jsonify(response), response_code

    def server_run(self):
        self.socket_client()
        self.app.debug = True
        serverStartStatus.add('stubServer')
        serve(self.app, host='0.0.0.0', port=self.stub_port, threads=10)

