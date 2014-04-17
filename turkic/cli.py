"""
A lightweight cli framework.

To use this module, decorate functions with the 'handler' decorator. Then, call
with 'turkic [command] [arguments]' from the shell.
"""

import sys
import database
import argparse
import urllib2
import os
import shutil
import glob
from turkic.api import CommunicationError
from turkic.models import *
from turkic.database import session
from sqlalchemy import func

try:
    import cPickle as pickle
except ImportError:
    import pickle

handlers = {}

def handler(help = "", inname = None):
    """
    Decorator bind a function as a handler for a cli command.

    help    specifies the help message to display
    inname  specifies the name of the handler, otherwise infer
    """
    def decorator(func):
        if inname is None:
            name = func.__name__.replace("_", "-")
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
        minapprovedamount = args.min_approved_amount if args.min_approved_amount else self.minapprovedamount(args)
        minapprovedpercent = args.min_approved_percent if args.min_approved_percent else self.minapprovedpercent(args)
        countrycode = args.only_allow_country

        donation = 0
        if args.donation == "option":
            donation = 1
        elif args.donation == "force":
            donation = 2

        group = HITGroup(title = title,
                         description = description,
                         duration = duration,
                         lifetime = lifetime,
                         cost = cost,
                         keywords = keywords,
                         donation  = donation,
                         offline = args.offline,
                         minapprovedamount = args.min_approved_amount,
                         minapprovedpercent = args.min_approved_percent,
                         countrycode = countrycode)

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

    def minapprovedamount(self, args):
        return 100

    def minapprovedpercent(self, args):
        return 90
        
importparser = argparse.ArgumentParser(add_help=False)
importparser.add_argument("--title", default = None)
importparser.add_argument("--description", default = None)
importparser.add_argument("--cost", "-c", type=float, default = None)
importparser.add_argument("--duration", type=int, default = None)
importparser.add_argument("--lifetime", type=int, default = None)
importparser.add_argument("--keywords", default = None)
importparser.add_argument("--donation",
    choices = ['force', 'option', 'disable'], default = 'disable')
importparser.add_argument("--offline", action="store_true")
importparser.add_argument("--min-approved-percent", type=int)
importparser.add_argument("--min-approved-amount", type=int)
importparser.add_argument("--only-allow-country", default = None)

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
            try:
                handler(args[1:])
            finally:
                if session:
                    session.remove()

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
        parser.add_argument("--verify", action = "store_true")
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
        available = session.query(HIT).filter(HIT.ready == True).count()
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

    def verify(self, session):
        passed = True

        print "Testing access to Amazon Mechanical Turk...",
        try:
            balance = api.server.balance
        except Exception as e:
            print "ERROR!", e
            passed = False
        else:
            print "OK"

        print "Testing access to database server...",
        try:
            count = session.query(HIT).count()
        except Exception as e:
            print "ERROR!", e
            passed = False
        print "OK"

        print "Testing access to web server...",
        try:
            da = urllib2.urlopen(
                    "{0}/turkic/verify.html".format(config.localhost))
            da = da.read().strip()
            if da == "1":
                print "OK"
            else:
                print "ERROR!",
                print "GOT RESPONSE, BUT INVALID"
                print da
                passed = False
        except Exception as e:
            print "ERROR!", e
            passed = False

        print ""
        if passed:
            print "All tests passed!"
        else:
            print "One or more tests FAILED!"

    def __call__(self, args):
        session = database.connect()
        try:
            self.serverconfig(session)
            if args.verify:
                self.verify(session)
            else:
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
            query = query.filter(HIT.ready == True)
            if args.disable:
                if args.offline:
                    print "Cannot disable offline HITs."
                    return
                query = query.filter(HIT.published == True)
                query = query.filter(HIT.completed == False)
                if args.limit > 0:
                    query = query.limit(args.limit)

                for hit in query:
                    try:
                        hitid = hit.disable()
                        print "Disabled {0}".format(hitid)
                    except Exception as e:
                        print "Unable to disable HIT {0}!".format(hit.hitid)
                        print e
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
        parser.add_argument("--warn", action="append", default = [])
        parser.add_argument("--validated", action = "store_true")
        parser.add_argument("--default", default="defer",
            choices=["accept", "reject", "defer", "warn"])
        parser.add_argument("--limit", type=int, default = None)
        return parser

    def process(self, hit, acceptkeys, rejectkeys, warnkeys, validated, default):
        if hit.validated and validated:
            if hit.accepted:
                hit.accept()
            else:
                hit.reject()
        elif hit.assignmentid in acceptkeys:
            hit.accept()
        elif hit.assignmentid in warnkeys:
            hit.warn()
        elif hit.assignmentid in rejectkeys:
            hit.reject()
        elif default == "accept":
            hit.accept()
        elif default == "reject":
            hit.reject()
        elif default == "warn":
            hit.warn()

    def __call__(self, args):
        session = database.connect()

        acceptkeys = []
        rejectkeys = []
        warnkeys = []

        for f in args.accept:
            acceptkeys.extend(line.strip() for line in open(f))
        for f in args.reject:
            rejectkeys.extend(line.strip() for line in open(f))
        for f in args.warn:
            warnkeys.extend(line.strip() for line in open(f))
            
        try:
            query = session.query(HIT)
            query = query.filter(HIT.completed == True)
            query = query.filter(HIT.compensated == False)
            query = query.join(HITGroup)
            query = query.filter(HITGroup.offline == False)

            if args.limit:
                query = query.limit(args.limit)

            for hit in query:
                if not hit.check():
                    print "WARNING: {0} failed payment check, ignoring".format(hit.hitid)
                    continue
                try:
                    self.process(hit, acceptkeys, rejectkeys, warnkeys,
                        args.validated, args.default)
                    if hit.compensated:
                        if hit.accepted:
                            print "Accepted HIT {0}".format(hit.hitid)
                        else:
                            print "Rejected HIT {0}".format(hit.hitid)
                        session.add(hit)
                except CommunicationError as e:
                    hit.compensated = True
                    session.add(hit)
                    print "Error with HIT {0}: {1}".format(hit.hitid, e)
        finally:
            session.commit()
            session.close()

