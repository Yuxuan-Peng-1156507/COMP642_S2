import pytest
from app import app, db_session, Customer, Staff, Order, OrderItem, Vegetable, PremadeBox
from werkzeug.security import generate_password_hash
from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'

    with app.test_client() as client:
        with app.app_context():
            try:
                # Disable foreign key checks to allow clean deletion
                db_session.execute(text('SET FOREIGN_KEY_CHECKS=0;'))
                db_session.commit()

                # Clean up the database, first delete the relevant order items, then delete the related orders, customers and employees
                db_session.query(OrderItem).delete()
                db_session.query(Order).delete()
                db_session.query(Customer).delete()
                db_session.query(Staff).delete()
                db_session.query(Vegetable).delete()
                db_session.query(PremadeBox).delete()
                db_session.commit()

                # Enable foreign key checks after cleanup
                db_session.execute(text('SET FOREIGN_KEY_CHECKS=1;'))
                db_session.commit()

                # add a customer, staff, and vegetable
                test_customer = Customer(
                    name="Test Customer",
                    email="testcustomer@example.com",
                    password=generate_password_hash("password"),
                    address="123 Test St",
                    account_balance=50.0
                )
                db_session.add(test_customer)

                test_staff = Staff(
                    name="Test Staff",
                    email="teststaff@example.com",
                    password=generate_password_hash("password"),
                    role="staff"
                )
                db_session.add(test_staff)

                test_vegetable = Vegetable(
                    id=1,  # Explicitly set ID to 1 for consistency with the test
                    name="Carrot",
                    price_per_kg=2.5,
                    stock_quantity=100
                )
                db_session.add(test_vegetable)
                db_session.commit()
            except IntegrityError as e:
                db_session.rollback()
                raise e
            except Exception as e:
                db_session.rollback()
                raise e

        yield client

# Test whether the home page returns normally
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Home" in response.data

# login test
def test_customer_login(client):
    response = client.post('/login', json={
        'email': 'testcustomer@example.com',
        'password': 'password',
        'user_type': 'customer'
    })
    assert response.status_code == 302

def test_staff_login(client):
    response = client.post('/login', json={
        'email': 'teststaff@example.com',
        'password': 'password',
        'user_type': 'staff'
    })
    assert response.status_code == 302

# register test
def test_register(client):
    response = client.post('/register', data={
        'name': 'New Customer',
        'email': 'newcustomer@example.com',
        'password': 'newpassword',
        'address': '456 New St'
    })
    assert response.status_code == 302

# customer dashboard
def test_customer_dashboard(client):
    response = client.post('/login', json={
        'email': 'testcustomer@example.com',
        'password': 'password',
        'user_type': 'customer'
    })
    assert response.status_code == 302

    response = client.get('/customer_dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b"Customer Dashboard" in response.data

# customer view orders
def test_view_orders(client):
    response = client.post('/login', json={
        'email': 'testcustomer@example.com',
        'password': 'password',
        'user_type': 'customer'
    })
    assert response.status_code == 302

    with client.session_transaction() as session:
        session['customer_id'] = 1

    response = client.get('/view_orders')
    assert response.status_code == 200
    assert b"Orders" in response.data

# view vegetables
def test_get_vegetables(client):
    response = client.post('/login', json={
        'email': 'testcustomer@example.com',
        'password': 'password',
        'user_type': 'customer'
    })
    assert response.status_code == 302

    response = client.get('/vegetables', follow_redirects=True)
    assert response.status_code == 200
    assert b"Vegetables" in response.data

# view premade boxes
def test_view_premade_boxes(client):
    response = client.post('/login', json={
        'email': 'testcustomer@example.com',
        'password': 'password',
        'user_type': 'customer'
    })
    assert response.status_code == 302

    response = client.get('/view_premade_boxes', follow_redirects=True)
    assert response.status_code == 200
    assert b"Premade Boxes" in response.data

# create premade box
def test_create_premade_box(client):
    response = client.post('/login', json={
        'email': 'testcustomer@example.com',
        'password': 'password',
        'user_type': 'customer'
    })
    assert response.status_code == 302

    with client.session_transaction() as session:
        session['customer_id'] = 1

    response = client.post('/create_premade_box', data={
        'size': 'small',
        'vegetable_ids': [1],
        'weight_1': 1.0
    }, follow_redirects=True)
    assert response.status_code == 200 or response.status_code == 302
    assert b"Cart" in response.data or b"Create Your Custom Premade Box" in response.data


