import database
import models

def getworkerstatus(workerid):
    session = database.connect()
    try:

        worker = session.query(models.Worker)
        worker = worker.filter(models.Worker.id == workerid)
        worker = worker.one()

        status = {}
        status["numaccepted"] = worker.numaccepted
        status["numrejected"] = worker.numrejected
        status["numsubmitted"] = worker.numsubmitted
        status["trained"] = worker.trained
        return status

    finally:
        session.close()

def savejobstats(hitid, workerid, assignmentid):
    return True
