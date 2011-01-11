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
        self(self.setup().parse_args(args))

    def setup(self):
        return argparse.ArgumentParser()

    def __call__(self, args):
        raise NotImplementedError("__call__() must be defined")

class LoadCommand(object):
    def __init__(self, args):
        args = self.setup().parse_args(args)
        group = HITGroup(title = args.title.format(c = args.plural),
                        description = args.description.format(c = args.plural),
                        duration = args.duration,
                        lifetime = args.lifetime,
                        cost = args.cost,
                        bonus = args.bonus,
                        keywords = args.keywords)
        self(args, group)

    def __call__(self, args, group):
        raise NotImplementedError("__call__() must be defined") 

importparser = argparse.ArgumentParser(add_help=False)
importparser.add_argument("--title", default = "Image annotation of {c}")
importparser.add_argument("--description", 
    default = "Draw boxes around {c} in this image.")
importparser.add_argument("--cost", "-c", type=float, default = 0.02)
importparser.add_argument("--duration", type=int, default = 600)
importparser.add_argument("--lifetime", type=int, default = 1209600)
importparser.add_argument("--keywords", default = "")
importparser.add_argument("--bonus", "-b", type=float, default = 0.00)

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

        print "Status:"
        print "  Available:   {0}".format(available)
        print "  Published:   {0}".format(published)
        print "  Completed:   {0}".format(completed)
        print "  Compensated: {0}".format(compensated)
        print "  Remaining:   {0}".format(published - completed)
        
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
        return parser

    def publish(self, hit):
        hit.publish()
        print "Published {0}".format(hit.hitid)

    def disable(self, hit):
        hitid = hit.disable()
        print "Disabled {0}".format(hitid)

    def __call__(self, args):
        session = database.connect()
        try:
            query = session.query(HIT)
            if args.disable:
                query = query.filter(HIT.published == True)
                query = query.filter(HIT.completed == False)
                if args.limit > 0:
                    query = query.limit(args.limit)

                for hit in query:
                    self.disable(hit)
                    session.add(hit)
            else:
                query = query.filter(HIT.published == False)
                if args.limit > 0:
                    query = query.limit(args.limit)

                for hit in query:
                    self.publish(hit)
                    session.add(hit)
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

    def awardbonus(self, hit, bonus, bonus_reason):
        if hit.accepted:
            print "Accepted HIT {0}".format(hit.hitid)
            if bonus > 0:
                hit.awardbonus(bonus, bonus_reason)
                print "Awarded bonus to HIT {0}".format(hit.hitid)
            if hit.group.bonus > 0:
                hit.awardbonus(hit.group.bonus, "Great job!")
                print "Awarded bonus to HIT {0}".format(hit.hitid)
        else:
            print "Rejected HIT {0}".format(hit.hitid)

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

            for hit in query:
                try:
                    self.process(hit, acceptkeys, rejectkeys,
                        args.validated, args.default)
                    if hit.compensated:
                        self.awardbonus(hit, args.bonus, args.bonus_reason)
                        session.add(hit)
                except CommunicationError as e:
                    print "Error with HIT {0}: {1}".format(hit.hitid, e)
        finally:
            session.commit()
            session.close()

class setupdb(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--no-confirm", action="store_true")
        return parser

    def __call__(self, args):
        import models
        import turkic.models

        if args.reset:
            if rgs.no_confirm:
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

try:
    import config
except ImportError:
    handler("Start a new project")(init)
else:
    handler("Report job status")(status)
    handler("Launch work")(publish)
    handler("Pay workers")(compensate)
    handler("Setup the database")(setupdb)
