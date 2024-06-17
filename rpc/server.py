import math
import json
import socket
import os

class SocketHandler:
    """ This is the class that handle socket connection
    """

    def __init__(self, server_address='/tmp/socket_file'):
        self.server_address = server_address
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.setup_socket()
    
    def setup_socket(self):
        # 以前の接続が残っていた場合には削除する
        try:
            os.unlink(self.server_address)
        except FileNotFoundError:
            pass

        self.sock.bind(self.server_address)
        print('starting on {}'.format(self.server_address))
    
    def listen(self, backlog=1):
        self.sock.listen(backlog)
    
    def accept_connection(self):
        try:
            connection, client_address = self.sock.accept()
            return connection, client_address
        except Exception as e:
            print(f"Error accepting connection: {e}")
            return None, None

    def close(self):
        self.sock.close()

class JsonValidator:
    """This is the class that validates JSON request"""

    @staticmethod
    def validateJson(data):
        # 送られてきたデータがjsonかどうかをチェック
        try:
            dic_data = json.loads(data)
        except ValueError as e:
            return False
        
        # 送られてきたデータに適切なkeyが存在しているかチェック
        required_key = ["method", "params", "param_types", "id"]
        for key in required_key:
            if key not in dic_data:
                return False
        return True

class Server:
    """ This is the main class that handle server
    """

    def __init__(self):
        self.socket_handler = SocketHandler()
        self.jsonValidator = JsonValidator()
        self.connections = {} # ソケットを管理するための辞書

    def send_error(self, connection, error_message, request_id=None):
        error_response = {
            "status": "error",
            "message": error_message,
            "id": request_id
        }
        connection.sendall(json.dumps(error_response).encode('utf-8'))
        
    def run(self):
        # 最大クライアント5つの接続要求をリッスンする
        self.socket_handler.listen(5)

        while True:
            # クライアントからの接続要求を受け入れる
            connection, client_address = self.socket_handler.accept_connection()
            client_id = ""
            try:
                print('connection from {}'.format(client_address))

                # サーバーが新しいデータを待ち続ける
                while True:
                    data = connection.recv(1024)
                    print(data)
                    if not data:
                        break

                    data_str = data.decode('utf-8')
                    # 受け取ったデータを表示します。
                    print('Received ' + data_str)
                    
                    if self.jsonValidator.validateJson(data_str):
                        data = json.loads(data_str)

                        # クライアントからの接続を辞書に格納します
                        client_id = data["id"]
                        self.connections[client_id] = connection

                        # calcurationクラスに必要なデータを用意します
                        functionname = data["method"]
                        input_value = data["params"]
                        input_paramtype = data["param_types"]

                        calc = Calculations(functionname, input_value, input_paramtype)
                        result = calc.calculate()

                        # クライアントにかえす結果
                        response = {
                            "results": result["result"],
                            "result_type": result["result_type"],
                            "id": data["id"]
                        }
                        print(response)
                        json_response = json.dumps(response)

                        # クライアントに結果をかえす
                        connection.sendall(json_response.encode())
                    
                    else:
                        print("Invalid JSON received")
                        self.send_error(connection, "Invalid JSON format")
                        break
            
            except ValueError as e:
                print(f"ValueError: {e}")
                self.send_error(connection, str(e))
                break

            except KeyError as e:
                print(f"KeyError: {e}")
                self.send_error(connection, str(e))
                break

            except Exception as e:
                print(f"Exception: {e}")
                self.send_error(connection, str(e))
                break

            finally:
                print("Closing current connection")
                connection.close()
                del self.connections[client_id]

class Calculations:
    """ This is the class that gathers methods to create a result of a request
    """

    def __init__(self, functionname, input_value, input_paramtype):
        """ インスタンス変数を初期化します"""
        self.input_value = input_value
        self.paramtype = input_paramtype
        self.functionname = functionname
        self.hashMap = {
            "floor": self.floor,
            "nroot": self.nroot,
            "reverse": self.reverse,
            "validAnagram": self.validAnagram,
            "sort": self.sort
        }
        self.validationhelperMap = {
            "floor": {
                "param_unit": 1,
                "param_type": ["float"]
            },
            "nroot": {
                "param_unit": 2,
                "param_type": ["int", "int"]
            },
            "reverse": {
                "param_unit": 1,
                "param_type": ["string"]
            },
            "validAnagram": {
                "param_unit": 2,
                "param_type": ["string","string"]
            },
            "sort": {
                "param_unit": 1,
                "param_type": ["strArr"]
            }
        }
    
    def validateHelper(self):
        if self.functionname not in self.hashMap:
            raise ValueError(f"Function {self.functionname} is not in hashMap")
        if len(self.input_value) != self.validationhelperMap[self.functionname]["param_unit"]:
            raise ValueError("params is not correct")
        if len(self.input_value) != len(self.paramtype):
            raise ValueError("paramtype or inputvalue length is not compatible")
        for i in range(len(self.paramtype)):
            if self.paramtype[i] != self.validationhelperMap[self.functionname]["param_type"][i]:
                raise ValueError("paramtype is not correct")
            
        return True
    
    def calculate(self):
        if self.validateHelper():
            method_to_call = self.hashMap[self.functionname]
            return method_to_call()
        else:
            raise ValueError("Request is invalid")

    def floor(self):
        result = math.floor(self.input_value[0])
        result_type = type(result).__name__

        return {
            "result": result,
            "result_type": result_type
        }

    def nroot(self):
        result = math.pow(self.input_value[1], 1/self.input_value[0])
        result_type = type(result).__name__

        return {
            "result": result,
            "result_type": result_type
        }
    
    def reverse(self):
        result = self.input_value[0][::-1]
        result_type = type(result).__name__

        return {
            "result": result,
            "result_type": result_type
        }

    def validAnagram(self):
        if len(self.input_value[0]) != len(self.input_value[1]):
            return {
                "result": "The strings are not anagram.",
                "result_type": "string"
            }
        hashmap1 = {}
        hashmap2 = {}
        for s in self.input_value[0]:
            if s in hashmap1:
                hashmap1[s] += 1
            else:
                hashmap1[s] = 1
        for s in self.input_value[1]:
            if s in hashmap2:
                hashmap2[s] += 1
            else:
                hashmap2[s] = 1
        for key in hashmap1:
            if key not in hashmap2:
                return {
                "result": "The strings are not anagram.",
                "result_type": "string"
            }
            if hashmap1[key] != hashmap2[key]:
                return {
                "result": "The strings are not anagram.",
                "result_type": "string"
            }
        return {
                "result": "The strings are anagram.",
                "result_type": "string"
            }

    
    def sort(self):
        result = sorted(self.input_value[0])
        result_type = type(result).__name__
        return {
            "result": result,
            "result_type": result_type
        }
    

# サーバの起動
if __name__ == "__main__":
    server = Server()
    server.run()

