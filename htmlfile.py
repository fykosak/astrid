import os
import os.path
import datetime
import cherrypy

def htmlfile(content=""):
    fh = ''
    url = "http://" + cherrypy.request.headers.get('Host', '') + \
             cherrypy.request.path_info

    # preamble
    fh += """<html>
<head>
<title>%s</title>
<style type="text/css">@import url("/filestyle.css");</style>
</head>
<body>
""" % url

    
    fh += '<pre>'
    fh += content
    fh += '</pre>'
    return fh