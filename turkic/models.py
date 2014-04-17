import api
from sqlalchemy import Column, Integer, String, Text, Float, Boolean
from sqlalchemy import ForeignKey, Index, DateTime, Numeric
from sqlalchemy.orm import relationship, backref
import database
import random
import logging
import math
import turkic.geolocation

logger = logging.getLogger("turkic.models")

class HITGroup(database.Base):
    __tablename__ = "turkic_hit_groups"

    id                  = Column(Integer, primary_key = True)
    title               = Column(String(250), nullable = False)
    description         = Column(String(250), nullable = False)
    duration            = Column(Integer, nullable = False)
    lifetime            = Column(Integer, nullable = False)
    cost                = Column(Float, nullable = False)
    keywords            = Column(String(250), nullable = False)
    height              = Column(Integer, nullable = False, default = 650)
    donation            = Column(Integer, default = 0) # 0=off,
                                                       # 1=option,
                                                       # 2=force
    offline             = Column(Boolean, default = False)
    minapprovedamount   = Column(Integer, default = None)
    minapprovedpercent  = Column(Integer, default = None)
    countrycode         = Column(String(10), default = None)

class Worker(database.Base):
    __tablename__ = "turkic_workers"

    id             = Column(String(14), primary_key = True)
    numsubmitted   = Column(Integer, nullable = False, default = 0)
    numacceptances = Column(Integer, nullable = False, default = 0)
    numrejections  = Column(Integer, nullable = False, default = 0)
    blocked        = Column(Boolean, default = False)
    donatedamount  = Column(Float, default = 0.0, nullable = False)
    bonusamount    = Column(Float, default = 0.0, nullable = False)
    verified       = Column(Boolean, default = False)

    def block(self, reason):
        api.server.block(self.id, reason)
        self.blocked = True

    def unblock(self, reason):
        api.server.unblock(self.id, reason)
        self.blocked = False

    def email(self, subject, message):
        api.server.email(self.id, subject, message)

    @classmethod
    def lookup(self, workerid, session = None):
        if not session:
            session = database.session

        worker = session.query(Worker)
        worker = worker.filter(Worker.id == workerid)

        if worker.count() > 0:
            worker = worker.one()
            logger.debug("Found existing worker {0}".format(workerid))
        else:
            worker = Worker(
                id = workerid,
                numsubmitted = 0,
                numacceptances = 0,
                numrejections = 0)
            logger.debug("Created new worker {0}".format(workerid))
        return worker

    @property
    def ips(self):
        return set(x.ipaddress for x in self.tasks)

    @property
    def locations(self):
        locs = [turkic.geolocation.lookup(x) for x in self.ips]
        return [x for x in locs if x]

