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
        """
        Generates a database connection.
        """
        return Session()

    def install():
        """
        Installs the database, but does not drop existing tables.
        """
        Base.metadata.create_all(engine)

    def reinstall():
        """
        Reinstalls the database by dropping all existing tables. Actual data is
        not migrated!
        """
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
