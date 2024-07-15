import socket
import json
import os
import re

class TcpConnection:

    def __init__(self):
        self.server_address = '0.0.0.0'
        self.server_port = 9001
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stream_rate = 1024
    
    def show_options(self):
        options = {
            "1": "動画の圧縮",
            "2": "動画の解像度変更",
            "3": "動画のアスペクト比変更",
            "4": "動画の音声変換",
            "5": "動画のGIF変換"
        }
        print('次の中から処理方法を選択してください')
        for key, value in options.items():
            print(f'{key}: {value}')
        option_flag = True
        choice = ''
        while option_flag:
            choice = input('選択肢の番号を入力してください。')
            if choice in options:
                option_flag = False
            else:
                print('無効な選択肢です。再度入力してください')
        return choice

    def input_variable(self, regex, input_txt):
        invalid_variable = True
        while invalid_variable:
            variable = input(f'{input_txt}')
            if re.fullmatch(regex, variable):
                invalid_variable = False
            else:
                print('無効な入力値です。再度入力してください。')
        return variable

    def create_json(self):
        option = self.show_options()
        dic = {
            "type": "",
            "variables": []
        }
        if option == "1":
            dic["type"] = "compression"
        elif option == "2":
            dic["type"] = "resolution_change"
            scale = self.input_variable(r'[1-9]\d*', '横幅スケールを自然数で入力してください')
            dic["variables"].append(scale)
        elif option == "3":
            dic["type"] = "aspect_change"
            aspect_ratio = self.input_variable(r'\d+/\d+', '希望するアスペクト比を半角分数で入力してください')
            dic["variables"].append(aspect_ratio)
        elif option == "4":
            dic["type"] = "video_to_mp3_change"
        elif option == "5":
            dic["type"] = "video_to_gif_change"
            cut_start_seconds = self.input_variable(r'\d\d:\d\d:\d\d', 'カットオフしたい時間を、hh:mm:ss単位で入力してください')
            gif_time_duratopn = self.input_variable(r'[1-9]\d*', 'GIFの再生時間を自然数で入力してください')
            flame_rate = self.input_variable(r'[1-9]\d*', 'フレームレートを自然数で入力してください')
            scale = self.input_variable(r'[1-9]\d*', '横幅スケールを自然数で入力してください')
            dic["variables"].extend([cut_start_seconds, gif_time_duratopn, flame_rate, scale])
        print(dic)
        return json.dumps(dic, ensure_ascii=False)
    
    def ask_mediatype(self):
        mediatype = input('mediatypeを入力してください')
        return mediatype
    
    def upload_file(self):
        basepath = '/var/www/html/video_compressor_service/stage2/inputfile/'
        filename = input('uploadしたファイル名を記入してください')
        print(basepath + filename)
        return basepath + filename

    def handle_connection(self):
        self.sock.connect((self.server_address, self.server_port))
        json_s = self.create_json()
        json_b = json_s.encode('utf-8')
        json_size = len(json_b).to_bytes(2, "big")

        mediatype = self.ask_mediatype()
        mediatype_b = mediatype.encode('utf-8')
        mediatype_size = len(mediatype_b).to_bytes(1, "big")

        filepath = self.upload_file()

        with open(filepath, 'rb') as f:
            f.seek(0, os.SEEK_END)
            filesize = f.tell()
            f.seek(0,0)

            filesize_b = filesize.to_bytes(5, "big")

            header = json_size + mediatype_size + filesize_b
            print(header)

            self.sock.send(header)
            self.sock.send(json_b)
            self.sock.send(mediatype_b)

            data = f.read(1400)
            while data:
                print('Sending {}'.format(data))
                self.sock.send(data)
                data = f.read(1400)

        # サーバーからの返事を待ち受ける
        test_b = "test".encode('utf-8')
        self.sock.send(test_b)
        receive_header = self.sock.recv(8)
        receive_json_size = int.from_bytes(receive_header[:2], 'big')
        receive_mediatype_size = int.from_bytes(receive_header[2:3], "big")
        receive_payload_size = int.from_bytes(receive_header[3:], "big")
        print('Received header from server. Byte lengths: json length {}, mediatype length {}, data Length {}'.format(receive_json_size, receive_mediatype_size, receive_payload_size))

        # jsonの保存
        json_b = self.sock.recv(receive_json_size)
        # mediatypeの保存
        mediatype_b = self.sock.recv(receive_mediatype_size)
        mediatype = mediatype_b.decode('utf-8')

        # payloadの読み込み
        filename = f'result.{mediatype}'
        with open(os.path.join('/var/www/html/video_compressor_service/stage2/client_outputfile/', filename), 'wb+') as f:
            while receive_payload_size:
                data = self.sock.recv(receive_payload_size if receive_payload_size <= self.stream_rate else self.stream_rate)
                f.write(data)
                receive_payload_size -= len(data)
        print('Finished downloading the file from server.')

if __name__ == '__main__':
    tcp_connection = TcpConnection()
    tcp_connection.handle_connection()

