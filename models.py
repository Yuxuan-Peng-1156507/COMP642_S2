from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Table, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Column, Boolean


Base = declarative_base()

# Association table for many-to-many relationship between PremadeBox and Vegetable
premade_box_vegetable = Table(
    'premade_box_vegetable',
    Base.metadata,
    Column('premade_box_id', Integer, ForeignKey('premade_boxes.id'), primary_key=True),
    Column('vegetable_id', Integer, ForeignKey('vegetables.id'), primary_key=True),
    Column('weight', Float, nullable=False)  
)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    address = Column(String(255))
    account_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship('Order', back_populates='customer')

class Staff(Base):
    __tablename__ = 'staff'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Vegetable(Base):
    __tablename__ = 'vegetables'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    price_per_kg = Column(Float, nullable=False)
    stock_quantity = Column(Float, default=0.0) 

    boxes = relationship('PremadeBox', secondary=premade_box_vegetable, back_populates='contents')

class PremadeBox(Base):
    __tablename__ = 'premade_boxes'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    size = Column(String(50), nullable=False)
    max_weight = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    price = Column(Float, nullable=False)  
    description = Column(String(255))
    is_default = Column(Boolean, default=False)
    contents = relationship('Vegetable', secondary=premade_box_vegetable, back_populates='boxes')

    def calculate_price(self, db_session):
        total_weight = sum(
            assoc.weight for assoc in db_session.query(premade_box_vegetable).filter_by(premade_box_id=self.id)
        )
        if total_weight > self.max_weight:
            raise ValueError("Total weight exceeds the box's capacity")

        total_price = sum(
            vegetable.price_per_kg * assoc.weight
            for vegetable, assoc in db_session.query(Vegetable, premade_box_vegetable).filter(
                premade_box_vegetable.c.premade_box_id == self.id,
                premade_box_vegetable.c.vegetable_id == Vegetable.id
            )
        )
        return self.base_price + total_price
    



class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default='Pending')
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    delivery_method = Column(Enum('pickup', 'delivery', 'pending', name='delivery_method_enum'))
    delivery_fee = Column(Float, default=0.0)
    delivery_address = Column(String(255), nullable=True)

    customer = relationship('Customer', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')

    def calculate_total_amount(self):
        item_total = sum(item.price * item.quantity for item in self.items)
        self.total_amount = item_total + (self.delivery_fee if self.delivery_method == 'delivery' else 0.0)

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_type = Column(Enum('vegetable', 'premade_box'), nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Float, nullable=False)  
    price = Column(Float, nullable=False)

    order = relationship('Order', back_populates='items')

# Database configuration
DATABASE_URI = 'mysql+pymysql://root:@localhost/fresh_harvest' 
engine = create_engine(DATABASE_URI, echo=True)
Base.metadata.create_all(engine)
