'''
KTN-project 2013 / 2014
Very simple server implementation that should serve as a basis
for implementing the chat server
'''
import SocketServer
from threading import Thread
import json
import time

'''
The RequestHandler class for our server.

It is instantiated once per connection to the server, and must
override the handle() method to implement communication to the
client.
'''


class ClientHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # Get a reference to the socket object
        self.connection = self.request
        # Get the remote ip adress of the socket
        self.ip = self.client_address[0]
        # Get the remote port number of the socket
        self.port = self.client_address[1]
        print 'Client connected @' + self.ip + ':' + str(self.port)
        # Wait for data from the client
        while 1:
            try:
                jsonobj = self.connection.recv(1024)
                done = self.checkUsername(json.loads(jsonobj))
                if done:
                    break
                else:
                    continue
            except Exception:
                print "client connection failed"
                break


    def sendErrorMessage(self,errorMessage,username):
        d = {'response': 'login', 'error': errorMessage, 'username':username}
        self.connection.sendall(json.dumps(d))

    def validUsername(self,username):
        if username == "":
            self.sendErrorMessage("invalid username: " + username + ", username can only contain alphanumerical values and underscores", username)
            return False
        chars = set('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ_')
        if any((c not in chars) for c in username):
            print 'not ok'
            self.sendErrorMessage("invalid username: " + username + ", username can only contain alphanumerical values and underscores", username)
            return False
        else:
            print 'ok'
            return True
        return True


    def checkUsername(self,data):
        if data.has_key("username"):
            username = data['username']
        else:
            return False
        validUsername = self.validUsername(username)
        if not validUsername:
            return False
        allowed = not self.server.usernameExist(username)
        if allowed:
            print "username ok"
            Worker(self.server,self.request, username)
            return True
        else:
            print "username not ok"
            self.sendErrorMessage("username already exists",username)
        return False
'''
This will make all Request handlers being called in its own thread.
Very important, otherwise only one client will be served at a time
'''

#####################################################################################################################################
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self,hostPort, clientHandler):
        self.list = {}
        self.messages = []
        SocketServer.TCPServer.__init__(self,hostPort,clientHandler)

    def usernameExist(self, username):
        return self.list.has_key(username)

    def addWorker(self, worker, username):
        self.list[username]= worker
        print "worker added"

    def sendMessage(self,username,data):
        if not self.usernameExist(username):
            return False
        timeAndMessage = username + "@" + time.strftime("%H:%M") + ":   " + data
        self.messages.append(timeAndMessage)
        for worker in self.list.itervalues():
            worker.sendMessage(timeAndMessage)
        return True
    def removeWorker(self,username):
        self.list.pop(username,None)
        print "worker removed"
    def getMessages(self):
        return self.messages

###################################################################################################################################
'''
    When a user has successfully connected to the server the worker handles all coummunication between user and server.
    The worker calls the server when it recieves messages, and the server contacts all users.
    The worker disconnects himself if the connection fails
'''
class Worker(Thread):

    def __init__(self, listener, connection, username):
        self.daemeon = True
        Thread.__init__(self)
        self.connection = connection
        self.listener = listener
        self.username = username
        self.listener.addWorker(self, username)
        self.run()
#        Thread.start()


    def run(self):
        self.initialMessage()
        print "A thread has started!!"
        while 1:
            try:
                data = self.connection.recv(1024)
                if data:
                    print data + " printed in thread"
                    self.decode(data)
                else:
                    print 'Client disconnected!'
                    raise Exception("damn")
            except Exception:
                self.listener.removeWorker(self.username)
                break
    def initialMessage(self):
        d = {'response': 'login', 'username': self.username}
        d['messages'] = self.listener.getMessages()
        self.connection.sendall(json.dumps(d))



    def decode(self,data):
        dictionary= json.loads(data)
        request = dictionary['request']
        if request == 'message':
            theMessage = dictionary['message']
            success = self.listener.sendMessage(self.username,theMessage)
            if not success:
                self.errorMessage('message')
        elif request == 'logout':
            userExist = self.listener.usernameExist(self.username)
            if userExist:
                dictionary = {'response': 'logout','username': self.username}
                self.connection.sendall(json.dumps(dictionary))
            else:
                self.errorMessage('logout')
        else:
            self.errorMessage(request)


    def errorMessage(self, request):
        if request == 'message':
            dictionary = {'response': 'message','error': 'You are not logged in!'}
        elif requset == 'logout':
            dictionary = {'response': 'logout','error': 'Not logged in!','username': self.username}
        else:
            dictionary = {'response': 'error','error': 'Request: ' + request + ' not recognized'}
        self.connection.sendall(json.dumps(dictionary))

    def sendMessage(self,data):
        dictionary = {'response': 'message','message': data}
        self.connection.sendall(json.dumps(dictionary))



if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 9999

    # Create the server, binding to localhost on port 9999
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
