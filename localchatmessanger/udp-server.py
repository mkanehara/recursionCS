import socket
import os
from faker import Faker

# socket.socket関数を使用して、新しいソケットを作成する
sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

# サーバーが接続を待ち受けるUNIXドメインソケットのパスを指定する
server_address = '/tmp/udp_socket_file'

# もし前回の実行でソケットファイルが残っていた場合、削除する
try:
    os.unlink(server_address)
except FileNotFoundError:
    pass

# ソケットが起動していることを表示する
print('starting up on {}'.format(server_address))

# ソケットを上記のアドレスにバインドする
sock.bind(server_address)

# ソケットはデータの受信を待ち続ける
while True:
    print('\nwaiting to receive message')

    # ソケットからのデータを受信する
    data, address = sock.recvfrom(4096)

    # 受信したデータとアドレスを表示する
    print('receiving {} bytes from {}\n'.format(len(data), address))
    print(data)

    if data:
        # Fakerで生成したメッセージを送り返す
        fake = Faker()
        response = fake.text()
        # バイトに変換
        b_response = '{}'.format(response).encode('utf-8')
        sent = sock.sendto(b_response, address)
        print('sent {} back to {}'.format(b_response, address))
   






