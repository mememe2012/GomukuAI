"""
通过python构建一个免费，单机，无服务器，不限流量的内网映射和局域网组队技术
"""
import os
import socket
import threading
import time
from typing import Literal

class Frp:
    def __init__(self, server_port:int=7000, server_host:str="127.0.0.1", protocol:Literal["TCP", "UDP"]="UDP"):
        self.server_port = server_port
        self.server_host = server_host
        self.protocol = protocol
        self.running = False
        self.client_sockets = []
        self.server_socket = None
        self.server_thread = None
        self.client_threads = []
    def start_server(self):
        pass