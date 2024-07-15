# 【FFMPEGクラス】
"""
# 動画の圧縮 ffmpeg -i input.mp4 -preset medium -crf 30 output.mp4
# 動画の解像度を変更 ffmpeg -i in.mp4 -vf scale=1280:-1 out.mp4
# 動画のアスペクト比を変更する ffmpeg -i input.mp4 -vf "scale=ih*4/3:ih,pad=w=ih*4/3:h=ih:x=(ow-iw)/2:y=(oh-ih)/2" output.mp4
# 動画を音声に変換する ffmpeg -i input.mp4 -q:a 0 output.mp3
# 動画を指定した時間範囲でGIFFに変更する ffmpeg -i input.mp4 -ss 00:00:05 -t 10 -vf "fps=10,scale=320:-1:flags=lanczos" -gifflags -transdiff output.gif

# ffmpeg.resolution_change('mov_hts-samp001.mp4', 'mov_hts-samp001.mp4', 1280)
# ffmpeg.compression('mov_hts-samp001.mp4', 'mov_hts-samp001.mp4')
# ffmpeg.video_to_mp3_change('free-video1-sea-cafinet.mp4', 'free-video1-sea-cafinet.mp3')
# ffmpeg.video_to_gif_change('free-video1-sea-cafinet.mp4', 'free-video1-sea-cafinet.gif', '00:00:05', 10, 10, 320)
"""

# 【JSON】
"""
# JSONファイルに、動画の圧縮・解像度の変更・アスペクト比の変更・オーディオに変換・GIFの作成のtypeをvalueに入れる
# 上記それぞれの場合に、追加の質問事項があれば、それをkey: valueにしてJSONに入れ込む
json = {
    type: compression, resolution_change, aspect_change, video_to_mp3_change, video_to_gif_change
}
"""

# 【TCP】

import subprocess
import os
import time
import socket
import json
import threading

