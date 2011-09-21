import os
import os.path
import datetime
import cherrypy

def htmldir( section="", dir="", path="", hdr=True, **kwargs ):
    fh = ''
    url = "http://" + cherrypy.request.headers.get('Host', '') + \
             cherrypy.request.path_info

    # preamble
    if hdr:
        fh += """<html>
<head>
<title>Directory listing for: %s</title>
<style type="text/css">@import url("/dirstyle.css");</style>
</head>
<body>
""" % url

    path = path.rstrip(r"\/")
    fh += '<h3>Directory listing for: <a href="' + url + '">' + url + \
             '</a></h3><hr>\n'
    fh += '<table><tr><th>File</th><th>Size</th><th>Last mod</th></tr>'
    
    fh += """<tr><td><a href="%s">%s/</a></td><td>%s</td><td>%s</td></tr>""" % ( "..",  "..", "", "",)
    for dpath, ddirs, dfiles in os.walk( path ):

        for dn in sorted( ddirs ):
            if dn.startswith("."):
                continue
            fdn = os.path.join( dpath, dn )
            dmtime = os.path.getmtime( fdn )
            dtim = datetime.datetime.fromtimestamp( dmtime ).isoformat('-')
            fh += """<tr><td><a href="%s">%s/</a></td><td>%s</td><td>%s</td></tr>""" % ( dn + '/',  dn, "", dtim,)

        del ddirs[:] # limit to one level

        for fil in sorted( dfiles ):
            if fil.startswith("."):
                continue
            fn = os.path.join( dpath, fil )
            siz = os.path.getsize( fn )
            fmtime = os.path.getmtime( fn )
            ftim = datetime.datetime.fromtimestamp( fmtime ).isoformat('-')
            fh += """<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td></tr>""" % ( fil, fil, str(siz), ftim, )

    fh += '</table>'
    # postamble
    if hdr:
        fh += """
</html>
"""

    return fh