import socket
import uuid
import threading
import time

# トークン毎のユーザのリスト
# {"chatroomname":
    #    "token1": {
    #                "address": XXX,
    #                "username": YYY,
    #                "host_flag": 0 or 1,
    #                "last_chat_time": YYYY_MM_DD hh:mm:ss
    #              },
    #    "token2": {
    #                "address": XXX,
    #                "username": YYY,
    #                "host_flag": 0 or 1,
    #                "last_chat_time": YYYY_MM_DD hh:mm:ss
#              }
# }

# チャットルームごとの情報のリスト
# chatroom_list[roomname] = {"port": 12345, "hosttoken": "dfghbry-fgbnmu"}
chatroom_list = {}

# チャットルームを管理するクラス
class TcpConnection:

    # TCP接続用のsocketを作成する。チャットルームの作成などが終わったら、閉じる。
    def __init__(self, user_list):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_address = '0.0.0.0'
        self.port = 9001
        self.user_list = user_list
        print('Starting up on {} port {}'.format(self.server_address, self.port))

    def bind(self):
        self.sock.bind((self.server_address, self.port))

    def listen(self):
        self.sock.listen(5)

    def start(self):
        self.bind()
        self.listen()
        while True:
            connection, address = self.sock.accept()
            client_thread = threading.Thread(target=self.handle_clients, args=(connection, address))
            client_thread.start()

    def get_header_body(self, connection):
        header = connection.recv(32)
        # 長さはヘッダーから取り出される
        roomname_size = header[0]
        operation_code = header[1]
        state_code = header[2]
        operation_payload_size = int.from_bytes(header[3:], "big")
        # ルーム名の取り出し
        roomname = connection.recv(roomname_size).decode('utf-8')
        # operation_payload（username）の呼び出し
        username = connection.recv(operation_payload_size).decode('utf-8')

        result = {
            "roomname_size": roomname_size,
            "operation_code": operation_code,
            "state_code": state_code,
            "roomname": roomname,
            "username": username
        }
        return result

    def comply_response(self, header_body, connection, address, operation_code, chatroomname):
        ###　まずはstate_code=1の準拠 ###
        state_code = 1
        # サーバー用チャットルームポートの設定
        chatroom_port = 9002
        # state_code=1と、チャットルームのポート番号を渡す
        response_payload = str(chatroom_port).encode('utf-8')
        operation_payload_size = len(response_payload)
        response_header = header_body["roomname_size"].to_bytes(1, "big") + header_body["operation_code"].to_bytes(1, "big") + state_code.to_bytes(1, "big") + operation_payload_size.to_bytes(29, "big")
        connection.sendall(response_header + response_payload)
        print('state_code:1 -> successfullly sent')

        ### state_code=2としてトークンを生成し、クライアントに渡す ###
        state_code = 2
        token = str(uuid.uuid4())
        response_payload = token.encode('utf-8')
        operation_payload_size = len(response_payload)
        response_header = header_body["roomname_size"].to_bytes(1, "big") + header_body["operation_code"].to_bytes(1, "big") + state_code.to_bytes(1, "big") + operation_payload_size.to_bytes(29, "big")
        connection.sendall(response_header + response_payload)
        print('state_code:2 -> successfullly sent')

        if chatroomname not in self.user_list:
            self.user_list[chatroomname] = {}

        # user_listにクライアントを追加
        host_flag = 1
        if operation_code == 2:
            host_flag = 0
        self.user_list[chatroomname][token] = {
                "address": address,
                "username": header_body["username"],
                "host_flag": host_flag,
                "last_chat_time": time.time()
            }
        print(self.user_list[chatroomname])

        # TCPコネクションクローズ
        connection.close()

        # ホストトークンとルームのポート番号をreturn
        return token, chatroom_port


    def handle_clients(self, connection, address):
        try:
            print('connecting from {}'.format(address))
            
            header_body = self.get_header_body(connection)
            print(header_body)

            # 操作コードによって、サーバーの挙動を変更する
            # チャットルームの作成
            if header_body["operation_code"] == 1:
                if header_body["state_code"] == 0:

                    # 認証を行い、トークンとルームのポート番号をクライアントに返却。この時にトークンリストにクライアントを追加。
                    token, chatroom_port = self.comply_response(header_body, connection, address, header_body["operation_code"], header_body["roomname"])

                    print(token, chatroom_port)
                    # 接続
                    udp_chat = UdpChat(self.user_list)
                    udp_chat.create_udp_socket(header_body["roomname"], chatroom_port, token)
                    udp_thread = threading.Thread(target=udp_chat.handle_chatroom)
                    udp_thread.start()

            elif header_body["operation_code"] == 2:
                # チャットルームに参加
                if header_body["state_code"] == 0:
                    # 認証を行い、トークンとルームのポート番号をクライアントに返却。この時にトークンリストにクライアントを追加。
                    token, chatroom_port = self.comply_response(header_body, connection, address, header_body["operation_code"], header_body["roomname"])

            else:
                raise Exception('Operation code is invalid.')

        except Exception as e:
            print(e)

        finally:
            # TCPコネクションクローズ
            print('connection close')
            connection.close()