class Ffmpeg:

    def __init__(self):
        self.outputbasepath = '/var/www/html/video_compressor_service/stage2/outputfile/'
        self.inputbasepath = '/var/www/html/video_compressor_service/stage2/inputfile/'

    def cleanup_video(self, outputfile, basepath):
        print(f"Trying to delete {outputfile}...")
        outputfilepath = basepath + outputfile
        if os.path.exists(outputfilepath):
            os.remove(outputfilepath)
            while os.path.exists(outputfilepath):
                time.sleep(0.1)  # 短い待機時間で再チェック
            if not os.path.exists(outputfile):
                print(f"{outputfile} は正常に削除されました。")
            else:
                print(f"{outputfile} の削除に失敗しました。")
        else:
            print(f"{outputfile} は存在しません。")

    def create_error_json(self, status_code, error_message, solution, connection):
        response = {
            "status_code": status_code,
            "error_message": error_message,
            "solution": solution
        }
        response_json = json.dumps(response)
        size = 0
        response_json_b = response_json.encode('utf-8')
        response_json_size = len(response_json_b).to_bytes(2, "big")
        mediatype_size = size.to_bytes(1, "big")
        payload_size = size.to_bytes(5, "big")
        header = response_json_size + mediatype_size + payload_size
        connection.send(header)
        connection.send(response_json_b)
        return response_json

    def create_success_json(self, status_code, success_message):
        response = {
            "status_code": status_code,
            "error_message": success_message,
        }
        response_json = json.dumps(response)
        return response_json
    
    def compression(self, inputfile, outputfile, connection):
        self.cleanup_video(outputfile, self.outputbasepath)
        
        inputfilepath = self.inputbasepath + inputfile
        outputfilepath = self.outputbasepath + outputfile

        command = ['ffmpeg','-i',inputfilepath,'-preset','medium','-crf', '30', outputfilepath]
        
        try:
            subprocess.run(command, check=True)
            print('video compresson was completed.')
            json_d = self.create_success_json("success", "compression was succeeded.")
        except subprocess.CalledProcessError as e:
            print('Error occured during compression: {}'.format(e))
            json_d = self.create_error_json("COMPRESSION ERROR", e, "Check input file", connection)
        return json_d

    def resolution_change(self, inputfile, outputfile, width_scale, connection):
        self.cleanup_video(outputfile, self.outputbasepath)

        inputfilepath = self.inputbasepath + inputfile
        outputfilepath = self.outputbasepath + outputfile

        scale = f"scale={width_scale}:ceil(ow/a/2)*2"

        command = ['ffmpeg', '-i', inputfilepath, '-vf', scale, outputfilepath]
        try:
            subprocess.run(command, check=True)
            print('video resolution_change was completed.')
            json_d = self.create_success_json("success", "video resolution_change was succeeded.")
        except subprocess.CalledProcessError as e:
            print('Error occured during resolution_change: {}'.format(e.stderr))
            json_d = self.create_error_json("RESOLUTION CHANGE ERROR", e, "Check input file and scale", connection)
        return json_d

    def aspect_change(self, inputfile, outputfile, aspect_ratio, connection):
        self.cleanup_video(outputfile, self.outputbasepath)

        inputfilepath = self.inputbasepath + inputfile
        outputfilepath = self.outputbasepath + outputfile

        scale = f"scale=ih*{str(aspect_ratio)}:ih,pad=w=ih*{str(aspect_ratio)}:h=ih:x=(ow-iw)/2:y=(oh-ih)/2"

        command = ['ffmpeg', '-i', inputfilepath, '-vf', scale, outputfilepath]
        try:
            subprocess.run(command, check=True)
            print('video aspect_change was completed.')
            json_d = self.create_success_json("success", "video aspect_change was succeeded.")
        except subprocess.CalledProcessError as e:
            print('Error occured during aspect_change: {e}')
            json_d = self.create_error_json("ASPECT CHANGE ERROR", e, "Check input file and scale", connection)
        return json_d

    def video_to_mp3_change(self, inputfile, outputfile, connection):
        self.cleanup_video(outputfile, self.outputbasepath)

        inputfilepath = self.inputbasepath + inputfile
        outputfilepath = self.outputbasepath + outputfile
        # outputfilepathの拡張子がmp3である必要あり

        command = ['ffmpeg', '-i', inputfilepath, outputfilepath]
        try:
            subprocess.run(command, check=True)
            print('video_to_mp3_change was completed.')
            json_d = self.create_success_json("success", "video_to_mp3_change was succeeded.")
        except subprocess.CalledProcessError as e:
            print('Error occured during video_to_mp3_change: {}'.format(e))
            json_d = self.create_error_json("ERROR ERROR", e, "Check input file and scale", connection)
        return json_d

    def video_to_gif_change(self, inputfile, outputfile, cut_start_seconds, gif_time_duration, flame_rate, scale, connection):
        self.cleanup_video(outputfile, self.outputbasepath)

        inputfilepath = self.inputbasepath + inputfile
        outputfilepath = self.outputbasepath + outputfile

        # format of cut_start_seconds: 00:00:05
        video_filter_option = f"fps={str(flame_rate)},scale={str(scale)}:ceil(ow/a/2)*2:flags=lanczos"

        command = ['ffmpeg', '-i', inputfilepath, '-ss', cut_start_seconds, '-t', str(gif_time_duration), '-vf', video_filter_option, '-gifflags', '-transdiff', outputfilepath]
        try:
            subprocess.run(command, check=True)
            print('video_to_gif_change was completed.')
            json_d = self.create_success_json("success", "video_to_gif_change was succeeded.")
        except subprocess.CalledProcessError as e:
            print('Error occured during video_to_gif_change: {}'.format(e))
            json_d = self.create_error_json("ASPECT CHANGE ERROR", e, "Check input file and scale", connection)
        return json_d

