'''
KTN-project 2013 / 2014
'''
import socket
import time
import thread
import json

class Client(object):

    def __init__(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def start(self, host, port):
        self.connection.connect((host, port))
        thread.start_new_thread(self.listen_for_connection,())
        self.login()
        print "Write 'exit' or 'logout' to quit"
        while self.connected:
            input = raw_input("message: ")
            if input == 'logout' or input == 'exit':
                self.send('logout','')
                break
            self.send('message', input)
            time.sleep(0.02)

    def login(self):
        while 1:
            username = raw_input("Type username: ")
            self.send('login',username)
            time.sleep(0.2)
            if self.connected:
              break

    def listen_for_connection(self):
        while 1:
            try:
                jsonobj = self.connection.recv(1024).strip()
                if jsonobj:
                    thread.start_new_thread(self.decodeJSON,(jsonobj,))
                else:
                    pass
            except Exception:
                print "stop listening"
                break

    def decodeJSON(self, jsonobj):
        dictionary = json.loads(jsonobj)
        if self.noError(dictionary):
            type = dictionary["response"]
            if type == 'login':
                self.loginSuccess(dictionary)
            elif type == 'message':
                    print dictionary['message']
            elif type == 'logout':
                print "logout successful!"
                self.connected = False
                self.connection.close()
            else:
                print 'unknown response from server'

    def noError(self,dictionary):
        if not dictionary.has_key('error'):
                return True
        else:
            print dictionary['error']
            return False

    def message_received(self, message):
        print "Recived: " + message + " on server"

    def loginSuccess(self, dictionary):
        self.connected = True
        print "Welcome " + dictionary['username']
        for message in dictionary['messages']:
            print message

    def send(self, type, data):
        d = {'request': type}
        if not type == 'logout':
            if type == 'login':
                d['username'] = data
            else:
                d[type] = data
        self.connection.sendall(json.dumps(d))

if __name__ == "__main__":
    client = Client()
    client.start('localhost', 9999)
