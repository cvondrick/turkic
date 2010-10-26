from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

Base = declarative_base()

try:
    import config
except ImportError:
    pass
else:
    engine = create_engine(config.database)
    Session = sessionmaker(bind=engine)

    def connect():
        return Session()

    def install():
        Base.metadata.create_all(engine)

    def reinstall():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)


