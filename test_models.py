import pytest
from app import app
from models import (
    Base, Person, Staff, Customer, PrivateCustomer, CorporateCustomer,
    Veggie, WeightedVeggie, PackVeggie, UnitPriceVeggie,
    PremadeBox, Order, OrderLine, Payment, CreditCardPayment,
    DebitCardPayment
)
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///:memory:')
Session = sessionmaker(bind=engine)

@pytest.fixture(scope='module')
def db_session():
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_person_model(db_session):
# Test creation of Person object
    person = Person(
        first_name='Test',
        last_name='User',
        username='testuser',
        person_type='person'
    )
    person.set_password('password123')
    db_session.add(person)
    db_session.commit()

    retrieved_person = db_session.query(Person).filter_by(username='testuser').first()
    assert retrieved_person is not None
    assert retrieved_person.check_password('password123') == True

def test_staff_model(db_session):
# Test creation of Staff object
    staff = Staff(
        first_name='Staff',
        last_name='Member',
        username='staffmember',
        dept_name='Sales',
        date_joined=datetime.datetime.now()
    )
    staff.set_password('password123')
    db_session.add(staff)
    db_session.commit()

    retrieved_staff = db_session.query(Staff).filter_by(username='staffmember').first()
    assert retrieved_staff is not None
    assert retrieved_staff.dept_name == 'Sales'
    assert retrieved_staff.check_password('password123') == True

def test_private_customer_model(db_session):
# Test creation of PrivateCustomer object
    private_customer = PrivateCustomer(
        first_name='Private',
        last_name='Customer',
        username='privatecustomer',
        cust_address='123 Main St',
        max_owing=100.0
    )
    private_customer.set_password('password123')
    db_session.add(private_customer)
    db_session.commit()

    retrieved_customer = db_session.query(PrivateCustomer).filter_by(username='privatecustomer').first()
    assert retrieved_customer is not None
    assert retrieved_customer.cust_address == '123 Main St'
    assert retrieved_customer.max_owing == 100.0
    assert retrieved_customer.check_password('password123') == True

def test_corporate_customer_model(db_session):
# Test creation of CorporateCustomer object
    corporate_customer = CorporateCustomer(
        first_name='Corporate',
        last_name='Customer',
        username='corporatecustomer',
        cust_address='456 Corporate Ave',
        max_credit=1000.0,
        discount_rate=0.1
    )
    corporate_customer.set_password('password123')
    db_session.add(corporate_customer)
    db_session.commit()

    retrieved_customer = db_session.query(CorporateCustomer).filter_by(username='corporatecustomer').first()
    assert retrieved_customer is not None
    assert retrieved_customer.cust_address == '456 Corporate Ave'
    assert retrieved_customer.max_credit == 1000.0
    assert retrieved_customer.discount_rate == 0.1
    assert retrieved_customer.check_password('password123') == True

def test_veggie_models(db_session):
# Test creating various Veggie objects
    weighted_veggie = WeightedVeggie(
        veg_name='Carrot',
        veg_type='weighted',
        price_per_kilo=2.5
    )
    pack_veggie = PackVeggie(
        veg_name='Spinach',
        veg_type='pack',
        pack_size=1,
        price_per_pack=3.0
    )
    unit_price_veggie = UnitPriceVeggie(
        veg_name='Tomato',
        veg_type='unit_price',
        price_per_unit=0.5
    )
    db_session.add_all([weighted_veggie, pack_veggie, unit_price_veggie])
    db_session.commit()

    retrieved_weighted = db_session.query(WeightedVeggie).filter_by(veg_name='Carrot').first()
    assert retrieved_weighted is not None
    assert retrieved_weighted.price_per_kilo == 2.5

    retrieved_pack = db_session.query(PackVeggie).filter_by(veg_name='Spinach').first()
    assert retrieved_pack is not None
    assert retrieved_pack.price_per_pack == 3.0

    retrieved_unit_price = db_session.query(UnitPriceVeggie).filter_by(veg_name='Tomato').first()
    assert retrieved_unit_price is not None
    assert retrieved_unit_price.price_per_unit == 0.5

