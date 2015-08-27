__author__ = 'sagi'

import socket
import threading
import json
from random import randint
import sys
from ConfigUtils import ConfigUtils
import logging

"""this module holds the multi-threaded server logic"""


class Server(object):
    def __init__(self):

        self.connection_lock = threading.Lock()

        self.connections = set()  # also tells current num of clients
        self.client_connections_map = {}
        self.clients_id_rise = 1
        self.clients_data = {}  # client and it's allocated machines
        self.current_allocated = 0
        self.rand_ids = []

        self.supported_machines_list = []
        self.max_machines_limit = 0

        logging.basicConfig(filename='serverLog.log', level=logging.DEBUG,
                            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    def random_with_n_digits(self, n):
        """ generate n digits random number"""

        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def allocate_machines(self, connection, clients_request):  # synchronized
        """ this function gets the client's request and allocates the machines with unique id,
            while enforcing the total max number of machines.
            return: dict with allocated machines & boolean which tells if whole requested
            machines were allocated"""

        all_allocated = True
        return_dict = {}
        flag = True
        rand = 0

        for key, value in clients_request.items():
            if self.current_allocated >= self.max_machines_limit \
                    or not self.supported_machines_list.__contains__(value.lower()):
                logging.error('Cannot allocate machines for client ID %s due to max limit'
                              % self.client_connections_map[connection])
                all_allocated = False
                continue
            while flag:
                rand = self.random_with_n_digits(4)
                if not self.rand_ids.__contains__(rand):
                    flag = False
                    self.rand_ids.append(rand)

            new_machine = "private_" + str(value) + "_" + str(rand)
            return_dict[key] = new_machine
            self.current_allocated += 1

            flag = True

        client_id = self.client_connections_map[connection]

        if self.clients_data.__contains__(client_id):
            self.clients_data[client_id].update(return_dict)  # merge
        else:
            self.clients_data[client_id] = return_dict

        ret = (return_dict, all_allocated)
        return ret

    def receive(self, connection):
        """ receiving thread working with each client"""

        while True:
            print "Waiting for clients request"
            logging.info("Waiting for clients request")

            try:
                message = connection.recv(1024)
            except:
                print "Closing connection due to brutally shutdown"
                logging.error("Closing connection due to brutally shutdown")

                self.connection_lock.acquire()
                self.disconnect_client(connection)
                self.connection_lock.release()
                return

            if not message:
                print "Client has exited. Closing connection and removing from list"
                logging.error("Client has exited. Closing connection and removing from list")

                self.connection_lock.acquire()
                self.disconnect_client(connection)
                self.connection_lock.release()
                return

            try:
                clients_request = json.loads(message)
                print "Received request: %s " % clients_request
                logging.info("Received request: %s " % clients_request)
                self.connection_lock.acquire()

                if "command" in clients_request:  # client wants to disconnect
                    if clients_request["command"] == "disconnect":
                        self.disconnect_client(connection)
                        logging.info("client %s requested to disconnect"
                                     % self.client_connections_map[connection])
                else:
                    (return_dict, all_alocated) = self.allocate_machines(connection, clients_request)
                    self.send_back_json(return_dict, all_alocated, connection)

                self.connection_lock.release()

            except:
                print "Error on client input"
                logging.error("Error on client input")

    def send_back_json(self, return_dict, all_alocated, connection):
        """ sends back the json result to client, which holds a dict with allocated machines,
            and a statement that tells if the process went well or not """

        logging.info("Sending back Json to client ID %s" % self.client_connections_map[connection])

        response = {}
        if all_alocated:

            response['statement'] = 'You got everything you requested for'

        else:

            response['statement'] = 'Not all machines were allocated. check log for more info'
        response['data'] = return_dict

        serialized_res = json.dumps(response)
        connection.send(serialized_res)
        # self.connection_lock.release()

    def disconnect_client(self, connection):

        logging.info("Disconnecting client ID %s" % self.client_connections_map[connection])

        if connection not in self.connections:
            return

        try:
            # remove from connections set
            self.connections.remove(connection)

            client_id = self.client_connections_map[connection]
            if client_id in self.clients_data:
                clients_machines = self.clients_data[client_id]

                # remove all client's machines
                for key, value in clients_machines.items():
                    cut_rand = int(value[-4:])
                    if self.rand_ids.__contains__(cut_rand):
                        self.current_allocated -= 1
                        self.rand_ids.remove(cut_rand)

                # remove from client's data
                del self.clients_data[client_id]

            # remove from connections map
            del self.client_connections_map[connection]

            connection.send("Disconnected from server")
            connection.close()
        except:
            print "Warning - connection might disconnected brutally "
            logging.error("Warning - connection might disconnected brutally ")

    # -----------------

    def main(self):

        config_data = ConfigUtils()
        if not config_data.validate():
            print "Error- invalid data in config file"
            logging.error("Error- invalid data in config file")

            sys.exit(1)

        self.supported_machines_list = config_data.supported_machines
        self.max_machines_limit = config_data.max_machines

        # Set up the listening socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostname()  # local
        try:
            s.bind((host, config_data.port))
        except socket.error as err:
            print "Error: socket error\n" + err.message
            logging.error("Error: socket error\n" + err.message)
            sys.exit(1)
        print "Server is listening on port {p}...".format(p=config_data.port)

        s.listen(30)

        # accept connections in a loop
        while True:
            (connection, address) = s.accept()
            print "Got connection"
            self.connection_lock.acquire()

            if len(self.connections) >= config_data.max_clients:
                try:
                    connection.send("Sorry, too many clients connected")
                    logging.error("Sorry, too many clients connected")
                    # connection.shutdown()
                    connection.close()
                except:
                    print "Error on closing connection"
                    logging.error("Error on closing connection")
            else:
                connection.send("Connection succeeded")
                logging.info("Connection succeeded")
                self.connections.add(connection)
                self.client_connections_map[connection] = self.clients_id_rise
                self.clients_id_rise += 1
                self.connection_lock.release()
                threading.Thread(target=self.receive, args=[connection]).start()


if __name__ == '__main__':
    s = Server()
    s.main()
