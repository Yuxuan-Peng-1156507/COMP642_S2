
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

# Database configuration
DATABASE_URI = 'mysql+pymysql://root:zhao1411935907@localhost:3306/fresh_harvest'

engine = create_engine(DATABASE_URI, echo=True)  
Base.metadata.bind = engine

db_session = scoped_session(sessionmaker(bind=engine))