def test_premade_box_model(db_session):
    small_box = PremadeBox(
        box_size='small',
        price=15.0
    )
    db_session.add(small_box)
    db_session.commit()

# Testing the assemble_box method
    small_box.assemble_box(db_session)
    db_session.commit()

    retrieved_box = db_session.query(PremadeBox).filter_by(box_size='small').first()
    assert retrieved_box is not None
    assert len(retrieved_box.veggies) == 3  # small box should have 3 kinds of vegetables

def test_order_model(db_session):
# Create customers and products
    customer = PrivateCustomer(
        first_name='Order',
        last_name='Tester',
        username='ordertester',
        cust_address='789 Test Blvd',
        max_owing=100.0
    )
    customer.set_password('password123')
    db_session.add(customer)

    veggie = UnitPriceVeggie(
        veg_name='Cucumber',
        veg_type='unit_price',
        price_per_unit=0.3
    )
    db_session.add(veggie)
    db_session.commit()

# Create an order
    order = Order(
        customer=customer,
        order_number='ORD123',
        delivery_option='delivery'
    )
    db_session.add(order)
    db_session.commit()

# Create an order line
    order_line = OrderLine(
        order=order,
        item=veggie,
        item_number=10
    )
    db_session.add(order_line)
    db_session.commit()

    retrieved_order = db_session.query(Order).filter_by(order_number='ORD123').first()
    assert retrieved_order is not None
    assert retrieved_order.customer.username == 'ordertester'
    assert len(retrieved_order.list_of_items) == 1
    assert retrieved_order.list_of_items[0].item.veg_name == 'Cucumber'

def test_payment_models(db_session):
    customer = PrivateCustomer(
        first_name='Payment',
        last_name='Tester',
        username='paymenttester',
        cust_address='101 Payment St',
        max_owing=100.0
    )
    customer.set_password('password123')
    db_session.add(customer)
    db_session.commit()

# Create a payment object
    payment = Payment(
        customer=customer,
        payment_amount=50.0,
        payment_type='account'
    )
    db_session.add(payment)
    db_session.commit()

    retrieved_payment = db_session.query(Payment).filter_by(customer_id=customer.id).first()
    assert retrieved_payment is not None
    assert retrieved_payment.payment_amount == 50.0
    assert retrieved_payment.payment_type == 'account'

# Create a credit card payment object
    cc_payment = CreditCardPayment(
        customer=customer,
        payment_amount=75.0,
        payment_type='credit_card',
        card_number='1234567890123456',
        card_expiry_date='12/25',
        card_type='Visa'
    )
    db_session.add(cc_payment)
    db_session.commit()

    retrieved_cc_payment = db_session.query(CreditCardPayment).filter_by(card_number='1234567890123456').first()
    assert retrieved_cc_payment is not None
    assert retrieved_cc_payment.payment_amount == 75.0
    assert retrieved_cc_payment.card_type == 'Visa'

def test_customer_can_place_order(db_session):
    private_customer = PrivateCustomer(
        first_name='Limit',
        last_name='Tester',
        username='limittester',
        cust_address='202 Limit Rd',
        max_owing=100.0,
        cust_balance=0.0
    )
    private_customer.set_password('password123')
    db_session.add(private_customer)
    db_session.commit()

# Test that the order amount is within the limit
    assert private_customer.can_place_order(50.0) == True

# Test that the order amount exceeds the limit
    assert private_customer.can_place_order(150.0) == False

    corporate_customer = CorporateCustomer(
        first_name='Corp',
        last_name='Tester',
        username='corptester',
        cust_address='303 Corp Ave',
        max_credit=1000.0,
        discount_rate=0.1,
        cust_balance=0.0
    )
    corporate_customer.set_password('password123')
    db_session.add(corporate_customer)
    db_session.commit()

# Test that the order amount is within the credit limit
    assert corporate_customer.can_place_order(800.0) == True

# Test that the order amount exceeds the credit limit
    assert corporate_customer.can_place_order(1200.0) == False
