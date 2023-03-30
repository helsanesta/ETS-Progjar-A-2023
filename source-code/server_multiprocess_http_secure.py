import os
import socket
import threading
import time
import sys
import logging
import ssl
from multiprocessing import Process

from http import HttpServer

httpserver = HttpServer()


class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		rcv=""
		while True:
			try:
				data = self.connection.recv(32)
				if data:
					#merubah input dari socket (berupa bytes) ke dalam string
					#agar bisa mendeteksi \r\n
					d = data.decode()
					rcv=rcv+d
					if rcv[-2:]=='\r\n':
						#end of command, proses string
						logging.warning("data dari client: {}" . format(rcv))
						hasil = httpserver.proses(rcv)
						#hasil akan berupa bytes
						#untuk bisa ditambahi dengan string, maka string harus di encode
						hasil=hasil+"\r\n\r\n".encode()
						logging.warning("balas ke  client: {}" . format(hasil))
						#hasil sudah dalam bentuk bytes
						self.connection.sendall(hasil)
						rcv=""
						self.connection.close()
				else:
					break
			except OSError as e:
				pass
		self.connection.close()


class Server:
	def __init__(self, hostname='testing.net'):
		self.hostname = hostname

	def serve(self):
		context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
		cert_location = os.getcwd() + '/certs/'
		context.load_cert_chain(certfile=cert_location + 'domain.crt',
									 keyfile=cert_location + 'domain.key')

		my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		my_socket.bind(('0.0.0.0', 8443))
		my_socket.listen(200)
		while True:
			connection, client_address = my_socket.accept()
			try:
				secure_connection = context.wrap_socket(connection, server_side=True)
				logging.warning("connection from {}".format(client_address))
				clt = ProcessTheClient(secure_connection, client_address)
				clt.start()
			except ssl.SSLError as essl:
				print(str(essl))


def main():
	servers = [Server() for _ in range(4)]
	processes = [Process(target=srv.serve) for srv in servers]
	for process in processes:
		process.start()
	for process in processes:
		process.join()


if __name__ == '__main__':
	main()
