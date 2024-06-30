import socket
import threading

# TCPソケットの作成

# チャットルームの情報を格納
# チャットルーム名がkey, token, チャットルームのポート番号(port)


class TcpClient:

  def __init__(self):
    self.server_address = '127.0.0.1'
    self.server_port = 9001
    self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.chatroom_info = {}

  # roomNameSize バイトとOperationPayloadSize バイトのバイト数のバリデーション
  def input_chatroom_name(self):
    chatroom_name = input('please type in chatroom name: ')
    chatroom_name_b = chatroom_name.encode('utf-8')
    if len(chatroom_name_b) > 256:
      print('chatroom name exceeds max length. please input again')
      self.input_chatroom_name()
    
    return chatroom_name
  
  def input_username(self, chatroomname):
    username = input('please type in username: ')
    username_b = username.encode('utf-8')
    chatroomname_b = chatroomname.encode('utf-8')
    if len(username_b) + len(chatroomname_b) > 2**29:
      print('username exceeds max length. please input again')
      self.input_username(chatroomname)
    
    return username

  def start(self):
    ### チャットルームの作成依頼 ###
    chatroom_name = self.input_chatroom_name()
    username = self.input_username(chatroom_name)

    # ヘッダー、ペイロード情報の作成
    b_chatroom_name = chatroom_name.encode('utf-8')
    operation_code_i = input('Please input operation_code: ')
    operation_code = int(operation_code_i)
    b_operation_code = operation_code.to_bytes(1, "big")
    state_code = 0
    b_state_code = state_code.to_bytes(1, "big")
    b_username = username.encode('utf-8')
    roomname_size = len(b_chatroom_name).to_bytes(1, "big")
    operation_payload_size = len(b_username).to_bytes(29, "big")

    header = roomname_size + b_operation_code + b_state_code + operation_payload_size
    body = b_chatroom_name + b_username

    try:
      # サーバーにリクエストを送信
      self.tcp_sock.connect((self.server_address, self.server_port))
      self.tcp_sock.send(header + body)

      # 1回目のサーバーからヘッダーを受信
      header = self.tcp_sock.recv(32)
      roomname_size = header[0]
      operation_code = header[1]
      state_code = header[2]
      operation_payload_size = int.from_bytes(header[3:32], "big")
      print("Response1 from server:", roomname_size, operation_code, state_code, operation_payload_size)

      # 応答ペイロードを受信
      port = self.tcp_sock.recv(operation_payload_size)
      print("Payload1 from server port:", port)

      # 2回目のサーバーからの応答を受信
      header = self.tcp_sock.recv(32)
      roomname_size = header[0]
      operation_code = header[1]
      state_code = header[2]
      operation_payload_size = int.from_bytes(header[3:32], "big")
      print("Response2 from server:", roomname_size, operation_code, state_code, operation_payload_size)

      # 応答ペイロードを受信
      token = self.tcp_sock.recv(operation_payload_size).decode('utf-8')
      print("Payload2 from server token:", token)

      # chatroom_infoに情報を格納
      chatroom_info = {
        "chatroomname": chatroom_name,
        "token": token,
        "port": port
      }

      return chatroom_info

    finally:
      print("closing socket")
      self.tcp_sock.close()

class UdpClient:
  def __init__(self, server_address, chatroomnname, server_port, token):
    self.server_port = server_port
    self.server_address = server_address
    self.token = token
    self.chatroomname = chatroomnname
    self.running = True

  def protocol_header(self):
    # header: RoomNameSize（1 バイト）| TokenSize（1 バイト）
    # body: 最初の RoomNameSize バイトはルーム名、次の TokenSize バイトはトークン文字列、そしてその残りが実際のメッセージ
    chatroomname_b = self.chatroomname.encode('utf-8')
    print(chatroomname_b)
    roomnamesize = len(self.chatroomname).to_bytes(1, "big")
    print(roomnamesize)
    token_b = self.token.encode('utf-8')
    print(token_b)
    tokensize = len(token_b).to_bytes(1, "big")
    print(tokensize)
    
    return roomnamesize + tokensize + chatroomname_b + token_b

  def send_message(self):
    # UDPコネクションの作成
    self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.udp_sock.bind(('0.0.0.0', 0))

    while self.running:
      try:
        message = input('please input message to be sent: ')
        message_b = message.encode('utf-8')
        print('sending {!r}'.format(message_b))
        header_body = self.protocol_header() + message_b
        if len(message_b) > 4096:
          print('message body exceeds 4094 bytes.')
          self.send_message()

        # サーバへのデータ送信
        sent = self.udp_sock.sendto(header_body, (self.server_address, int(self.server_port)))
        print('Send {} bytes'.format(sent))
      except Exception as e:
        print(e)

  def receive_message(self):
    while self.running:
      try:
        # 応答を受信
        data, server = self.udp_sock.recvfrom(4096)
        data_str = data.decode('utf-8')
        print('received {!r}'.format(data_str))
        if "#### socket was closed. ####" in data_str:
          self.stop()
      except Exception as e:
        print(e)
  
  def start(self):
    send_thread = threading.Thread(target=self.send_message)
    receive_thread = threading.Thread(target=self.receive_message)

    send_thread.start()
    receive_thread.start()
    send_thread.join()
    receive_thread.join()
  
  def stop(self):
    self.running = False
    self.udp_sock.sendto(b'', (self.server_address, int(self.server_port)))
    self.udp_sock.close()

if __name__ == "__main__":
  tcpclient = TcpClient()
  chatroom_info = tcpclient.start()

  if chatroom_info:
    udpclient = UdpClient('127.0.0.1', chatroom_info["chatroomname"], chatroom_info["port"], chatroom_info["token"])
    udpclient.start()
  else:
    print('Falied to obtain chatroom information')
