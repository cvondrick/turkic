import json

handlers = {}

def handler(type = "json", jsonify = None, raw = False):
    type = type.lower()
    if type == "json" and jsonify is None:
        jsonify = True
        type == "text/json"
    def decorator(func):
        handlers[func.__name__] = (func, type, jsonify, raw)
        return func
    return decorator

import serverutil
handlers["turkic_getworkerstatus"] = (serverutil.getworkerstatus, "text/json", True, False)
handlers["turkic_savejobstats"] = (serverutil.savejobstats, "text/json", True, False)

def application(environ, start_response):
    path = environ.get("PATH_INFO", "").lstrip("/").split("/")

    try:
        action = path[0]
    except IndexError:
        raise Error404("Missing action.")

    try:
        handler, type, jsonify, raw = handlers[action]
    except IndexError:
        raise Error404("Action {0} not defined.".format(action))

    try:
        if raw:
            response = handler(environ)
        else:
            response = handler(*path[1:])
    except Error404 as e:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["Error 404", str(e)]
    except Exception as e:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["Uncaught Exception", str(e)]
    else:
        start_response("200 OK", [("Content-Type", type)])
        if jsonify:
            return [json.dumps(response)]
        else:
            return [response]

class Error404(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
