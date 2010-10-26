import sys
import cliutil

handlers = {}

def handler(inname = None):
    def decorator(func):
        if inname is None:
            name = func.__name__
        else:
            name = inname
        handlers[name] = func
        return func
    return decorator

def main(args = None):
    if args is None:
        args = sys.argv[1:]

    try:
        args[0]
    except IndexError:
        help()
    else:
        try:
            handler = handlers[args[0]]
        except KeyError:
            print "Error: Unknown action {0}".format(args[0])
        else:
                handler(args[1:])

@handler()
def help(args = None):
    print "Available actions:"
    for action in sorted(handlers.keys()):
        print "  {0}".format(action)


try:
    import config
except ImportError:
    handler()(cliutil.init)
else:
    handler()(cliutil.build)
    handler()(cliutil.progress)
    handler()(cliutil.publish)
    handler()(cliutil.compensate)
