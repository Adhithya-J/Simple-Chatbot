import socket
import threading
import os
from string import punctuation

import chatbot
import utils

conf = utils.get_config()
toBool = lambda str: True if str == "True" else False 
DEBUG_SERVER = toBool(conf["DEBUG"]["server"])

def session(connection):
    i = 0
    startMessage = "Starting bot...\n"

    conf = utils.get_config()

    DBHOST = conf["MySQL"]["server"]
    DBUSER = conf["MySQL"]["dbuser"]
    DBNAME = conf["MySQL"]["dbname"]

    print("Starting bot...")

    print("Connecting to database...")
    DBconnection = utils.db_connection(DBHOST, DBUSER, DBNAME)
    DBcursor = DBconnection.cursor()
    DBconnectionID = utils.db_connectionID(DBcursor)

    print("...connected")

    botSentence = "Hello!"
    weight = 0

    trainMe = False

    startMessage = startMessage + ("...started\n")

    def receive(connection):

        if DEBUG_SERVER: print(f"PID {pid}, thread {thread} \n")
        received = connection.recv(1024)
        if not received:
            print(f"Closing connection {thread}")
            return False
        else:
            if DEBUG_SERVER: print(f"Received {received}, echoing")
            return received
        
    while True:
        pid = os.getpid()
        thread = threading.current_thread()

        received = receive(connection)
        humanSentence = received.decode().strip()
        
        if ((humanSentence == "") or (humanSentence.strip(punctuation).lower() == "quit") or (humanSentence.strip(punctuation).lower() == "exit")):
                break
                
        botSentence, weight, trainMe = chatbot.chat_flow(DBcursor, humanSentence, weight)


        if trainMe:
            send = "Bot> Please can you train me - enter a response for me to learn (or \"skip\" to skip)".encode()
            connection.send(send)
            previousSentence = humanSentence
            received = receive(connection)
            humanSentence =received.decode().strip()

            if humanSentence != "skip":
                chatbot.train_me(previousSentence, humanSentence, DBcursor)
                botSentence = "Bot> Thanks I've noted that"
            else:
                botSentence = "Bot> Okay, moving on..."
                trainMe = False
        DBconnection.commit()
        send = botSentence.encode()

        if i == 0:
            send = startMessage.encode() + send()

        connection.send()
        i+=1


if __name__ == "__main__":
    print("Starting...")

    LISTEN_HOST = conf["Server"]["listen_host"]
    LISTEN_PORT = conf["Server"]["tcp_socket"]
    LISTEN_QUEUE = conf["Server"]["listen_queue"]


    sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sckt.bind((LISTEN_HOST, LISTEN_PORT))
        sckt.listen(LISTEN_QUEUE)
        print("...socket set up")
    except Exception as e:
        print("botserver: Error in setting up the socket:",e)
        exit()



    try:
        while True:
            print("waiting for connection...")
            try:
                (connection, address) = sckt.accept()
                print("Connction received from ", address)
                t = threading.Thread(target = session, args = [connection], daemon=True)    
                t.start()
            except Exception as e:
                print("Error in accepting connection:",e)
                continue
    except KeyboardInterrupt:
        print("botserver: KeyboardInterrupt received, closing server...")
    
    print("Closing")
    sckt.close()
#    DBconnection.close()  # Close the database connection when exiting
