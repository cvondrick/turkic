"""
A lightweight cli framework.

To use this module, import the 'application function', which will dispatch commands
based on handlers. To define a handler, decorate a function with the 'handler'
decorator.
"""

import sys
import argparse
import cliutil

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
            try:
                handler.setup
            except AttributeError:
                handler(args[1:])
            else:
                handlerinst = handler()
                parser = handlerinst.setup()
                parser.prog = "turkic {0}".format(args[0])
                handlerinst(parser.parse_args(args[1:]))

def help(args = None):
    """
    Print the help information.
    """
    for action, (_, help) in sorted(handlers.items()):
        print "{0:>15}   {1:<50}".format(action, help)

try:
    import config
except ImportError:
    handler("Start a new project")(cliutil.init)
else:
    handler("Report job status")(cliutil.progress)
    handler("Launch work")(cliutil.publish)
    handler("Pay workers")(cliutil.compensate)
    handler("Setup the database")(cliutil.setupdb)
