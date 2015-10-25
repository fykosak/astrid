import cherrypy
import os.path
import cherrypy.lib.auth_basic
import re
import stat
import urllib
import datetime
from cherrypy.lib import cptools, http
from cherrypy.lib.static import staticdir

from ConfigParser import ConfigParser

import astrid


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
            dtim = datetime.datetime.fromtimestamp( dmtime ).isoformat(' ')
            fh += """<tr><td><a href="%s">%s/</a></td><td>%s</td><td>%s</td></tr>""" % ( dn + '/',  dn, "", dtim,)

        del ddirs[:] # limit to one level

        for fil in sorted( dfiles ):
            if fil.startswith("."):
                continue
            fn = os.path.join( dpath, fil )
            siz = os.path.getsize( fn )
            fmtime = os.path.getmtime( fn )
            ftim = datetime.datetime.fromtimestamp( fmtime ).isoformat(' ')
            fh += """<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td></tr>""" % ( fil, fil, str(siz), ftim, )

    fh += '</table>'
    # postamble
    if hdr:
        fh += """
</html>
"""

    return fh

def staticdirindex(section, dir, root="", match="", content_types=None, index="", indexlistermatch="", indexlister=None, **kwargs):
    """Serve a directory index listing for a dir.

    Compatibility alert: staticdirindex is built on and is dependent on
    staticdir and its configurations.  staticdirindex only works effectively
    in locations where staticdir is also configured.  staticdirindex is
    coded to allow easy integration with staticdir, if demand warrants.

    indexlister must be configured, or no function is performed.
    indexlister should be a callable that accepts the following parameters:
        section: same as for staticdir (and implicitly calculated for it)
        dir: same as for staticdir, but already combined with root
        path: combination of section and dir

        Other parameters that are configured for staticdirindex will be passed
        on to indexlister.

    Should use priorty > than that of staticdir, so that only directories not
    served by staticdir, call staticdirindex.

"""
    req = cherrypy.request
    response = cherrypy.response
    
    user = req.login
    reponame = req.path_info.split("/")[1]
    if reponame not in ["info", "build", "buildlog"]:
        if reponame not in astrid.repos.sections():
                raise cherrypy.HTTPError(404)
            
        if user not in astrid.repos.get(reponame, "users"):
            raise cherrypy.HTTPError(401)


    match = indexlistermatch

    # first call old staticdir, and see if it does anything
    sdret = staticdir( section, dir, root, match, content_types, index )
    if sdret:
        return True

    # if not, then see if we are configured to do anything
    if indexlister is None:
        return False

    # N.B. filename ending in a slash or not does not imply a directory
    # the following block of code directly copied from static.py staticdir
    if match and not re.search(match, cherrypy.request.path_info):
        return False
    
    # Allow the use of '~' to refer to a user's home directory.
    dir = os.path.expanduser(dir)

    # If dir is relative, make absolute using "root".
    if not os.path.isabs(dir):
        if not root:
            msg = "Static dir requires an absolute dir (or root)."
            raise ValueError(msg)
        dir = os.path.join(root, dir)
    
    # Determine where we are in the object tree relative to 'section'
    # (where the static tool was defined).
    if section == 'global':
        section = "/"
    section = section.rstrip(r"\/")
    branch = cherrypy.request.path_info[len(section) + 1:]
    branch = urllib.unquote(branch.lstrip(r"\/"))
    
    # If branch is "", filename will end in a slash
    filename = os.path.join(dir, branch)
    
    # There's a chance that the branch pulled from the URL might
    # have ".." or similar uplevel attacks in it. Check that the final
    # filename is a child of dir.
    if not os.path.normpath(filename).startswith(os.path.normpath(dir)):
        raise cherrypy.HTTPError(403) # Forbidden
    # the above block of code directly copied from static.py staticdir
    # N.B. filename ending in a slash or not does not imply a directory

    # Check if path is a directory.

    path = filename
    # The following block of code copied from static.py serve_file

    # If path is relative, users should fix it by making path absolute.
    # That is, CherryPy should not guess where the application root is.
    # It certainly should *not* use cwd (since CP may be invoked from a
    # variety of paths). If using tools.static, you can make your relative
    # paths become absolute by supplying a value for "tools.static.root".
    if not os.path.isabs(path):
        raise ValueError("'%s' is not an absolute path." % path)
    
    try:
        st = os.stat(path)
    except OSError:
        # The above block of code copied from static.py serve_file

        return False

    if stat.S_ISDIR(st.st_mode):

        # Set the Last-Modified response header, so that
        # modified-since validation code can work.
        response.headers['Last-Modified'] = http.HTTPDate(st.st_mtime)
        cptools.validate_since()
        response.body = indexlister( section=section, dir=dir, path=path,
                                     **kwargs )
        response.headers['Content-Type'] = 'text/html'
        req.is_index = True
        return True

    return False

# Replace the real staticdir with our version
cherrypy.tools.staticdir = cherrypy._cptools.HandlerTool( staticdirindex )


