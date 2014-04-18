"""
Use to connect to the configured database.

>>> from turkic.database import session, Base
>>> class Mymodel(Base):
...     pass
>>> session.query(MyModel).spam()
>>> session.add(mymodel)
>>> session.commit()
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import reflection
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
    )
import logging

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

logger = logging.getLogger("turkic.database")

Base = declarative_base()

try:
    import config
except ImportError:
    session = None
    Session = None
else:
    engine = create_engine(config.database, pool_recycle = 3600)

    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)

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
        dropall()
        Base.metadata.create_all(engine)

    def dropall():
        """
        Drops all constraints, then all tables.
        """
        inspector = reflection.Inspector.from_engine(engine)
        metadata = MetaData()

        tbs = []
        all_fks = []

        for table_name in inspector.get_table_names():
            fks = []
            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append(
                    ForeignKeyConstraint((),(),name=fk['name'])
                    )
            t = Table(table_name,metadata,*fks)
            tbs.append(t)
            all_fks.extend(fks)

        for fkc in all_fks:
            session.execute(DropConstraint(fkc))

        for table in tbs:
            session.execute(DropTable(table))
