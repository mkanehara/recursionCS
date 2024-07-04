import socket
import os

class TcpConnection:
    def __init__(self):
        server_address = '0.0.0.0'
        server_port = 9001
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_address, server_port))

    # ファイルを開き、1400バイトずつサーバーに送る
    # 最初の32バイトはヘッダー、ファイルのバイト数を通知
    # ファイルサイズは4GB(2^32バイト)が最大
    def handle_connection(self):
        file_path = '/var/www/html/video_compressor_service/stage1/file/mov_hts-samp001.mp4'

        # ファイルタイトルの確認
        # mp4ファイルかどうかのバリデーション
        filename = os.path.basename(file_path)
        if filename[-4:] != '.mp4':
            raise Exception('File extension should be "mp4".')

        with open(file_path, 'rb') as f:
            # ファイルサイズの確認
            f.seek(0, os.SEEK_END)
            filesize = f.tell()
            f.seek(0, 0)

            if filesize > pow(2, 32):
                raise Exception('file size must be below 4GB.')
            
            # ヘッダー: ファイルサイズを32バイトで送信
            filesize_bits = filesize.to_bytes(32, "big")
            self.sock.send(filesize_bits)

            # 1400バイトに分割
            data = f.read(1400)

            while data:
                print('Sending {}'.format(data))
                self.sock.send(data)
                data = f.read(1400)

        # サーバーからの返事を待ち受ける
        receive = self.sock.recv(32)
        print(receive)

        self.sock.close()

if __name__ == "__main__":
    tcp_connection = TcpConnection()
    tcp_connection.handle_connection()
