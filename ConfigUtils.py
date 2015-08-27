__author__ = 'sagi'

import json
import os
import sys

"""
This module handles the configuration data.
"""


class ConfigUtils(object):
    def __init__(self):

        os.environ['CONF_PATH'] = "C:\\Users\\sagi\\PycharmProjects\\mrph_2\\config.json"

        filePath = os.getenv('CONF_PATH')
        print ("The file path is: " + os.getenv('CONF_PATH'))
        print "=============================================================="

        if filePath is not None:
            with open(filePath) as data_file:
                data = json.load(data_file)

            self.port = data.get("Port")
            self.supported_machines = data.get("Supported")
            self.max_clients = data.get("Max clients")
            self.max_machines = data.get("Max machines")

        else:
            print "Error- bad path for config file"
            sys.exit(1)

    def validate(self):

        """validates data from config file"""

        if isinstance(self.port, int):
            if self.port > 65536 or self.port < 1024:
                return False
        else:
            return False

        if not isinstance(self.max_clients, int) or not isinstance(self.max_machines, int):
            return False

        if type(self.supported_machines) is not list and type(self.supported_machines) is not tuple:
            return False

        return True
