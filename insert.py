from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from models import Customer, Staff, Vegetable, PremadeBox, Order, OrderItem, Base, engine
from datetime import datetime, timedelta

Session = sessionmaker(bind=engine)
db_session = Session()

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Insert Customers
customers = [
    Customer(
        name="Alice Johnson",
        email="alice@example.com",
        password=generate_password_hash("alice123"),
        address="123 Maple St",
        account_balance=100.0
    ),
    Customer(
        name="Bob Smith",
        email="bob@example.com",
        password=generate_password_hash("bob123"),
        address="456 Oak St",
        account_balance=150.0
    ),
    Customer(
        name="Carol Williams",
        email="carol@example.com",
        password=generate_password_hash("carol123"),
        address="789 Pine St",
        account_balance=120.0
    ),
]

# Insert Staff
staff_members = [
    Staff(
        name="Parker",
        email="parkerstaff@example.com",
        password=generate_password_hash("parker123"),
        role="staff",
        created_at=datetime.now()
    ),
    Staff(
        name="Jordan",
        email="jordanstaff@example.com",
        password=generate_password_hash("jordan123"),
        role="manager",
        created_at=datetime.now()
    ),
]   

# Insert Vegetables
vegetables = [
    Vegetable(name="Tomato", price_per_kg=2.5, stock_quantity=100),
    Vegetable(name="Lettuce", price_per_kg=1.5, stock_quantity=150),
    Vegetable(name="Carrot", price_per_kg=1.0, stock_quantity=200),
    Vegetable(name="Cucumber", price_per_kg=2.0, stock_quantity=120),
    Vegetable(name="Pepper", price_per_kg=3.0, stock_quantity=80),
]

# Insert Premade Boxes
premade_boxes = [
    PremadeBox(name="Small Box", size="Small", max_weight=5.0, base_price=10.0, price=15.0, description="A small box of mixed vegetables", is_default=True),
    PremadeBox(name="Medium Box", size="Medium", max_weight=10.0, base_price=15.0, price=25.0, description="A medium box of mixed vegetables", is_default=True),
    PremadeBox(name="Large Box", size="Large", max_weight=20.0, base_price=20.0, price=35.0, description="A large box of mixed vegetables", is_default=True),
]


# Add customers, staff, vegetables, and premade boxes to session
db_session.add_all(customers + staff_members + vegetables + premade_boxes)
db_session.commit()

vegetable_items = db_session.query(Vegetable).all()
box_items = db_session.query(PremadeBox).all()

# Insert Orders and OrderItems
orders = []
for i in range(10):
    order_date = datetime.now() - timedelta(days=i)
    customer = customers[i % len(customers)]  # Rotate through customers

    delivery_method = 'pickup' if i % 2 == 0 else 'delivery'
    delivery_fee = 0.0 if delivery_method == 'delivery' else 0.0

    order = Order(
        customer_id=customer.id,
        order_date=order_date,
        status="Completed" if i < 5 else "Pending",
        total_amount=30.0 + i * 5,
        payment_method="credit_card" if i % 2 == 0 else "debit_card",
        delivery_method=delivery_method,
        delivery_fee=delivery_fee,
        delivery_address=customer.address if delivery_method == 'delivery' else None,
        customer=customer
    )

    vegetable = vegetable_items[i % len(vegetable_items)]
    premade_box = box_items[i % len(box_items)]

    order.items.append(OrderItem(
        product_type="vegetable",
        product_id=vegetable.id,
        quantity=2,
        price=vegetable.price_per_kg
    ))
    
    order.items.append(OrderItem(
        product_type="premade_box",
        product_id=premade_box.id,
        quantity=1,
        price=premade_box.price
    ))

    orders.append(order)

db_session.add_all(orders)

try:
    db_session.commit()
    print("Data inserted successfully!")
except Exception as e:
    db_session.rollback()
    print(f"An error occurred: {e}")
finally:
    db_session.close()
