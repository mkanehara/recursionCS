import socket

# serverに送るメッセージをかえす関数
def protocol_message(username, message_bits):
    username_bytes = username.encode('utf-8')
    usernamelen = len(username_bytes)
    if usernamelen > 255:
        raise ValueError('username is too long')
    username_length = usernamelen.to_bytes(1, "big")
    return username_length + username_bytes + message_bits

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = '192.168.33.10'
server_port = 9001

address = ''
port = 9050
# 空の文字列も0.0.0.0として使用できる
sock.bind((address, port))

username = input("Type in the username: ")

# message = input("Type in the message to send: ")
message = "AAAAAA"

try:
    # messageのバイト列への変換
    message_bits = message.encode('utf-8')
    message_length = len(message_bits)
    if message_length > 4096:
        i = 0
        while i < message_length:
            if i + 4096 > message_length:
                chunk = message_bits[i:]
            else:
                chunk = message_bits[i:i+4096]
            message = protocol_message(username, chunk)
            sent = sock.sendto(message, (server_address, server_port))
            print('Sent {} bytes from position {}'.format(sent, i))

            i += 4096
    else:
        message = protocol_message(username, message_bits)
        sent = sock.sendto(message, (server_address, server_port))
        print('Sent {} bytes'.format(sent))


    # 応答を受信
    print('wating to receive')
    data, server = sock.recvfrom(4096)
    print('received {!r}'.format(data))

finally:
    print('closing socket')
    sock.close()