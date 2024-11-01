from models import Customer, Staff, Vegetable, PremadeBox, Order, OrderItem, Base, engine, premade_box_vegetable
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy.orm import scoped_session, sessionmaker
import threading  
import time
from sqlalchemy import text
from sqlalchemy import func
from sqlalchemy import desc
from flask import redirect
from sqlalchemy import text






app = Flask(__name__)
app.secret_key = 'your_secret_key'  

Session = scoped_session(sessionmaker(bind=engine))
db_session = Session

@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Flask 应用上下文结束时关闭数据库会话。
    如果有异常，则回滚事务。
    """
    if exception:
        db_session.rollback()  # 回滚事务，如果有异常
    db_session.remove()  # 关闭会话

def keep_connection_alive():
    """
    定期运行简单查询以保持数据库连接活跃。
    每200秒运行一次 SELECT 1。
    """
    while True:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))  # 使用 text 执行简单查询
            time.sleep(200)  # 每200秒运行一次
        except Exception as e:
            print(f"Failed to keep the connection alive: {e}")

# 启动后台线程以保持数据库连接活跃
threading.Thread(target=keep_connection_alive, daemon=True).start()



@app.route('/')
def home():
    return render_template('home.html')  


#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')  

        print(f"Trying to log in with email: {email} and password: {password}")

        if user_type == 'customer':
            customer = db_session.query(Customer).filter_by(email=email).first()
            if customer and check_password_hash(customer.password, password):
                session['customer_id'] = customer.id
                return redirect(url_for('customer_dashboard'))
            print("Invalid customer credentials!")
            return jsonify({'message': 'Invalid credentials!'}), 401

        elif user_type == 'staff':
            staff = db_session.query(Staff).filter_by(email=email).first()
            if staff and check_password_hash(staff.password, password):
                session['staff_id'] = staff.id
                return redirect(url_for('staff_dashboard'))  # Redirect to staff dashboard
            print("Invalid staff credentials!")
            return jsonify({'message': 'Invalid credentials!'}), 401
    
    return render_template('login.html')  


#logout
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))  # Redirect to home 


# register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address', '')

        if not name or not email or not password:
            return render_template('register.html', error="Missing required fields: name, email, and password.")

        # check if email is existed 
        existing_customer = db_session.query(Customer).filter_by(email=email).first()
        if existing_customer:
            # if email existed, get error 
            return render_template('register.html', error="This email is already registered. Please use a different email.")

        new_customer = Customer(
            name=name,
            email=email,
            password=generate_password_hash(password),  # hash the password
            address=address,
            account_balance=0.0
        )

        db_session.add(new_customer)

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return render_template('register.html', error="An error occurred while registering. Please try again.")

        # back to login 
        return redirect(url_for('login'))

    return render_template('register.html')  

#customer dashboard
@app.route('/customer_dashboard', methods=['GET'])
def customer_dashboard():
    customer_id = session.get('customer_id')
    if customer_id:
        customer = db_session.query(Customer).get(customer_id)
        if customer:
            return render_template('customer_dashboard.html', customer=customer)  
    return redirect(url_for('login'))  


#View orders
@app.route('/view_orders', methods=['GET'])
def view_orders():
    staff_id = session.get('staff_id')
    customer_id = session.get('customer_id')

    if staff_id:
        # stuff view orders
        orders = db_session.query(Order).all()  
        return render_template('view_orders_staff.html', orders=orders)  

    elif customer_id:
        # customer view orders
        orders = db_session.query(Order).filter_by(customer_id=customer_id).filter(Order.status != 'Cancelled').all()
        return render_template('view_orders.html', orders=orders) 

    return redirect(url_for('login'))  

#view order details 
@app.route('/view_order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id, customer_id=customer_id).first()
    if not order:
        return redirect(url_for('view_orders'))

    return render_template('view_order.html', order=order)


#cancel order
@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    # Retrieve the order for the current customer
    order = db_session.query(Order).filter_by(id=order_id, customer_id=customer_id).first()

    # Check if order exists and is in 'Pending' status
    if order and order.status == 'Pending':
        order.status = 'Cancelled'
        db_session.commit()
        message = "Order has been successfully cancelled."
    else:
        message = "Only orders with 'Pending' status can be cancelled."

    return redirect(url_for('view_orders', message=message))


#check vegetables
@app.route('/vegetables', methods=['GET'])
def get_vegetables():
    staff_id = session.get('staff_id')

    if staff_id:
        vegetables = db_session.query(Vegetable).all()
        return render_template('vegetables_staff.html', vegetables=vegetables) 

    customer_id = session.get('customer_id')
    if customer_id:
        vegetables = db_session.query(Vegetable).all()  
        return render_template('vegetables.html', vegetables=vegetables)

    return redirect(url_for('login'))  


#check premade boxes
@app.route('/view_premade_boxes', methods=['GET'])
def view_premade_boxes():
    staff_id = session.get('staff_id')
    customer_id = session.get('customer_id')

    # only show defult premade_boxe
    boxes = db_session.query(PremadeBox).filter_by(is_default=True).all()
    
    if not boxes:
        print("No default boxes found!")

    if staff_id:
        return render_template('view_premade_boxes_staff.html', boxes=boxes) 

    elif customer_id:
        return render_template('view_premade_boxes.html', boxes=boxes) 

    return redirect(url_for('login'))  


#create customer premade box 
@app.route('/create_premade_box', methods=['GET', 'POST'])
def create_premade_box():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    if request.method == 'GET':
        vegetables = db_session.query(Vegetable).all()
        max_weights = {'small': 5.0, 'medium': 10.0, 'large': 20.0} 
        return render_template('create_premade_box.html', vegetables=vegetables, max_weights=max_weights)

    box_size = request.form.get('size')
    selected_vegetable_ids = request.form.getlist('vegetable_ids')
    selected_vegetables = []

    for veg_id in selected_vegetable_ids:
        weight = request.form.get(f'weight_{veg_id}')
        if weight:
            selected_vegetables.append({'vegetable_id': int(veg_id), 'weight': float(weight)})

    if not box_size or not selected_vegetables:
        vegetables = db_session.query(Vegetable).all()
        max_weights = {'small': 5.0, 'medium': 10.0, 'large': 20.0}
        error_message = "Please select at least one vegetable and specify its weight."
        return render_template('create_premade_box.html', vegetables=vegetables, max_weights=max_weights, error=error_message)

    max_weights = {'small': 5.0, 'medium': 10.0, 'large': 20.0}
    max_weight = max_weights.get(box_size)

    total_weight = sum(item['weight'] for item in selected_vegetables)
    if total_weight > max_weight:
        vegetables = db_session.query(Vegetable).all()
        error_message = f"Total weight exceeds the maximum allowed weight for {box_size} box ({max_weight} kg). Please reduce the weight."
        return render_template('create_premade_box.html', vegetables=vegetables, max_weights=max_weights, error=error_message)

    def calculate_premade_box_price(selected_vegetables, base_price):
        total_price = base_price
        for item in selected_vegetables:
            vegetable = db_session.query(Vegetable).get(item['vegetable_id'])
            if not vegetable:
                raise ValueError(f"Vegetable with ID {item['vegetable_id']} not found")
            weight = item['weight']
            price_for_vegetable = vegetable.price_per_kg * weight
            total_price += price_for_vegetable
        return total_price

    base_price = 10.0  
    calculated_price = calculate_premade_box_price(selected_vegetables, base_price)

    premade_box = PremadeBox(
        name=f'Custom {box_size.capitalize()} Box',
        size=box_size,
        max_weight=max_weight,
        base_price=base_price,
        price=calculated_price,
        description=None  
    )

    db_session.add(premade_box)
    db_session.commit()

    # 添加到购物车
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({
        'product_id': premade_box.id,
        'product_type': 'premade_box',
        'quantity': 1,  
        'weight': total_weight
    })

    session.modified = True

    return redirect(url_for('cart'))



# check profile
@app.route('/profile', methods=['GET'])
def profile():
    customer_id = session.get('customer_id')
    if customer_id:
        customer = db_session.query(Customer).get(customer_id)
        if customer:
            return render_template('profile.html', customer=customer)  
    return redirect(url_for('login')) 


#add to cart 
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    product_type = request.form.get('product_type')
    quantity = int(request.form.get('quantity', 1))

    if 'cart' not in session:
        session['cart'] = []

    product = None
    if product_type == 'vegetable':
        product = db_session.query(Vegetable).get(product_id)
    elif product_type == 'premade_box':
        product = db_session.query(PremadeBox).get(product_id)

    if not product:
        return jsonify({'message': 'Product not found'}), 404

    session['cart'].append({
        'product_id': product_id,
        'product_type': product_type,
        'quantity': quantity,
        'weight': getattr(product, 'weight', 0) * quantity  
    })

    session.modified = True
    return redirect(url_for('cart'))


#remove items from cart 
@app.route('/remove_from_cart/<int:item_index>', methods=['POST'])
def remove_from_cart(item_index):
    cart_items = session.get('cart', [])
    if 0 <= item_index < len(cart_items):
        del cart_items[item_index]
        session['cart'] = cart_items
        session.modified = True
    return redirect(url_for('cart'))


#view cart 
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    products = []

    for item in cart_items:
        product = None
        if item['product_type'] == 'vegetable':
            product = db_session.query(Vegetable).get(item['product_id'])
            product_price = product.price_per_kg if product else 0  
        elif item['product_type'] == 'premade_box':
            product = db_session.query(PremadeBox).get(item['product_id'])
            product_price = product.price if product else 0  

        if product:
            products.append({
                'name': product.name,
                'price': product_price,
                'quantity': item['quantity'],
                'total': product_price * item['quantity']
            })
        else:
            # Log or handle the case where a product is not found
            print(f"Product with ID {item['product_id']} not found")

    return render_template('cart.html', products=products)


#top up account balance 
@app.route('/topup', methods=['GET', 'POST'])
def topup():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login')) 

    error_message = None
    success_message = None

    if request.method == 'POST':
        try:
            topup_amount = float(request.form.get('topup_amount'))
            
            if topup_amount <= 0:
                error_message = "Please enter a valid amount greater than zero."
            else:
                customer = db_session.query(Customer).get(customer_id)

                customer.account_balance += topup_amount

                db_session.commit()

                success_message = f"Successfully topped up ${topup_amount:.2f} to your account."

        except ValueError:
            error_message = "Invalid input. Please enter a valid number."
        except Exception as e:
            db_session.rollback()
            error_message = f"An error occurred while processing your top-up. Error: {str(e)}"

    return render_template('topup.html', error_message=error_message, success_message=success_message)


# place an order
@app.route('/place_order', methods=['POST'])
def place_order():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))

    total_weight = 0
    total_amount = 0

    # calculate totlal amount
    for item in cart_items:
        product = db_session.query(Vegetable if item['product_type'] == 'vegetable' else PremadeBox).get(item['product_id'])
        if not product:
            return jsonify({'message': f'Product with ID {item["product_id"]} not found'}), 404

        if item['product_type'] == 'vegetable':
            item_weight = item['quantity']
            total_weight += item_weight
            total_amount += product.price_per_kg * item['quantity']
        else:
            total_amount += product.price * item['quantity']
            if total_weight > product.max_weight:
                return jsonify({'message': f'Exceeded max weight for {product.name}'}), 400

    order = Order(
    customer_id=customer_id,
    status="Pending",
    total_amount=total_amount,
    order_date=datetime.now(),
    payment_method="pending",
    delivery_method="pending"
    )

    db_session.add(order)
    db_session.commit()

    for item in cart_items:
        product = db_session.query(Vegetable if item['product_type'] == 'vegetable' else PremadeBox).get(item['product_id'])
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product_id'],
            product_type=item['product_type'],
            quantity=item['quantity'],
            price=product.price_per_kg if item['product_type'] == 'vegetable' else product.price
        )
        db_session.add(order_item)

    db_session.commit()

    session.pop('cart', None)
    return redirect(url_for('checkout', order_id=order.id))


# check out 
@app.route('/checkout/<int:order_id>', methods=['GET', 'POST'])
def checkout(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id).first()
    if not order:
        return redirect(url_for('cart'))

    if request.method == 'POST':
        # choose delivery_method
        delivery_method = request.form.get('delivery_method')

        if delivery_method not in ['pickup', 'delivery']:
            return jsonify({'message': 'Invalid delivery method'}), 400

        # delivery fee
        if order.delivery_method == 'pending':
            order.delivery_method = delivery_method
            if delivery_method == 'delivery':
                order.delivery_fee = 10.0  
            else:
                order.delivery_fee = 0.0  
            # update total ammount
            order.total_amount += order.delivery_fee
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return jsonify({'message': 'An error occurred while updating the order.', 'error': str(e)}), 500
        return redirect(url_for('select_payment', order_id=order.id))

    return render_template('checkout.html', order=order)

# payment method
@app.route('/select_payment/<int:order_id>', methods=['GET', 'POST'])
def select_payment(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id).first()

    if not order:
        return redirect(url_for('cart'))

    total_amount = order.total_amount

    error_message = None  

    if request.method == 'POST':
        payment_type = request.form.get('payment_type')

        if payment_type not in ['credit_card', 'debit_card', 'account']:
            error_message = 'Invalid payment type'
        else:
            # check account balance
            if payment_type == 'account':
                customer = db_session.query(Customer).get(customer_id)
                if customer.account_balance < total_amount:
                    error_message = 'Insufficient account balance.'
                else:
                    return redirect(url_for('confirm_payment', order_id=order.id, payment_type=payment_type))

            if payment_type in ['credit_card', 'debit_card']:
                return redirect(url_for('confirm_payment', order_id=order.id, payment_type=payment_type))

    return render_template('select_payment.html', order=order, total_amount=total_amount, error_message=error_message)

# confirm order
@app.route('/confirm_payment/<int:order_id>/<payment_type>', methods=['GET', 'POST'])
def confirm_payment(order_id, payment_type):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id).first()
    customer = db_session.query(Customer).get(customer_id)
    total_amount = order.total_amount

    if request.method == 'POST':
        try:
            # make sure aacount balance is enough 
            if payment_type == 'account':
                if customer.account_balance < total_amount:
                    return jsonify({'message': 'Insufficient account balance.'}), 400
                customer.account_balance -= total_amount

            order.payment_method = payment_type
            order.status = 'Completed'
            order.order_date = datetime.now()

            db_session.commit()
            return redirect(url_for('transaction_complete', order_id=order.id))
        except Exception as e:
            db_session.rollback()
            return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

    return render_template('confirm_payment.html', order=order, payment_type=payment_type, total_amount=total_amount)


#payment successfully 
@app.route('/transaction_complete/<int:order_id>')
def transaction_complete(order_id):
    order = db_session.query(Order).filter_by(id=order_id).first()
    if not order:
        return redirect(url_for('view_orders'))

    return render_template('transaction_complete.html', order=order)


#stuff dashbaord
@app.route('/staff_dashboard', methods=['GET'])
def staff_dashboard():
    staff_id = session.get('staff_id')
    if staff_id:
        staff = db_session.query(Staff).get(staff_id)
        if staff:
            return render_template('staff_dashboard.html', staff=staff)  
    return redirect(url_for('login'))  


#view customer 
@app.route('/view_customers', methods=['GET'])
def view_customers():
    customers = db_session.query(Customer).all()
    return render_template('view_customers.html', customers=customers)


#sales report 
@app.route('/generate_sales_report', methods=['GET'])
def generate_sales_report():
    # time range 
    today = datetime.today()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)
    one_year_ago = today - timedelta(days=365)

    def calculate_sales(start_date):
        return db_session.query(func.sum(OrderItem.price * OrderItem.quantity)).\
            join(Order, OrderItem.order_id == Order.id).\
            filter(Order.order_date >= start_date, Order.status == 'Completed').scalar() or 0

    week_sales = calculate_sales(one_week_ago)
    month_sales = calculate_sales(one_month_ago)
    year_sales = calculate_sales(one_year_ago)

    popular_items = db_session.query(
        OrderItem.product_id,
        OrderItem.product_type,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).group_by(OrderItem.product_id, OrderItem.product_type).\
        order_by(desc('total_quantity')).\
        limit(5).all()

    popular_products = []
    for item in popular_items:
        if item.product_type == 'vegetable':
            product = db_session.query(Vegetable).get(item.product_id)
        elif item.product_type == 'premade_box':
            product = db_session.query(PremadeBox).get(item.product_id)
        else:
            product = None

        product_name = product.name if product else "Unknown Product"
        popular_products.append({
            "product_name": product_name,
            "quantity_sold": item.total_quantity
        })

    vegetable_sales = db_session.query(func.sum(OrderItem.price * OrderItem.quantity)).\
        join(Order, OrderItem.order_id == Order.id).\
        filter(OrderItem.product_type == 'vegetable', Order.status == 'Completed').scalar() or 0

    premade_box_sales = db_session.query(func.sum(OrderItem.price * OrderItem.quantity)).\
        join(Order, OrderItem.order_id == Order.id).\
        filter(OrderItem.product_type == 'premade_box', Order.status == 'Completed').scalar() or 0

    return render_template(
        'sales_report.html',
        week_sales=week_sales,
        month_sales=month_sales,
        year_sales=year_sales,
        popular_products=popular_products,
        vegetable_sales=vegetable_sales,
        premade_box_sales=premade_box_sales
    )


#clear cache
@app.route('/clear_session')
def clear_session():
    session.clear()
    return "Session cleared!"

from models import Customer, Staff, Vegetable, PremadeBox, Order, OrderItem, Base, engine, premade_box_vegetable
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import sessionmaker, scoped_session
import threading
import time

from sqlalchemy.orm import scoped_session, sessionmaker

@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Flask 应用上下文结束时关闭数据库会话。
    如果有异常，则回滚事务。
    """
    if exception:
        db_session.rollback()  # 回滚事务，如果有异常
    db_session.remove()  # 关闭会话

def keep_connection_alive():
    """
    定期运行简单查询以保持数据库连接活跃。
    每200秒运行一次 SELECT 1。
    """
    while True:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # 使用 text 执行简单查询
        time.sleep(200)  # 每200秒运行一次

# 启动后台线程以保持数据库连接活跃
threading.Thread(target=keep_connection_alive, daemon=True).start()


if __name__ == '__main__':
    app.run(debug=True)