class TcpConnection:

    def __init__(self, server_address, server_port):
        self.dpath = '/var/www/html/video_compressor_service/stage2/inputfile/'
        self.stream_rate = 4096
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((server_address, server_port))
        self.sock.listen(1)

    def handle_connection(self, ffmpeg):
        while True:
            connection, client_address = self.sock.accept()
            try:
                print('connecting from {} ...'.format(client_address))
                # ヘッダーは８バイト
                # JSONサイズ（2バイト）、メディアタイプサイズ（1バイト）、ペイロードサイズ（5 バイト）
                header = connection.recv(8)
                json_size = int.from_bytes(header[:2], 'big')
                mediatype_size = int.from_bytes(header[2:3], "big")
                payload_size = int.from_bytes(header[3:], "big")

                print('Received header from client. Byte lengths: json length {}, mediatype length {}, data Length {}'.format(json_size, mediatype_size, payload_size))

                # jsonの保存
                json_b = connection.recv(json_size)
                print(json_b)

                # mediatypeの読み取り
                mediatype_b = connection.recv(mediatype_size)
                mediatype = mediatype_b.decode('utf-8')
                print(mediatype_b)

                # bodyの読み取り
                filename = f'{client_address[1]}.{mediatype}'
                with open(os.path.join(self.dpath, filename), '+wb') as f:
                    while payload_size > 0:
                        data = connection.recv(payload_size if payload_size <= self.stream_rate else self.stream_rate)
                        f.write(data)
                        payload_size -= len(data)
                    print('Finished downloading the file from client.')

                # jsonファイルの読み込み
                json_t = json_b.decode('utf-8')
                json_j = json.loads(json_t)

                # 関数名, 変数名の読み込み 
                function_name = json_j["type"]
                print("function_name:", function_name)

                outputfile = ""
                outputjson_d = {}
                outputmediatype = mediatype
                if function_name == "compression":
                    outputfile = filename
                    outputjson_d = ffmpeg.compression(filename, outputfile, connection)
                elif function_name == "resolution_change":
                    outputfile = filename
                    outputjson_d = ffmpeg.resolution_change(filename, outputfile, json_j["variables"][0], connection)
                elif function_name == "aspect_change":
                    outputfile = filename
                    outputjson_d = ffmpeg.aspect_change(filename, outputfile, json_j["variables"][0], connection)
                elif function_name == "video_to_mp3_change":
                    outputfile = f'{client_address[1]}.mp3'
                    outputjson_d = ffmpeg.video_to_mp3_change(filename, outputfile, connection)
                    outputmediatype = 'mp3'
                elif function_name == "video_to_gif_change":
                    outputfile = f'{client_address[1]}.gif'
                    outputjson_d = ffmpeg.video_to_gif_change(filename, outputfile, json_j["variables"][0], json_j["variables"][1], json_j["variables"][2], json_j["variables"][3], connection)
                    outputmediatype = 'gif'

                # クライアントにデータを送信
                outputjson_b = json.dumps(outputjson_d, ensure_ascii=False).encode('utf-8')
                outputjson_size = len(outputjson_b).to_bytes(2, "big")
                outputmediatype_b = outputmediatype.encode('utf-8')
                outputmediatype_size = len(outputmediatype_b).to_bytes(1, "big")

                filepath = f'/var/www/html/video_compressor_service/stage2/outputfile/{outputfile}'
                with open(filepath, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    filesize = f.tell()
                    f.seek(0,0)

                    outputfilesize_b = filesize.to_bytes(5, "big")

                    header = outputjson_size + outputmediatype_size + outputfilesize_b
                    print(header)
                    connection.send(header)
                    connection.send(outputjson_b)
                    connection.send(outputmediatype_b)

                    data = f.read(1400)
                    while data:
                        print('Sending {}'.format(data))
                        connection.send(data)
                        data = f.read(1400)
                    
                ffmpeg.cleanup_video(outputfile, ffmpeg.outputbasepath)
                ffmpeg.cleanup_video(outputfile, ffmpeg.inputbasepath)

            except Exception as e:
                print('Error: {}'.format(str(e)))
                ffmpeg.create_error_json("ERROR ERROR", e, "Check input file", connection)

            finally:
                print('closing current connection...')
                connection.close()

if __name__ == "__main__":
    ffmpeg = Ffmpeg()
    tcp_connection = TcpConnection('0.0.0.0', 9001)
    tcp_connection.handle_connection(ffmpeg)
