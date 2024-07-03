import socket
import os

class TcpConnection:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = '0.0.0.0'
        self.server_port = 9001
        self.dpath = "received_file"
        self.sock.bind((self.server_address, self.server_port))
        self.sock.listen()
        self.check_folder()
        print('Starting up on {} port {}'.format(self.server_address, self.server_port))

    def check_folder(self):
        if not os.path.exists(self.dpath):
            os.makedirs(self.dpath)
    
    def handle_connection(self):
        while True:
            connection, address = self.sock.accept()
            print('connection: {}'.format(connection))
            print('address: {}'.format(address))

            header = connection.recv(32)
            filesize = int.from_bytes(header, "big")
            filename = "port_" + str(address[-1]) + ".mp4"
            print('filesize: {}, filename: {}'.format(filesize, filename))

            with open(os.path.join(self.dpath, filename), 'wb+') as f:
                while filesize > 0:
                    data = connection.recv(filesize if filesize < 1400 else 1400)
                    f.write(data)
                    filesize = filesize - len(data)
            
            response = 'mp4 file was received!'
            connection.sendall(response.encode('utf-8'))
            break

        connection.close()


if __name__ == "__main__":
    tcp_connection = TcpConnection()
    tcp_connection.handle_connection()