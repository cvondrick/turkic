import api
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Index, DateTime, Numeric
from sqlalchemy.orm import relationship, backref
import database
import random
import config

class HITGroup(database.Base):
    __tablename__ = "turkic_hit_groups"

    id          = Column(Integer, primary_key = True)
    title       = Column(String(250), nullable = False)
    description = Column(String(250), nullable = False)
    duration    = Column(Integer, nullable = False)
    lifetime    = Column(Integer, nullable = False)
    cost        = Column(Float, nullable = False)
    keywords    = Column(String(250), nullable = False)
    height      = Column(Integer, nullable = False, default = 650)
    bonus       = Column(Float, nullable = False, default = 0.0)
    donatebonus = Column(Boolean, default = False)
    perobject   = Column(Float, nullable = False, default = 0.0)
    offline     = Column(Boolean, default = False)

class Worker(database.Base):
    __tablename__ = "turkic_workers"

    id             = Column(String(14), primary_key = True)
    numsubmitted   = Column(Integer, nullable = False, default = 0)
    numacceptances = Column(Integer, nullable = False, default = 0)
    numrejections  = Column(Integer, nullable = False, default = 0)
    trained        = Column(Boolean, default = False)
    trusted        = Column(Boolean, default = False)
    blocked        = Column(Boolean, default = False)

    def block(self):
        api.server.block(self.id)

    def unblock(self):
        api.server.unblock(self.id)

    def email(self, subject, message):
        api.server.email(self.id, subject, message)

    @classmethod
    def lookup(self, session, workerid):
        worker = session.query(Worker)
        worker = worker.filter(Worker.id == workerid)

        if worker.count() > 0:
            worker = worker.one()
        else:
            worker = Worker(
                id = workerid,
                numsubmitted = 0,
                numacceptances = 0,
                numrejections = 0)
        return worker

class HIT(database.Base):
    __tablename__ = "turkic_hits"

    id            = Column(Integer, primary_key = True)
    hitid         = Column(String(30))
    groupid       = Column(Integer, ForeignKey(HITGroup.id), index = True)
    group         = relationship(HITGroup, cascade = "all", backref = "hits")
    assignmentid  = Column(String(30))
    workerid      = Column(String(14), ForeignKey(Worker.id), index = True)
    worker        = relationship(Worker, cascade = "all", backref = "tasks")
    published     = Column(Boolean, default = False, index = True)
    completed     = Column(Boolean, default = False, index = True)
    compensated   = Column(Boolean, default = False, index = True)
    accepted      = Column(Boolean, default = False, index = True)
    validated     = Column(Boolean, default = False, index = True)
    reason        = Column(Text)
    comments      = Column(Text)
    timeaccepted  = Column(DateTime)
    timecompleted = Column(DateTime)
    timeonserver  = Column(DateTime)
    ipaddress     = Column(String(15))
    bonus         = Column(Numeric, default = 0.0)
    page          = Column(String(250), nullable = False, default = "")
    donatebonus   = Column(Boolean, default = False)
    numobjects    = Column(Integer, default = 0)

    def publish(self):
        resp = api.server.createhit(
            title = self.group.title,
            description = self.group.description,
            amount = self.group.cost,
            duration = self.group.duration,
            lifetime = self.group.lifetime,
            keywords = self.group.keywords,
            height = self.group.height,
            page = self.page
        )
        self.hitid = resp.hitid
        self.published = True

    def markcompleted(self, workerid, assignmentid):
        try:
            workerid.numsubmitted
        except:
            session = database.Session.object_session(self)
            worker = Worker.lookup(session, workerid)
        else:
            worker = workerid
            
        self.completed = True
        self.assignmentid = assignmentid
        self.worker = worker
        self.worker.numsubmitted += 1

    def disable(self):
        if not self.published:
            raise RuntimeError("HIT cannot be disabled because it is not published")
        if self.completed:
            raise RuntimeError("HIT cannot be disabled because it is completed")
        api.server.disable(self.hitid)
        oldhitid = self.hitid
        self.published = False
        self.hitid = None
        return oldhitid

    def accept(self, reason = None, bs = True):
        if not reason:
            if bs:
                reason = random.choice(reasons) 
            else:
                reason = ""

        api.server.accept(self.assignmentid, reason)
        self.accepted = True
        self.compensated = True
        self.worker.numacceptances += 1

    def reject(self, reason = ""):
        api.server.reject(self.assignmentid, reason)
        self.accepted = False
        self.compensated = True
        self.worker.numrejections += 1
    
    def awardbonus(self, amount, reason):
        api.server.bonus(self.workerid, self.assignmentid, amount, reason)

    def offlineurl(self):
        return "{0}{1}&hitId=offline".format(config.localhost, self.page)

reasons = ["Thanks for your hard work!",
          "Excellent work!",
          "Excellent job!",
          "Great work!",
          "Great job!",
          "Fantastic job!",
          "Perfect!",
          "Thank you!",
          "Please keep working!",
          "Your work is helping advance research.",
          "We appreciate your work.",
          "Please keep working.",
          "You are doing an excellent job.",
          "You are doing a great job.",
          "You are doing a superb job.",
          "Keep up the fantastic work!"]