class UdpChat:
    def __init__(self, user_list):
        self.user_list = user_list
        self.running = True

    def create_udp_socket(self, roomname, latest_chatroom_port, hosttoken):
        # UDPソケットコネクションの作成とリッスンまで
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.chatroom_address = '0.0.0.0'
        self.chatroom_port = latest_chatroom_port
        self.roomname = roomname
        self.hosttoken = hosttoken
        print('stating up chatroom {} on {}'.format(self.chatroom_address, self.chatroom_port))
        self.sock.bind((self.chatroom_address, self.chatroom_port))
        chatroom_list[self.roomname] = {"port": self.chatroom_port, "hosttoken": self.hosttoken}

    def handle_chatroom(self):
        # ホストがトークンリストに存在するまで、while Trueでメッセージを受け続ける
        try:
            while self.running:
                data, address = self.sock.recvfrom(4096)
                print('sent {} bytes back to {}'.format(data, address))

                # dataの中からroomnamebitesize, tokensizeを取り出し、それをもとに実際のデータを取り出す
                roomnamebite_size = int.from_bytes(data[:1],"big")
                tokensize = int.from_bytes(data[1:2],"big")
                roomname = data[2:2+roomnamebite_size].decode('utf-8')
                current_token = data[2+roomnamebite_size:2+roomnamebite_size+tokensize].decode('utf-8')
                message = data[2+roomnamebite_size+tokensize:]
                print('roomname: {}, token: {}'.format(roomname, current_token))
                # user_listのアドレスをtcpのものからudpのものに更新
                self.user_list[roomname][current_token]["address"] = address
                # 最終メッセージ時刻を更新
                self.user_list[roomname][current_token]["last_chat_time"] = time.time()
                print(self.user_list)

                # user_listを更新（一定時間接続していないユーザーの削除）
                deleted_user_addresses = self.delete_client(roomname)
                print(deleted_user_addresses)

                if len(deleted_user_addresses) > 0:
                    message = "logout due to time out"
                    message_b = message.encode('utf-8')
                    for address in deleted_user_addresses:
                        self.sock.sendto(message_b, address)

                # ホストがいるかを識別
                hosttoken = chatroom_list[self.roomname]["hosttoken"]
                print('hosttoken: {}'.format(hosttoken))
                print(self.user_list[roomname])
                if hosttoken in self.user_list[roomname]:
                    for client_token, value in self.user_list[roomname].items():
                        if current_token != client_token:
                            client_address = self.user_list[roomname][client_token]["address"]
                            self.sock.sendto(str(message).encode('utf-8'), client_address)
                else:
                    message = 'chatroom host was logged out. #### socket was closed. ####'
                    message_b = message.encode('utf-8')
                    self.sock.sendto(message_b, self.user_list[roomname][current_token]["address"])
                    del chatroom_list[self.roomname]
                    del self.user_list[roomname]
                    self.stop()

        except Exception as e:
                print(f'Error handling UDP message: {e}')
        
        finally:
            self.sock.close()  # ソケットを閉じる
            print('UDP socket closed.')
    
    def stop(self):
        self.running = False  # ループを停止する
        self.sock.sendto(b'', (self.chatroom_address, self.chatroom_port))
    
    def delete_client(self, roomname):
        deleted_user_addresses = []
        current_time = time.time()

        tokens_to_delete = [client_token for client_token in self.user_list[roomname] if current_time - self.user_list[roomname][client_token]["last_chat_time"] > 120]

        for client_token in tokens_to_delete:
            deleted_user_addresses.append(self.user_list[roomname][client_token]["address"])
            del self.user_list[roomname][client_token]
        
        return deleted_user_addresses

                    
if __name__  == "__main__":
    user_list = {}
    tcpserver = TcpConnection(user_list)
    tcpserver.start()
