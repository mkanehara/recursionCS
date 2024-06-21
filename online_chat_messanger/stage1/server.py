import socket
import os
from pathlib import Path
import time

# 送られてきたソケットから、usernameとmessageを返します
# データの最初の１バイトである、usernamelenを取り出し、そこからusernameとmessageを返します
def process_message(data):
    username_length = int.from_bytes(data[:1], "big") + 1
    username = data[1:username_length]
    message = data[username_length:]
    return username, message

# ソケットオブジェクトの作成（IPv4アドレスファミリ, UDPソケット）
# 任意のアドレスからの受付を受け入れる
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001

# clientの辞書を初期化します
clients = {}
# 送信失敗の回数をカウントする辞書
failure_counts = {}
max_failuer_counts = 3

print('Starting up on {} port {}'.format(server_address, server_port))

# バインドする
sock.bind((server_address, server_port))

while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)
    print('received {} bytes data from {}'.format(len(data), address))

    username, message = process_message(data)

    # アドレスとusername, 最終接続時間を辞書に格納
    clients[address] = (username, time.time())
    # 失敗カウントの辞書に登録
    failure_counts.setdefault(address, 0)

    # アドレス長に登録されているクライアントに、メッセージをリレーする。
    # この時、送信元にはリレーしない
    for client_address in clients:
        if client_address != address:
            relay_message = f'{username}: {message}'.encode('utf-8')
            try:
                sock.sendto(relay_message, client_address)
                print(f'Sent message to {client_address}')
                failure_counts[client_address] = 0
            except Exception as e:
                print(f'Failed to send message to {client_address}: {e}')
                failure_counts[client_address] += 1
                if failure_counts[client_address] >= max_failuer_counts:
                    print('Removed client due to repeated error')
                    del clients[client_address]
                    del failure_counts[client_address]
                
    
    # 120秒アクセスがなかった場合はclients辞書から削除
    currenttime = time.time()
    inactive_clients = [addr for addr, (username, last_msg_time) in clients.items() if currenttime - last_msg_time > 120]
    for addr in inactive_clients:
        del clients[addr]
        print(f'deleted {addr}')







