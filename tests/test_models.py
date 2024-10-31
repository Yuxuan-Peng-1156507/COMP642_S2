import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from models import Base, Customer, Staff, Vegetable, PremadeBox, Order, OrderItem

# Set up a temporary SQLite database for testing
@pytest.fixture(scope='module')
def db_session():
    engine = create_engine('sqlite:///:memory:')  # In-memory database for tests
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_create_customer(db_session):
    customer = Customer(
        name="Test User",
        email="testuser@example.com",
        password="hashedpassword",
        address="123 Test St",
        account_balance=100.0,
        created_at=datetime.now()
    )
    db_session.add(customer)
    db_session.commit()
    assert customer.id is not None
    assert db_session.query(Customer).count() == 1

def test_create_staff(db_session):
    staff = Staff(
        name="Staff User",
        email="staffuser@example.com",
        password="hashedpassword",
        role="manager",
        created_at=datetime.now()
    )
    db_session.add(staff)
    db_session.commit()
    assert staff.id is not None
    assert db_session.query(Staff).count() == 1

def test_create_vegetable(db_session):
    vegetable = Vegetable(
        name="Carrot",
        price=1.5,
        stock_quantity=100
    )
    db_session.add(vegetable)
    db_session.commit()
    assert vegetable.id is not None
    assert db_session.query(Vegetable).count() == 1

def test_create_order(db_session):
    customer = db_session.query(Customer).first()
    order = Order(
        customer_id=customer.id,
        status="Pending",
        total_amount=50.0,
        order_date=datetime.now(),
        payment_method="credit_card"
    )
    db_session.add(order)
    db_session.commit()
    assert order.id is not None
    assert order.customer_id == customer.id
    assert db_session.query(Order).count() == 1

def test_create_order_item(db_session):
    order = db_session.query(Order).first()
    vegetable = db_session.query(Vegetable).first()
    order_item = OrderItem(
        order_id=order.id,
        product_type="vegetable",
        product_id=vegetable.id,
        quantity=5,
        price=vegetable.price
    )
    db_session.add(order_item)
    db_session.commit()
    assert order_item.id is not None
    assert order_item.order_id == order.id
    assert db_session.query(OrderItem).count() == 1