class donation(Command):
    def __call__(self, args):
        hits = session.query(HIT).filter(HIT.donatedamount > 0)
        for hit in hits:
            print hit.workerid, hit.timeonserver, hit.donatedamount

class setup(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--database", action="store_true")
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--public-symlink", action="store_true")
        parser.add_argument("--no-confirm", action="store_true")
        return parser

    def resetdatabase(self):
        #try:
        #    hits = session.query(HIT)
        #    hits = hits.filter(HIT.published == True)
        #    hits = hits.filter(HIT.completed == False)
        #    for hit in hits:
        #        print "Disabled HIT {0}".format(hit.hitid)
        #        hit.disable()
        #except:
        #    print "Failed disabling online HITs. Disable manually with:"
        #    print "\timport config, turkic.api"
        #    print "\tturkic.api.server.purge()"
        database.reinstall()
        print "Database reset!"

    def database(self, args):
        import turkic.models
        import models

        if args.reset:
            if args.no_confirm:
                self.resetdatabase()
            else:
                resp = raw_input("Reset database? ").lower()
                if resp in ["yes", "y"]:
                    self.resetdatabase()
                else:
                    print "Aborted. No changes to database."
        else:
            database.install()
            print "Installed new tables, if any."

    def __call__(self, args):
        if args.public_symlink:
            target = os.getcwd() + "/public/turkic"
            public = os.path.dirname(__file__) + "/public"
            try:
                os.symlink(public, target)
            except OSError:
                print "Could not create symlink!"
            else:
                print "Created symblink {0} to {1}".format(public, target)
                
        if args.database:
            self.database(args)

class invalidate(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("id")
        parser.add_argument("--hit", action = "store_true", default = False)
        parser.add_argument("--no-block", action = "store_true",
                            default = False)
        parser.add_argument("--no-publish", action = "store_true",
                            default = False)
        return parser

    def __call__(self, args):
        query = session.query(HIT)
        query = query.filter(HIT.useful == True)
        if args.hit:
            query = query.filter(HIT.hitid == args.id)
        else:
            worker = session.query(Worker).get(args.id)
            if not worker:
                print "Worker \"{0}\" not found".format(args.id)
                return
            if not args.no_block:
                worker.block("HIT was invalid.")
                print "Blocked worker \"{0}\"".format(args.id)
                session.add(worker)

            query = query.filter(HIT.workerid == args.id)

        for hit in query:
            replacement = hit.invalidate() 
            session.add(hit)
            print "Invalidated {0}".format(hit.hitid)

            if replacement:
                session.add(replacement)
                if not args.no_publish:
                    session.commit()
                    replacement.publish()
                    session.add(replacement)
                    print "Respawned with {0}".format(replacement.hitid)
        session.commit()

class workers(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--load")
        parser.add_argument("--dump")
        parser.add_argument("--block")
        parser.add_argument("--unblock")
        parser.add_argument("--search")
        parser.add_argument("--summary")
        parser.add_argument("--location", action="store_true", default=False)
        return parser

    def __call__(self, args):
        if args.load:
            for data in pickle.load(open(args.load)):
                worker = Worker.lookup(data[0])
                worker.numsubmitted = data[1]
                worker.numacceptances = data[2]
                worker.numrejections = data[3]
                worker.blocked = data[4]
                worker.donatedamount = data[5]
                worker.bonusamount = data[6]
                worker.verified = data[7]
                print "Loaded {0}".format(worker.id)
                session.add(worker)
            session.commit()
        elif args.dump:
            data = []
            for worker in session.query(Worker):
                data.append((worker.id,
                             worker.numsubmitted,
                             worker.numacceptances,
                             worker.numrejections,
                             worker.blocked,
                             worker.donatedamount,
                             worker.bonusamount,
                             worker.verified))
                print "Dumped {0}".format(worker.id)
            pickle.dump(data, open(args.dump, "w"))
        elif args.block:
            worker = Worker.lookup(args.block)
            worker.block("Poor quality work.")
            session.add(worker)
            session.commit()
            print "Blocked {0}".format(args.block)
        elif args.unblock:
            worker = Worker.lookup(args.unblock)
            worker.unblock("Continue working.")
            session.add(worker)
            session.commit()
            print "Unblocked {0}".format(args.unblock)
        elif args.search:
            query = session.query(Worker)
            query = query.filter(Worker.id.like(args.search + "%"))
            if query.count():
                print "Matches:"
                for worker in query:
                    print worker.id
            else:
                print "No matches."
        elif args.summary:
            query = session.query(Worker)
            query = query.filter(Worker.id == args.summary)
            if query.count():
                worker = query.one()
                print "Submitted: {0}".format(worker.numsubmitted)
                print "Accepted: {0}".format(worker.numacceptances)
                print "Rejected: {0}".format(worker.numrejections)
                print "Bonuses: {0}".format(worker.bonusamount)
                print "Donated: {0}".format(worker.donatedamount)
                print "Verified: {0}".format(worker.verified)
                print "Blocked: {0}".format(worker.blocked)
                if args.location:
                    print "Locations: {0}".format(", ".join(set(x.country for x in worker.locations)))
            else:
                print "No matches."
        else:
            workers = session.query(Worker)
            workers = workers.order_by(Worker.numacceptances)
            for worker in workers:
                extra = ""
                if worker.blocked:
                    extra = "BLOCKED"
                if args.location:
                    locs = set(x.country for x in worker.locations)
                    if locs:
                        locs = ", ".join(locs)
                        extra += " " + locs
                extra = extra.strip()
                data = (worker.id,
                        worker.numsubmitted,
                        worker.numacceptances,
                        worker.numrejections,
                        extra)
                print "{0:<15} {1:>5} jobs {2:>5} acc {3:>5} rej     {4}".format(*data)

class email(Command):
    def setup(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("workerid")
        parser.add_argument("subject")
        parser.add_argument("message")
        parser.add_argument("--no-confirm", action="store_true")
        return parser

    def __call__(self, args):
        message = open(args.message).read()

        print "To: {0}".format(args.workerid)
        print "Subject: {0}".format(args.subject)
        print ""
        print message
        print ""

        if not args.no_confirm:
            print ""
            resp = raw_input("Send? ").lower()
            if resp not in ["yes", "y"]:
                print "Aborted!"
                return

        print "Sending..."

        api.server.email(args.workerid, args.subject, message)

        print "Message sent!"

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
    handler("Manage the workers")(workers)
    handler("Invalidates and rewspawn tasks")(invalidate)
    handler("Email a worker")(email)
