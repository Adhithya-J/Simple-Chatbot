import socket
import select
import argparse

parser = argparse.ArgumentParser(description="Interactive Chat Client using TCP Sockets")
parser.add_argument("-a", "--addr", dest = "host", default = "vhost1", help = "remote host-name or IP address", required = True)
parser.add_argument("-p", "--port", dest="port", type = int, default = 9999, help = "TCP port", required = True)

args = parser.parse_args()
ADDR = args.host
PORT  = args.port


def connect_to_server(host, port):
    sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_addr  = (host, port)
    try:
        sckt.connect(server_addr)
        print(f"Connected to server {ADDR} at port {PORT}")
        return sckt

    except Exception as e:
        print("Error connecting to server: ",e)
        return None

def close_connection(sckt):
    if sckt:
        try:
            sckt.shutdown(socket.SHUT_RDWR)
            sckt.close()
        except Exception as e:
            print("Error closing connection: ",e)


def chat_client():
    sckt = connect_to_server(ADDR, PORT)

    if not sckt:
        return None
    
    try:
        while True:
            ready_to_read, ready_to_write, in_error = select.select([sckt,],[sckt,],[],5)
            
            if not ready_to_read:
                continue
            
            message = input(">>>").strip()
            if not message:
                continue

            if message.lower() in ["exit","quit"]:   
                sckt.send(message.encode())
                sckt.send("".encode())
                break
            
            sckt.send(message.encode())
            print(sckt.recv(1024).decode())
    except KeyboardInterrupt:
        print("\nClosing connection...")
    finally:
        close_connection(sckt)
        print("Connection closed")

if __name__ == "__init__":
    chat_client()