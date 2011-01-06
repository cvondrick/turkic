import database
import models

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
