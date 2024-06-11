import socket

# UNIXドメインソケットとデータグラム（非接続）ソケットを作成します
sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

# サーバーのアドレスを定義する
# サーバーはこのアドレスでメッセージを待ち受ける
server_address = '/tmp/udp_socket_file'

# クライアントが待ちうけるアドレス
address = '/tmp/udp_client_socket_file'

# サーバーに送信するメッセージ
print('Input the message to be sent')
message = input()
b_message = '{}'.format(message).encode('utf-8')

# クライアントのアドレスをバインドする
sock.bind(address)

try:
    # サーバーにメッセージを送信する
    print('Sending {!r}'.format(b_message))
    sent = sock.sendto(b_message, server_address)

    # サーバーからの応答を待ち受ける
    print('Waiting to receive')
    # 最大4096バイトのデータを受け取る
    data, server = sock.recvfrom(4096)

    # サーバーから受け取ったメッセージを表紙
    print('\nReceived {!r}'.format(data))

finally:
    print('Closing socket')
    sock.close()