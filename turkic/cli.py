"""
A lightweight cli framework.

To use this module, decorate functions with the 'handler' decorator. Then, call
with 'turkic [command] [arguments]' from the shell.
"""

import sys
import database
import argparse
from turkic.api import CommunicationError
from turkic.models import *
from sqlalchemy import func

handlers = {}

def handler(help = "", inname = None):
    """
    Decorator bind a function as a handler for a cli command.

    help    specifies the help message to display
    inname  specifies the name of the handler, otherwise infer
    """
    def decorator(func):
        if inname is None:
            name = func.__name__
        else:
            name = inname
        handlers[name.lower()] = func, help
        return func
    return decorator

class Command(object):
    def __init__(self, args):
        parser = self.setup()
        parser.prog = "turkic {0}".format(sys.argv[1])
        self(parser.parse_args(args))

    def setup(self):
        return argparse.ArgumentParser()

    def __call__(self, args):
        raise NotImplementedError("__call__() must be defined")

class LoadCommand(object):
    def __init__(self, args):
        args = self.setup().parse_args(args)

        title = args.title if args.title else self.title(args)
        description = args.description if args.description else self.description(args)
        cost = args.cost if args.cost is not None else self.cost(args)
        lifetime = args.lifetime if args.lifetime else self.lifetime(args)
        duration = args.duration if args.duration else self.duration(args)
        keywords = args.keywords if args.keywords else self.keywords(args)

        group = HITGroup(title = title,
                        description = description,
                        duration = duration,
                        lifetime = lifetime,
                        cost = cost,
                        bonus = args.bonus,
                        keywords = keywords,
                        donatebonus = args.donate_bonus,
                        perobject = args.per_object,
                        offline = args.offline)

        self(args, group)

    def __call__(self, args, group):
        raise NotImplementedError("__call__() must be defined") 

    def title(self, args):
        raise NotImplementedError()

    def description(self, args):
        raise NotImplementedError()

    def cost(self, args):
        return 0.02

    def lifetime(self, args):
        return 1209600

    def duration(self, args):
        return 600

    def keywords(self, args):
        return ""
        
importparser = argparse.ArgumentParser(add_help=False)
importparser.add_argument("--title", default = None)
importparser.add_argument("--description", default = None)
importparser.add_argument("--cost", "-c", type=float, default = None)
importparser.add_argument("--duration", type=int, default = None)
importparser.add_argument("--lifetime", type=int, default = None)
importparser.add_argument("--keywords", default = None)
importparser.add_argument("--bonus", "-b", type=float, default = 0.00)
importparser.add_argument("--donate-bonus", action="store_true")
importparser.add_argument("--per-object", type=float, default = 0.00)
importparser.add_argument("--offline", action="store_true")

def main(args = None):
    """
    Dispatches the cli command through a given handler.
    """
    if args is None:
        args = sys.argv[1:]
    try:
        args[0]
    except IndexError:
        help()
    else:
        try:
            handler = handlers[args[0]][0]
        except KeyError:
            print "Error: Unknown action {0}".format(args[0])
        else:
            handler(args[1:])

def help(args = None):
    """
    Print the help information.
    """
    for action, (_, help) in sorted(handlers.items()):
        print "{0:>15}   {1:<50}".format(action, help)

