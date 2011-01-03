import database
import models

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

def savejobstats(hitid, workerid, assignmentid):
    """
    Saves statistics for a job.
    """
    return True
