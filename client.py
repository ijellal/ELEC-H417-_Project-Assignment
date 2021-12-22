import socket
import threading
import sys
import getpass
import time
from cryptography.fernet import Fernet

HEADER_LENGTH = 256

#Wait for incoming data from server
#.decode is used to turn the message in bytes to a string
def receive(socket, signal,fernet):
    while signal:
        try:
            data = socket.recv(HEADER_LENGTH)
            print(data.decode("utf-8"))
            if data.decode("utf-8")=="exit":
                
                break
            else:
              
                dec_message = fernet.decrypt(data).decode("utf-8")
                print(dec_message)
            
        except:
            print("You have been disconnected from the server")
            signal = False
            break
    socket.close()

def send(socket, signal,fernet):
    while signal:
        try:
            message = input()
            if message!="":
                if message =="exit":
                    socket.send(message.encode("utf-8"))
                    break
                enc_message = fernet.encrypt(message.encode("utf-8"))
                socket.send(enc_message)
        except:
            print("You have been disconnected from the server")
            signal = False
            break
    socket.close()
  

def ask_password(client_socket):
    
    password_test = getpass.getpass("Your username exists, please put your password:  ")
    client_socket.send(password_test.encode("utf-8"))
    password_in_database = client_socket.recv(HEADER_LENGTH).decode("utf-8")
    if password_in_database == "True":
        print('Your password is valid')
    else:
        print('Your password is wrong')
        ask_password(client_socket)


def ask_username(client_socket):
    username_test = input("Please enter your username: ")
    client_socket.send(username_test.encode("utf-8"))
    username_in_database = client_socket.recv(HEADER_LENGTH).decode("utf-8")
    
    if username_in_database == "True":
        ask_password(client_socket)
        return username_test
    else:
        print("Your username is not in the database")
        return ask_username(client_socket)


def check_if_username_in_database(client_socket):
    username = input("Please enter your username: ")
    client_socket.send(username.encode("utf-8"))
    bool_check = client_socket.recv(HEADER_LENGTH).decode("utf-8")
    if bool_check =="False":
        password_test = getpass.getpass("Enter your new password : ")
        key1 = Fernet.generate_key()
        fernet1 = Fernet(key1)
        filename = username+".txt"
        f = open(filename,"w")
        f.write(key1.decode('utf-8'))
        f.close()
        enc_message = fernet1.encrypt(password_test.encode('utf-8')) 
        client_socket.send(enc_message)
        return username
    else:
        print("Your username is already used")
        return check_if_username_in_database(client_socket)

def connexion_database(client_socket):
    print("Welcome to te chat application\n ")
    try:
        response = input("Are you  already registered in the application ? [Yes/No] : ")
        client_socket.send(response.encode("utf-8"))
        if response =="No" or response == "no" or response == "NO":
            username = check_if_username_in_database(client_socket)
        elif response == "Yes" or response == "yes" or response == "YES":
            username = ask_username(client_socket)
        print("You are now connected to the database ! ")
        return username
    except:
        print("Wrong answer to [Yes/No] \n")

def start_conversation(current_user,sock):
    correspondant = input("Who do you want to start a converstation with ? ")
    sock.send(correspondant.encode("utf-8"))
    bool_check2 = sock.recv(HEADER_LENGTH).decode("utf-8")
    if (bool_check2 == "True") and (current_user == correspondant):
        print("You can't create a conversation with yourself!")
        return start_conversation(current_user, sock)

    elif (bool_check2 == "False"):
        print("This username doesn't exist ")
        return start_conversation(current_user, sock)

    elif (bool_check2 == "True") and (current_user != correspondant):
        print("Wait for the key to be generated ... ")
        potential_key = sock.recv(HEADER_LENGTH).decode("utf-8")
        print("This is the key : " + potential_key)
        response = input("Do you agree to talk with this key ? [Yes/No] : ")
        sock.send(response.encode("utf-8"))
        if response =="No" or response == "no" or response == "NO":
            sum = sock.recv(HEADER_LENGTH).decode("utf-8")
            if(sum=="0") or (sum=="-2"):
                return start_conversation(current_user, sock)
        elif response == "Yes" or response == "yes" or response == "YES":
            resp_no = sock.recv(HEADER_LENGTH).decode("utf-8")
            if resp_no == "-1":
                return start_conversation(current_user, sock)
            print("You can start the conversation ! \n")
            fernet = Fernet(potential_key.encode("utf-8"))
            return fernet


#Get host and port
host = input("Enter ip address : ")
port = int(input("Enter your port : "))

#Attempt connection to server
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
except:
    print("Could not make a connection to the server")
    input("Press enter to quit")
    sys.exit(0)

current_user = str(connexion_database(sock))

# Envoi du user actuel
sock.send(current_user.encode("utf-8"))
fernet_test = start_conversation(current_user,sock)


#Create new thread to wait for data
receiveThread = threading.Thread(target = receive, args = (sock, True,fernet_test))
receiveThread.start()

#Send data to server
#str.encodes used to turn the string message into bytes so it can be sent across the network
sendThread = threading.Thread(target = send, args = (sock, True,fernet_test))
sendThread.start()