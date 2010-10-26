import config
from turkic.server import handler, application

@handler
def helloworld(name):
    return {"response": "Hello, {0}!".format(name)}
