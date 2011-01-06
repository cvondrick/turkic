import database
import models

from datetime import datetime

def getworkerstatus(workerid):
    """
    Returns the worker status as a dictionary for the server.
    """
    session = database.connect()
    try:
        worker = session.query(models.Worker)
        worker = worker.filter(models.Worker.id == workerid)

        status = {}
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

def savejobstats(hitid, timeaccepted, timecompleted, environ):
    """
    Saves statistics for a job.
    """
    session = database.connect()
    try:
        hit = session.query(models.HIT).filter(models.HIT.hitid == hitid).one()

        hit.timeaccepted = datetime.fromtimestamp(int(timeaccepted) / 1000)
        hit.timecompleted = datetime.fromtimestamp(int(timecompleted) / 1000)
        hit.timeonserver = datetime.now()

        hit.ipaddress = environ.get("HTTP_X_FORWARDED_FOR", None)
        hit.ipaddress = environ.get("REMOTE_ADDR", hit.ipaddress)

        session.add(hit)
        session.commit()
    finally:
        session.close()
