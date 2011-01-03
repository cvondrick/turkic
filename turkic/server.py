"""
A lightweight server framework. 

To use this module, import the 'application' function, which will dispatch
requests based on handlers. To define a handler, decorate a function with
the 'handler' decorator. Example:

>>> from turkic.server import handler, application
... @handler
... def spam():
...     return True
"""

import json

handlers = {}

def handler(type = "json", jsonify = None, raw = False):
    """
    Decorator to bind a function as a handler in the server software.

    type        specifies the Content-Type header
    jsonify     dumps data in json format if true
    raw         gives handler full control of environ if ture
    """
    type = type.lower()
    if type == "json" and jsonify is None:
        jsonify = True
        type == "text/json"
    def decorator(func):
        handlers[func.__name__] = (func, type, jsonify, raw)
        return func
    return decorator

def application(environ, start_response):
    """
    Dispatches the server application through a handler. Specify a handler
    with the 'handler' decorator.
    """
    path = environ.get("PATH_INFO", "").lstrip("/").split("/")

    try:
        action = path[0]
    except IndexError:
        raise Error404("Missing action.")

    try:
        handler, type, jsonify, raw = handlers[action]
    except KeyError:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return action + " in " + ",".join(handlers)
        return ["Error 404\n", "Action {0} undefined.".format(action)]

    try:
        if raw:
            response = handler(environ)
        else:
            response = handler(*path[1:])
    except Error404 as e:
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return ["Error 404\n", str(e)]
    except Exception as e:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["Uncaught Exception\n", str(e)]
    else:
        start_response("200 OK", [("Content-Type", type)])
        if jsonify:
            return [json.dumps(response)]
        else:
            return [response]

class Error404(Exception):
    """
    Exception indicating that an 404 error occured.
    """
    def __init__(self, message):
        Exception.__init__(self, message)

# bind some default handlers
import serverutil
handlers["turkic_getworkerstatus"] = \
    (serverutil.getworkerstatus, "text/json", True, False)
handlers["turkic_savejobstats"] = \
    (serverutil.savejobstats, "text/json", True, False)
