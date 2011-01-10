import os
import shutil
import api
import glob
import database
import optparse

try:
    import config
except ImportError:
    pass

from turkic.models import *

def init(args):
    try:
        args[0]
    except IndexError:
        print "Error: Expected argument."
        return

    skeleton = os.path.dirname(__file__) + "/skeleton"
    target = os.getcwd() + "/" + args[0]

    if os.path.exists(target):
        print "{0} already exists".format(target)
        return

    shutil.copytree(skeleton, target);

    for file in glob.glob(target + "/*.pyc"):
        os.remove(file)

    public = os.path.dirname(__file__) + "/public"
    os.symlink(public, target + "/public/turkic")

    print "Initialized new project: {0}".format(args[0]);

def progress(args):
    session = database.connect()
    balance = api.server.balance

    try:
        available = session.query(HIT).count()
        published = session.query(HIT).filter(HIT.published == True).count()
        completed = session.query(HIT).filter(HIT.completed == True).count()
        compensated = session.query(HIT).filter(HIT.compensated == True).count()

        print "Server Configuration:"
        print "  Sandbox:     {0}".format("True" if config.sandbox else "False")
        print "  Database:    {0}".format(config.database)
        print "  Localhost:   {0}".format(config.localhost)
        print ""

        print "Mechanical Turk Status:"
        print "  Balance:     ${0:.2f}".format(balance)
        print ""

        print "Server Status:"
        print "  Available:   {0}".format(available)
        print "  Published:   {0}".format(published)
        print "  Completed:   {0}".format(completed)
        print "  Remaining:   {0}".format(published - completed)
        print "  Compensated: {0}".format(compensated)

    finally:
        session.close()

def publish(args):
    session = database.connect()

    try:
        query = session.query(HIT)
        query = query.filter(HIT.published == False)

        for hit in query:
            hit.publish()
            session.add(hit)
            print "Published {0}".format(hit.hitid)

    finally:
        session.commit()
        session.close()

def compensate(args):
    parser = optparse.OptionParser(optparse.SUPPRESS_USAGE)
    parser.add_option("--bonus", action="store", type="float", default = 0.0)
    parser.add_option("--bonus-reason", action="store", type="str", default="Great job!")
    parser.add_option("--accept", action="append", default = [])
    parser.add_option("--reject", action="append", default = [])
    parser.add_option("--validated", action="store_true", default = False)
    parser.add_option("--default", action="store", choices=["accept", "reject", "defer"], default="defer")
    options, arguments = parser.parse_args(args)

    session = database.connect()

    acceptkeys = []
    rejectkeys = []
    for f in options.accept:
        acceptkeys.extend(line.strip() for line in open(f))
    for f in options.reject:
        rejectkeys.extend(line.strip() for line in open(f))
        
    try:
        query = session.query(HIT)
        query = query.filter(HIT.completed == True)
        query = query.filter(HIT.compensated == False)

        for hit in query:
            if hit.validated and options.validated:
                if hit.accepted:
                    hit.accept()
                else:
                    hit.reject()
            elif hit.assignmentid in acceptkeys:
                hit.accept()
            elif hit.assignmentid in rejectkeys:
                hit.reject()
            elif options.default == "accept":
                hit.accept()
            elif options.default == "reject":
                hit.reject()

            if hit.compensated:
                if hit.accepted:
                    print "Accepted HIT {0}".format(hit.hitid)
                    if options.bonus > 0:
                        hit.awardbonus(options.bonus, options.bonus_reason)
                        print "Awarded bonus to HIT {0}".format(hit.hitid)
                    if hit.group.bonus > 0:
                        hit.awardbonus(hit.group.bonus, "Great job!")
                        print "Awarded bonus to HIT {0}".format(hit.hitid)
                else:
                    print "Rejected HIT {0}".format(hit.hitid)
                session.add(hit)
    finally:
        session.commit()
        session.close()

def setupdb(args):
    import models
    import turkic.models

    if "--reset" in args:
        if "--no-confirm" in args:
            database.reinstall()
            print "Reinstalled."
        else:
            resp = raw_input("Reset database? ").lower()
            if resp in ["yes", "y"]:
                database.reinstall()
                print "Reinstalled."
            else:
                print "Aborted."
    else:
        database.install()
        print "Installed."
