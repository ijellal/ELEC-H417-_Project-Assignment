import json
import signal
import socket
import sys
import threading
from cryptography.fernet import Fernet
import time
from datetime import datetime

mutex = threading.Lock()

response_no = 0
response_yes = 0

def signal_handler(signal, frame):
        sys.exit(0)





#Variables for holding information about connections
connections = []
total_connections = 0
HEADER_LENGTH=256

#Variable about conversations
conversations_opened = []
conversations = []


#Client class, new instance created for each connected client
#Each instance has the socket and address that is associated with items
#Along with an assigned ID and a name chosen by the client
class Client(threading.Thread):
    def __init__(self, socket, address, id, name, signal):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self.name = name
        self.signal = signal
        #self.friend = friend
    
    def __str__(self):
        return str(self.id) + " " + str(self.address)
    
    #Attempt to get data from client
    #If unable to, assume client has disconnected and remove him from server data
    #If able to and we get data back, print it in the server and send it back to every
    #client aside from the client that has sent it
    #.decode is used to convert the byte data into a printable string
    def run(self):
        # Client registration, authentication and login
        my_dict2 = load_database("dico.json")
        response = self.socket.recv(HEADER_LENGTH).decode("utf-8")
        if response == "No" or response == "no" or response == "NO":
            check_if_username_in_database_server(self.socket,my_dict2)
        elif response == "Yes" or response == "yes" or response == "YES":
            ask_username_server(self.socket,my_dict2)
        
        # Start a conversation
        self.name = str(self.socket.recv(HEADER_LENGTH).decode("utf-8"))

        friend= input_correspondant_server(self.socket,self.name)
        for client in connections:
            if client.name == friend:
                receive_and_transfer(self,True,client)
        
  
def receive_and_transfer(client_from, signal,client_target):
    msgs=[]
    while signal:
        try:
            data = client_from.socket.recv(HEADER_LENGTH)
            if data.decode("utf-8") == "exit":
                client_target.socket.send(data)
                signal=False
            else:
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                new_data = str(current_time) + " " + client_from.name + " : " + data.decode('utf-8')
                msgs.append(new_data)
                client_target.socket.send(data)

        except:
            print(client_from.name + " have left conversation ")
            signal = False
            break
    
    list_tuple = [client_from.name,client_target.name]
    list_tuple.sort()
    duo= list_tuple[0]+list_tuple[1]
    file_name = duo+ ".txt"
    mutex.acquire()
    tf= open(file_name, "w")
    for i in msgs:
        tf.write(i+"\n")
    tf.close()
    mutex.release()
    client_from.socket.close()
   

#Wait for new connections
def newConnections(socket):
    while True:
        sock, address = socket.accept()
        global total_connections
        connections.append(Client(sock, address, total_connections, "Name", True))
        connections[len(connections) - 1].start()
        print("New connection at ID " + str(connections[len(connections) - 1]))
        total_connections += 1

def input_correspondant_server(socket,curr_user):
    global response_no
    global response_yes
    corrspdt = socket.recv(HEADER_LENGTH).decode("utf-8")
    bool_check = str(bool_connected(corrspdt))
    socket.send(bool_check.encode("utf-8"))
    if bool_check == "False":
        return input_correspondant_server(socket,curr_user)
    elif (bool_check == "True") and (corrspdt==curr_user):
        return input_correspondant_server(socket,curr_user)
    elif (bool_check == "True") and (curr_user != corrspdt):
        
        key,key_of_key = create_conversation_key(curr_user,corrspdt)
        time.sleep(1)
        socket.send(key.encode("utf-8"))
        response_no =0
        response_yes=0
        response = socket.recv(HEADER_LENGTH).decode("utf-8")
        if response =="No" or response == "no" or response == "NO":
            response_no -=  1
            while response_yes == 0 and response_no == -1:
                i=1
            
            sum=response_no+response_yes
            socket.send(str(sum).encode("utf-8"))
            return input_correspondant_server(socket,curr_user)
        elif response == "Yes" or response == "yes" or response == "YES":
            response_yes = response_yes + 1
            while response_yes == 1 and response_no == 0:
                i=1
            socket.send(str(response_no).encode("utf-8"))
            if response_no == -1:
                return input_correspondant_server(socket,curr_user)
            elif response_yes == 2:
                return corrspdt

   


def delete_key(key_of_key):
    keys_dico=load_database("keys_dico.json")
    keys_dico.pop(key_of_key)
    update_database(keys_dico,"keys_dico.json")

def bool_connected(corrspdt):
    for client in connections:
        if client.name == corrspdt:
            return True
    return False

def create_conversation_key(curr_user,corrspdt):
    keys_dico=load_database("keys_dico.json")
    list_tuple = [corrspdt,curr_user]
    list_tuple.sort()
    value_key_dico = list_tuple[0]+list_tuple[1]
    if value_key_dico not in keys_dico:
        conversation_key = generate_new_key()
        keys_dico[value_key_dico] = conversation_key
        update_database(keys_dico,"keys_dico.json")
    return keys_dico[value_key_dico],value_key_dico
        
def generate_new_key():
    key = Fernet.generate_key()
    return key.decode("utf-8")

def load_database(name):
    tf = open(name, "r")
    new_dict = json.load(tf)
    tf.close()
    return new_dict

def update_database(my_dict,name):
    tf = open(name, "w")
    json.dump(my_dict, tf)
    tf.close()

def add_user_database(username,password,my_dict):
    my_dict[username] = password
    
def check_username_in_database(username,my_dict):
    if username in my_dict.keys():
        return True
    return False
    
def check_password_with_database(username,password,my_dict):
    password_from_db = my_dict[username]
    filename = username+".txt"
    f = open(filename,"r")
    key_of_password = f.readline()
    f.close()
    fernet_check = Fernet(key_of_password.encode('utf-8'))
    password_decrypted = fernet_check.decrypt(password_from_db.encode('utf-8')).decode('utf-8')
    if password ==  password_decrypted:
        return True
    return False

def ask_password_server(socket,username3,my_dict2):
    password3 = socket.recv(HEADER_LENGTH).decode("utf-8")
    if check_password_with_database(username3,password3,my_dict2) is True:
        socket.send("True".encode("utf-8"))
    else:
        socket.send("False".encode("utf-8"))
        ask_password_server(socket,username3,my_dict2)

def ask_username_server(socket,my_dict):
    username = socket.recv(HEADER_LENGTH).decode("utf-8")
    if check_username_in_database(username,my_dict) is True:
        a = "True"
        socket.send(a.encode("utf-8"))
        ask_password_server(socket,username,my_dict)
    else:
        socket.send("False".encode("utf-8"))
        ask_username_server(socket,my_dict)

def check_if_username_in_database_server(socket,my_dict):
    username3 = socket.recv(HEADER_LENGTH).decode("utf-8")
    check = str(check_username_in_database(username3,my_dict))
    socket.send(check.encode("utf-8"))
    if check =="False":
        password3 = socket.recv(HEADER_LENGTH).decode("utf-8")
        add_user_database(username3, password3, my_dict)
        update_database(my_dict,"dico.json")
    else:
        check_if_username_in_database_server(socket,my_dict)


def main():

    signal.signal(signal.SIGINT, signal_handler)

    
    #Get host and port
    host = input("Enter ip address : ")
    port = int(input("Enter your port : "))

    #Create new server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)

    #Create new thread to wait for connections
    newConnectionsThread = threading.Thread(target = newConnections, args = (sock,))
    newConnectionsThread.start()
    global response_agree
    response_agree = 0
    

main()
