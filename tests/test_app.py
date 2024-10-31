import pytest
from app import app, db_session, Customer, Staff, Order, OrderItem  
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'

  
    with app.test_client() as client:
        with app.app_context():
            # Clean up the database, first delete the relevant order items, then delete the related orders, customers and employees
            db_session.query(OrderItem).delete()  
            db_session.query(Order).delete()  
            db_session.query(Customer).delete()  
            db_session.query(Staff).delete()  
            db_session.commit()

            # add a customer and stuff
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
            db_session.commit()

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
