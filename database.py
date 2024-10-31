from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Customer, Vegetable, PremadeBox, Order, OrderItem  

DATABASE_URI = 'mysql+pymysql://root:@localhost/fresh_harvest'  

engine = create_engine(DATABASE_URI, echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

customers = session.query(Customer).all()
for customer in customers:
    print(f"Customer: {customer.name}, Email: {customer.email}")

session.close()
