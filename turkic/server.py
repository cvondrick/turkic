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

try:
    from wsgilog import log as wsgilog
except ImportError:
    def wsgilog(*args, **kwargs):
        return lambda x: x

def handler(type = "json", jsonify = None, post = False, environ = False):
    """
    Decorator to bind a function as a handler in the server software.

    type        specifies the Content-Type header
    jsonify     dumps data in json format if true
    environ     gives handler full control of environ if ture
    """
    type = type.lower()
    if type == "json" and jsonify is None:
        jsonify = True
        type == "text/json"
    def decorator(func):
        handlers[func.__name__] = (func, type, jsonify, post, environ)
        return func
    return decorator

@wsgilog(tostream=True)
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
        handler, type, jsonify, post, passenviron = handlers[action]
    except KeyError:
        start_response("200 OK", [("Content-Type", "text/plain")])
        return action + " in " + ",".join(handlers)
        return ["Error 404\n", "Action {0} undefined.".format(action)]

    try:
        args = path[1:]
        if post:
            postdata = environ["wsgi.input"].read()
            if post == "json":
                args.append(json.loads(postdata))
            else:
                args.append(postdata)
        if passenviron:
            args.append(environ)
        response = handler(*args)
    except Error404 as e:
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return ["Error 404\n", str(e)]
    else:
        start_response("200 OK", [("Content-Type", type)])
        if jsonify:
            return [json.dumps(response)]
        else:
            return response

class Error404(Exception):
    """
    Exception indicating that an 404 error occured.
    """
    def __init__(self, message):
        Exception.__init__(self, message)




import models
import database
from datetime import datetime

def getworkerstats(hitid, workerid):
    """
    Returns the worker status as a dictionary for the server.
    """
    session = database.connect()
    try:
        status = {}

        hit = session.query(models.HIT)
        hit = hit.filter(models.HIT.hitid == hitid)
        hit = hit.one()

        status["reward"] = hit.group.cost
        status["bonus"] = hit.group.bonus
        status["perobject"] = hit.group.perobject
        status["donate"] = hit.group.donatebonus
        
        worker = session.query(models.Worker)
        worker = worker.filter(models.Worker.id == workerid)

        try:
            worker = worker.one()
        except:
            status["newuser"] = True
        else:
            status["newuser"] = False
            status["numaccepted"] = worker.numacceptances
            status["numrejected"] = worker.numrejections
            status["numsubmitted"] = worker.numsubmitted
        return status

    finally:
        session.close()

def savejobstats(hitid, timeaccepted, timecompleted, donate, environ):
    """
    Saves statistics for a job.
    """
    session = database.connect()
    try:
        hit = session.query(models.HIT).filter(models.HIT.hitid == hitid).one()

        hit.timeaccepted = datetime.fromtimestamp(int(timeaccepted) / 1000)
        hit.timecompleted = datetime.fromtimestamp(int(timecompleted) / 1000)
        hit.timeonserver = datetime.now()
        hit.donatebonus = donate

        hit.ipaddress = environ.get("HTTP_X_FORWARDED_FOR", None)
        hit.ipaddress = environ.get("REMOTE_ADDR", hit.ipaddress)

        session.add(hit)
        session.commit()
    finally:
        session.close()

def markcomplete(hitid, assignmentid, workerid):
    """
    Marks a job as complete. Usually this is called right before the
    MTurk form is submitted.
    """
    session = database.connect()
    try:
        hit = session.query(models.HIT).filter(models.HIT.hitid == hitid).one()
        hit.markcompleted(workerid, assignmentid)
        session.add(hit)
        session.commit()
    finally:
        session.close()

handlers["turkic_getworkerstats"] = \
    (getworkerstats, "text/json", True, False, False)
handlers["turkic_savejobstats"] = \
    (savejobstats, "text/json", True, False, True)
handlers["turkic_markcomplete"] = \
    (markcomplete, "text/json", True, False, False)
