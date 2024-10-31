from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

Base = declarative_base()

# Association Table
box_contents = Table('box_contents', Base.metadata,
    Column('box_id', Integer, ForeignKey('premade_box.id')),
    Column('veggie_id', Integer, ForeignKey('veggie.id'))
)

class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    password = Column(String(1000), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    person_type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'person',
        'polymorphic_on': person_type
    }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Staff(Person):
    __tablename__ = 'staff'
    id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    date_joined = Column(DateTime, default=datetime.datetime.now)
    dept_name = Column(String(50))
    list_of_orders = relationship('Order', back_populates='staff')

    __mapper_args__ = {
        'polymorphic_identity': 'staff',
    }


class Customer(Person):
    __tablename__ = 'customer'
    id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    cust_address = Column(String(100), nullable=False)
    cust_balance = Column(Float, default=0.0)
    list_of_orders = relationship('Order', back_populates='customer')
    list_of_payments = relationship('Payment', back_populates='customer')

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }  

    def can_place_order(self, order_amount):
        """
        Check whether customers can place orders, based on their customer type and account balance/credit limit.
        """
        if isinstance(self, PrivateCustomer):
            new_balance = self.cust_balance - order_amount
            # For private customers, the debt cannot exceed max_owing.
            if abs(new_balance) > self.max_owing:
                return False
            else:
                return True
        elif isinstance(self, CorporateCustomer):
            new_balance = self.cust_balance - order_amount
            # For corporate customers, the balance cannot be lower than the credit limit (credit limit = max_credit).
            if abs(new_balance) > self.max_credit:
                return False
            else:
                return True
        else:
            return False


class PrivateCustomer(Customer):
    __tablename__ = 'private_customer'
    id = Column(Integer, ForeignKey('customer.id'), primary_key=True)
    max_owing = Column(Float, default=100.0)

    __mapper_args__ = {
        'polymorphic_identity': 'private_customer',
    }


class CorporateCustomer(Customer):
    __tablename__ = 'corporate_customer'
    id = Column(Integer, ForeignKey('customer.id'), primary_key=True)
    discount_rate = Column(Float, default=0.1)
    max_credit = Column(Float, default=1000.0)

    __mapper_args__ = {
        'polymorphic_identity': 'corporate_customer',
    }


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String(50)) 
    order_lines = relationship('OrderLine', back_populates='item')

    __mapper_args__ = {
        'polymorphic_identity': 'item',
        'polymorphic_on': item_type
    }

    @property
    def display_name(self):
        if isinstance(self, PremadeBox):
            return f"{self.box_size.capitalize()} Box"
        elif isinstance(self, Veggie):
            return self.veg_name
        else:
            return "Unknown Item"

    @property
    def display_price(self):
        if isinstance(self, UnitPriceVeggie):
            return f"${self.price_per_unit} per unit"
        elif isinstance(self, PackVeggie):
            return f"${self.price_per_pack} per pack"
        elif isinstance(self, WeightedVeggie):
            return f"${self.price_per_kilo} per kilo"
        elif isinstance(self, PremadeBox):
            return f"${self.price}"
        else:
            return "$0.00"

class Veggie(Item):
    __tablename__ = 'veggie'
    id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    veg_name = Column(String(50), nullable=False)
    veg_type = Column(String(20), nullable=False)  

    __mapper_args__ = {
        'polymorphic_identity': 'veggie',
    }


class WeightedVeggie(Veggie):
    __tablename__ = 'weighted_veggie'
    id = Column(Integer, ForeignKey('veggie.id'), primary_key=True)
    price_per_kilo = Column(Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'weighted_veggie',
    }


class PackVeggie(Veggie):
    __tablename__ = 'pack_veggie'
    id = Column(Integer, ForeignKey('veggie.id'), primary_key=True)
    pack_size = Column(Integer, nullable=False)
    price_per_pack = Column(Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'pack_veggie',
    }


class UnitPriceVeggie(Veggie):
    __tablename__ = 'unit_price_veggie'
    id = Column(Integer, ForeignKey('veggie.id'), primary_key=True)
    price_per_unit = Column(Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'unit_price_veggie',
    }


class PremadeBox(Item):
    __tablename__ = 'premade_box'
    id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    box_size = Column(String(10), nullable=False) 
    price = Column(Float, nullable=False)
    veggies = relationship('Veggie', secondary=box_contents, backref='boxes')

    def assemble_box(self, db_session):
        if self.box_size == 'small':
            self.veggies = db_session.query(Veggie).limit(3).all()
        elif self.box_size == 'medium':
            self.veggies = db_session.query(Veggie).limit(5).all()
        elif self.box_size == 'large':
            self.veggies = db_session.query(Veggie).limit(7).all()

    __mapper_args__ = {
        'polymorphic_identity': 'premade_box',
    }


class Order(Base):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    order_customer = Column(Integer, ForeignKey('customer.id'))
    customer = relationship('Customer', back_populates='list_of_orders')
    staff_id = Column(Integer, ForeignKey('staff.id'))
    staff = relationship('Staff', back_populates='list_of_orders')
    order_date = Column(DateTime, default=datetime.datetime.now)
    order_number = Column(String(50), unique=True, nullable=False)
    order_status = Column(String(20), default='Pending')
    delivery_option = Column(String(10), nullable=False, default='pickup')
    payment = relationship('Payment', back_populates='order', uselist=False)
    list_of_items = relationship('OrderLine', back_populates='order')


class OrderLine(Base):
    __tablename__ = 'order_line'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'))
    order = relationship('Order', back_populates='list_of_items')
    item_id = Column(Integer, ForeignKey('item.id'))
    item = relationship('Item', back_populates='order_lines')
    item_number = Column(Integer, nullable=False)
    weight = Column(Float) 


class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customer.id'))
    customer = relationship('Customer', back_populates='list_of_payments')
    payment_amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.datetime.now)
    payment_type = Column(String(20), nullable=False) 
    order_id = Column(Integer, ForeignKey('order.id'))
    order = relationship('Order', back_populates='payment')

    __mapper_args__ = {
        'polymorphic_identity': 'account',
        'polymorphic_on': payment_type
    }


class CreditCardPayment(Payment):
    __tablename__ = 'credit_card_payment'
    id = Column(Integer, ForeignKey('payment.id'), primary_key=True)
    card_number = Column(String(20), nullable=False)
    card_expiry_date = Column(String(10), nullable=False)
    card_type = Column(String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'credit_card',
    }


class DebitCardPayment(Payment):
    __tablename__ = 'debit_card_payment'
    id = Column(Integer, ForeignKey('payment.id'), primary_key=True)
    bank_name = Column(String(50), nullable=False)
    debit_card_number = Column(String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'debit_card',
    }