class init(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("name")
        return parser

    def __call__(self, args):
        skeleton = os.path.dirname(__file__) + "/skeleton"
        target = os.getcwd() + "/" + args.name

        if os.path.exists(target):
            print "{0} already exists".format(target)
            return

        shutil.copytree(skeleton, target);

        for file in glob.glob(target + "/*.pyc"):
            os.remove(file)

        public = os.path.dirname(__file__) + "/public"
        os.symlink(public, target + "/public/turkic")

        print "Initialized new project: {0}".format(args.name);

class status(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--turk", action = "store_true")
        return parser

    def serverconfig(self, session):
        print "Configuration:"
        print "  Sandbox:     {0}".format("True" if config.sandbox else "False")
        print "  Database:    {0}".format(config.database)
        print "  Localhost:   {0}".format(config.localhost)
        print ""

    def turkstatus(self, session):
        print "Mechanical Turk Status:"
        print "  Balance:     ${0:.2f}".format(api.server.balance)
        print "  Net Payout:  ${0:.2f}".format(api.server.rewardpayout)
        print "  Net Fees:    ${0:.2f}".format(api.server.feepayout)
        print "  Num Created: {0}".format(api.server.numcreated)
        print "  Approved:    {0:.2f}%".format(api.server.approvalpercentage)
        print ""

    def serverstatus(self, session):
        available = session.query(HIT).count()
        published = session.query(HIT).filter(HIT.published == True).count()
        completed = session.query(HIT).filter(HIT.completed == True).count()
        compensated = session.query(HIT).filter(HIT.compensated == True).count()
        remaining = published - completed

        print "Status:"
        print "  Available:   {0}".format(available)
        print "  Published:   {0}".format(published)
        print "  Completed:   {0}".format(completed)
        print "  Compensated: {0}".format(compensated)
        print "  Remaining:   {0}".format(remaining)
        print ""

        if remaining > 0:
            print "Server is ONLINE and accepting work!"
        else:
            if compensated == completed:
                print "Server is offline."
            else:
                print "Server is offline, but some workers are not compensated."
        
    def __call__(self, args):
        session = database.connect()
        try:
            self.serverconfig(session)
            if args.turk:
                self.turkstatus(session)
            self.serverstatus(session)
        finally:
            session.close()

class publish(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--limit", type=int, default = 0)
        parser.add_argument("--disable", action="store_true")
        parser.add_argument("--offline", action="store_true", default = False)
        return parser

    def __call__(self, args):
        session = database.connect()
        try:
            query = session.query(HIT)
            query = query.join(HITGroup)
            query = query.filter(HITGroup.offline == args.offline)
            if args.disable:
                if args.offline:
                    print "Cannot disable offline HITs."
                    return
                query = query.filter(HIT.published == True)
                query = query.filter(HIT.completed == False)
                if args.limit > 0:
                    query = query.limit(args.limit)

                for hit in query:
                    hitid = hit.disable()
                    print "Disabled {0}".format(hitid)
                    session.add(hit)
            else:
                query = query.filter(HIT.published == False)
                if args.limit > 0:
                    query = query.limit(args.limit)

                for hit in query:
                    if args.offline:
                        print hit.offlineurl(config.localhost)
                    else:
                        hit.publish()
                        print "Published {0}".format(hit.hitid)
                        session.add(hit)
                        session.commit()
        finally:
            session.commit()
            session.close()

class compensate(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--bonus", type=float, default = 0.0)
        parser.add_argument("--bonus-reason", default = "Great job!")
        parser.add_argument("--accept", action="append", default = [])
        parser.add_argument("--reject", action="append", default = [])
        parser.add_argument("--validated", action = "store_true")
        parser.add_argument("--default", default="defer",
            choices=["accept", "reject", "defer"])
        return parser

    def process(self, hit, acceptkeys, rejectkeys, validated, default):
        if hit.validated and validated:
            if hit.accepted:
                hit.accept()
            else:
                hit.reject()
        elif hit.assignmentid in acceptkeys:
            hit.accept()
        elif hit.assignmentid in rejectkeys:
            hit.reject()
        elif default == "accept":
            hit.accept()
        elif default == "reject":
            hit.reject()

    def awardbonus(self, hit):
        if hit.accepted:

            if hit.donatebonus or hit.group.donatebonus:
                print "Worker elected to donate bonus."
            else:
                if hit.bonus > 0:
                    hit.awardbonus(hit.bonus, "Great job!")
                    print "Awarded bonus to HIT {0}".format(hit.hitid)
                if hit.group.bonus > 0:
                    hit.awardbonus(hit.group.bonus, "Great job!")
                    print "Awarded bonus to HIT {0}".format(hit.hitid)

            if hit.group.perobject and hit.numobjects > 0:
                hit.awardbonus(hit.group.perobject * hit.numobjects, 
                    "For {0} units of work".format(hit.numobjects))
                print "Compensated HIT {0} for {1} objects".format(
                    hit.hitid, hit.numobjects)

    def __call__(self, args):
        session = database.connect()

        acceptkeys = []
        rejectkeys = []
        for f in args.accept:
            acceptkeys.extend(line.strip() for line in open(f))
        for f in args.reject:
            rejectkeys.extend(line.strip() for line in open(f))
            
        try:
            query = session.query(HIT)
            query = query.filter(HIT.completed == True)
            query = query.filter(HIT.compensated == False)
            query = query.join(HITGroup)
            query = query.filter(HITGroup.offline == False)

            for hit in query:
                try:
                    self.process(hit, acceptkeys, rejectkeys,
                        args.validated, args.default)
                    if hit.compensated:
                        if hit.accepted:
                            print "Accepted HIT {0}".format(hit.hitid)
                            self.awardbonus(hit)
                        else:
                            print "Rejected HIT {0}".format(hit.hitid)
                        self.awardbonus(hit, args.bonus, args.bonus_reason)
                        session.add(hit)
                except CommunicationError as e:
                    print "Error with HIT {0}: {1}".format(hit.hitid, e)
        finally:
            session.commit()
            session.close()

class donation(Command):
    def __call__(self, args):
        session = database.connect()
        try:
            donateyes = session.query(HIT)
            donateyes = donateyes.filter(HIT.donatebonus == True)
            donateyes = donateyes.filter(HIT.completed == True)
            donateyes = donateyes.count()

            donateno = session.query(HIT)
            donateno = donateno.filter(HIT.donatebonus == False)
            donateno = donateno.filter(HIT.completed == True)
            donateno = donateno.count()

            completed = donateyes + donateno
            if completed > 0:
                percentyes = donateyes / float(completed) * 100
                percentno = donateno / float(completed) * 100

                donateamount = session.query(func.sum(HITGroup.bonus))
                donateamount = donateamount.join(HIT)
                donateamount = donateamount.filter(HIT.donatebonus == True)
                donateamount = donateamount.one()[0]
            else:
                percentyes = 0
                percentno = 0
                donateamount = 0

            print "{0:>5} total HITs completed".format(completed)
            print ("{0:>5} times the worker elected for a donation ({1:.0f}%)"
                .format(donateyes, percentyes))
            print ("{0:>5} times the worker elected for a bonus    ({1:.0f}%)"
                .format(donateno, percentno))
            print "${0:>4.2f} total amount donated".format(donateamount)
        finally:
            session.close()

class setup(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--database", action="store_true")
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--no-confirm", action="store_true")
        return parser

    def database(self, args):
        import turkic.models
        import models

        if args.reset:
            if args.no_confirm:
                database.reinstall()
                print "Database reset!"
            else:
                resp = raw_input("Reset database? ").lower()
                if resp in ["yes", "y"]:
                    database.reinstall()
                    print "Database reset!"
                else:
                    print "Aborted. No changes to database."
        else:
            database.install()
            print "Installed new tables, if any."

    def __call__(self, args):
        if args.database:
            self.database(args)

try:
    import config
except ImportError:
    handler("Start a new project")(init)
else:
    handler("Report job status")(status)
    handler("Launch work")(publish)
    handler("Pay workers")(compensate)
    handler("Setup the application")(setup)
    handler("Report status on donations")(donation)
