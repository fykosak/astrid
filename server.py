#!/usr/bin/python

import BaseHTTPServer
import ConfigParser

from Controller import Controller

srv_section = "Server"
config = ConfigParser.ConfigParser({"address": "", "port":"8000"})
config.read("config.ini")


try:
    server_address = (config.get(srv_section, "address"), int(config.get(srv_section, "port")))
    httpd = BaseHTTPServer.HTTPServer(server_address, Controller)
    httpd.serve_forever()
except KeyboardInterrupt:
    print "Server killed on user request (keyboard interrupt)."
