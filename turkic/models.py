import api
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship, backref
import database

class HITGroup(database.Base):
    __tablename__ = "turkic_hit_groups"

    id          = Column(Integer, primary_key = True)
    title       = Column(String(250), nullable = False)
    description = Column(String(250), nullable = False)
    duration    = Column(Integer, nullable = False)
    lifetime    = Column(Integer, nullable = False)
    cost        = Column(Float, nullable = False)
    keywords    = Column(String(250), nullable = False)

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
        pass

    def unblock(self):
        pass

class HIT(database.Base):
    __tablename__ = "turkic_hits"

    id            = Column(String(30), primary_key = True)
    groupid       = Column(Integer, ForeignKey(HITGroup.id), index = True)
    group         = relationship(HITGroup, cascade = "all", backref = "hits")
    assignmentid  = Column(String(30))
    workerid      = Column(Integer, ForeignKey(Worker.id), index = True)
    worker        = relationship(Worker, cascade = "all", backref = "tasks")
    published     = Column(Boolean, default = False, index = True)
    completed     = Column(Boolean, default = False, index = True)
    compensated   = Column(Boolean, default = False, index = True)
    accepted      = Column(Boolean, default = False, index = True)
    pageurl       = Column(String(250))
    reason        = Column(Text)
    comments      = Column(Text)
    timeaccepted  = Column(DateTime)
    timecompleted = Column(DateTime)

    def publish(self):
        pass

    def accept(self, reason = ""):
        pass

    def reject(self, reason = ""):
        pass
    
    def awardbonus(self, amount, reason):
        pass