class HIT(database.Base):
    __tablename__ = "turkic_hits"

    id            = Column(Integer, primary_key = True)
    hitid         = Column(String(30))
    groupid       = Column(Integer, ForeignKey(HITGroup.id), index = True)
    group         = relationship(HITGroup, backref = "hits")
    assignmentid  = Column(String(30))
    workerid      = Column(String(14), ForeignKey(Worker.id), index = True)
    worker        = relationship(Worker, backref = "tasks")
    ready         = Column(Boolean, default = True, index = True)
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
    page          = Column(String(250), nullable = False, default = "")
    opt2donate    = Column(Float, default = 0)
    donatedamount = Column(Float, nullable = False, default = 0.0)
    bonusamount   = Column(Float, nullable = False, default = 0.0)
    useful        = Column(Boolean, default = True)

    discriminator = Column("type", String(250))
    __mapper_args__ = {"polymorphic_on": discriminator,
                       "with_polymorphic": "*"}

    def publish(self):
        if self.published:
            raise RuntimeError("HIT cannot be published because it has already"
                " been published.")
        resp = api.server.createhit(
            title = self.group.title,
            description = self.group.description,
            amount = self.group.cost,
            duration = self.group.duration,
            lifetime = self.group.lifetime,
            keywords = self.group.keywords,
            height = self.group.height,
            minapprovedamount = self.group.minapprovedamount,
            minapprovedpercent = self.group.minapprovedpercent,
            countrycode = self.group.countrycode,
            page = self.getpage())
        self.hitid = resp.hitid
        self.published = True
        logger.debug("Published HIT {0}".format(self.hitid))

    def getpage(self):
        raise NotImplementedError()

    def markcompleted(self, workerid, assignmentid):
        try:
            workerid.numsubmitted
        except:
            session = database.Session.object_session(self)
            worker = Worker.lookup(workerid, session)
        else:
            worker = workerid
            
        self.completed = True
        self.assignmentid = assignmentid
        self.worker = worker
        self.worker.numsubmitted += 1

        logger.debug("HIT {0} marked complete".format(self.hitid))

    def disable(self):
        if not self.published:
            raise RuntimeError("HIT cannot be disabled because "
                               "it is not published")
        if self.completed:
            raise RuntimeError("HIT cannot be disabled because "
                               "it is completed")
        api.server.disable(self.hitid)
        oldhitid = self.hitid
        self.published = False
        self.hitid = None
        logger.debug("HIT (was {0}) disabled".format(oldhitid))
        return oldhitid

    def accept(self, reason = None, bs = True):
        if not reason:
            if bs:
                reason = random.choice(reasons) 
            else:
                reason = ""

        for schedule in self.group.schedules:
            schedule.award(self)

        if self.donatedamount > 0:
            reason = (reason + " For this HIT, we have donated ${0:>4.2f} to "
            "the World Food Programme on your behalf. Thank you for your "
            "support!".format(self.donatedamount))

        api.server.accept(self.assignmentid, reason)
        self.accepted = True
        self.compensated = True
        self.worker.numacceptances += 1

        logger.debug("Accepted work for HIT {0}".format(self.hitid))

    def warn(self, reason = None):
        if not reason:
            reason = ("Warning: we will start REJECTING your work soon if you"
            "do not improve your quality. Please reread the instructions.")
        api.server.accept(self.assignmentid, reason)
        self.accepted = True
        self.compensated = True
        self.worker.numacceptances += 1

        logger.debug("Accepted, but warned for HIT {0}".format(self.hitid))

    def reject(self, reason = ""):
        try:
          api.server.reject(self.assignmentid, reason)
        except:
          print "Failed to reject {0}".format(self.assignmentid)
        self.accepted = False
        self.compensated = True
        self.worker.numrejections += 1

        logger.debug("Rejected work for HIT {0}".format(self.hitid))

    def check(self):
        return True
    
    def awardbonus(self, amount, reason = None, bs = True):
        self.donatedamount += amount * self.opt2donate
        self.worker.donatedamount += amount * self.opt2donate

        amount = math.floor(amount * (1 - self.opt2donate) * 100) / 100

        if amount > 0:
            logger.debug("Awarding bonus of {0} on HIT {1}"
                            .format(amount, self.hitid))
            self.bonusamount += amount 
            self.worker.bonusamount += amount 
            if not reason:
                if bs:
                    reason = random.choice(reasons)
                else:
                    reason = ""
            api.server.bonus(self.workerid, self.assignmentid, amount, reason)

    def offlineurl(self, localhost):
        return "{0}{1}&hitId=offline".format(localhost, self.getpage())

    def invalidate(self):
        raise NotImplementedError("Subclass must implement 'invalid()'")

class EventLog(database.Base):
    __tablename__ = "turkic_event_log"

    id        = Column(Integer, primary_key = True)
    hitid     = Column(Integer, ForeignKey(HIT.id), index = True)
    hit       = relationship(HIT, cascade = "all", backref = "hits")
    domain    = Column(Text)
    message   = Column(Text)
    timestamp = Column(DateTime)

class BonusSchedule(database.Base):
    __tablename__ = "turkic_bonus_schedules"

    id = Column(Integer, primary_key = True)
    groupid = Column(Integer, ForeignKey(HITGroup.id))
    group = relationship(HITGroup, backref = "schedules")
    discriminator = Column('type', String(250))
    __mapper_args__ = {'polymorphic_on': discriminator}

    def award(self, hit):
        raise NotImplementedError()

    def description(self):
        raise NotImplementedError()

class ConstantBonus(BonusSchedule):
    __tablename__ = "turkic_bonus_schedule_constant"
    __maper_args__ = {"polymorphic_identity": "turkic_constant"}

    id = Column(Integer, ForeignKey(BonusSchedule.id), primary_key = True)
    amount = Column(Float, nullable = False)

    def award(self, hit):
        hit.awardbonus(self.amount, "For completing the task.")
        return self.amount

    def description(self):
        return (self.amount, "bonus")

reasons = [""]
#reasons = ["Thanks for your hard work!",
#           "Excellent work!",
#           "Excellent job!",
#           "Great work!",
#           "Great job!",
#           "Fantastic job!",
#           "Perfect!",
#           "Thank you!",
#           "Please keep working!",
#           "Your work is helping advance research.",
#           "We appreciate your work.",
#           "Please keep working.",
#           "You are doing an excellent job.",
#           "You are doing a great job.",
#           "You are doing a superb job.",
#           "Keep up the fantastic work!"]
