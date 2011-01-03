"""
A lightweight cli framework.

To use this module, import the 'application function', which will dispatch commands
based on handlers. To define a handler, decorate a function with the 'handler'
decorator.
"""

import sys
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
        handlers[name] = func, help
        return func
    return decorator

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

try:
    import config
except ImportError:
    handler("Start a new project")(cliutil.init)
else:
    handler("Prepare for deployment.")(cliutil.build)
    handler("Report job status")(cliutil.progress)
    handler("Launch work")(cliutil.publish)
    handler("Pay workers")(cliutil.compensate)
