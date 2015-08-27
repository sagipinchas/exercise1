__author__ = 'sagi'

import socket
import sys
import select
import json

"""this module holds the clients logic"""


class Client(object):
    def __init__(self):

        self.is_connected = False
        self.clients_machines = {}
        self.port = 31337
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()

    def getVirtualMachines(self, req):

        if self.is_connected is False:
            print "Error: client is not connected to server"
            return

        serialized = json.dumps(req)

        self.client.send(serialized)

        while True:
            (readable, writable, errored) = select.select([self.client], [], [self.client], 0.1)
            if readable or errored:
                response = self.client.recv(1024)
                if not response:
                    print "Disconnected"
                    return

                # print response
                res_dict = json.loads(response)
                statement = res_dict['statement']
                data = res_dict['data']
                print "Server response>> " + statement

                return data

    def connect(self):

        print "Connecting to server.."
        try:
            self.client.connect((self.host, self.port))

            while True:
                response = ""
                (readable, writable, errored) = select.select([self.client], [], [self.client], 0.1)
                if readable or errored:
                    response = self.client.recv(1024)

                if response != "":
                    print "Server response>> " + response
                    if "succeeded" in response:
                        self.is_connected = True
                    break
        except:
            print "Error connecting to server"
            sys.exit(1)

    def disconnect(self):

        if self.is_connected is False:
            print "Error: client is not connected to server"
            return

        disconnect = {"command": "disconnect"}

        serialized = json.dumps(disconnect)
        self.client.send(serialized)

        while True:

            response = ""
            (readable, writable, errored) = select.select([self.client], [], [self.client], 0.1)
            if readable or errored:
                response = self.client.recv(1024)

            if response != "":
                print "Server response>> " + response
                if "Disconnected" in response:
                    self.is_connected = False
                break

# if __name__ == "__main__":
#     c = Client()
#     c.connect()
