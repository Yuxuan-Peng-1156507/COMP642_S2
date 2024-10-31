
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db_session
from models import (
    Person, Staff, PrivateCustomer, CorporateCustomer, Customer,
    Veggie, WeightedVeggie, PackVeggie, UnitPriceVeggie,
    PremadeBox, Order, OrderLine, Payment, CreditCardPayment,
    DebitCardPayment, Item
)
import datetime
from sqlalchemy import func, desc

# Setting up Flask app
app = Flask(__name__)
app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:zhao1411935907@localhost:3306/fresh_harvest'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.context_processor
def utility_processor():
    def calculate_order_total(order, delivery_option, customer=None):
        total = 0.0
        for line in order.list_of_items:
            item = line.item
            if isinstance(item, WeightedVeggie):
                total += item.price_per_kilo * (line.weight or 0)
            elif isinstance(item, PackVeggie):
                total += item.price_per_pack * line.item_number
            elif isinstance(item, UnitPriceVeggie):
                total += item.price_per_unit * line.item_number
            elif isinstance(item, PremadeBox):
                total += item.price * line.item_number
        if delivery_option == 'delivery':
            total += 10.0
        if customer and isinstance(customer, CorporateCustomer):
            total *= (1 - customer.discount_rate)
        return total
    return dict(calculate_order_total=calculate_order_total)



def calculate_order_total(order, delivery_option, customer=None):
    total = 0.0
    for line in order.list_of_items:
        item = line.item
        if isinstance(item, WeightedVeggie):
            total += item.price_per_kilo * (line.weight or 0)
        elif isinstance(item, PackVeggie):
            total += item.price_per_pack * line.item_number
        elif isinstance(item, UnitPriceVeggie):
            total += item.price_per_unit * line.item_number
        elif isinstance(item, PremadeBox):
            total += item.price * line.item_number
    if delivery_option == 'delivery':
        total += 10.0
    if customer and isinstance(customer, CorporateCustomer):
        total *= (1 - customer.discount_rate)
    return total


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db_session.query(Person).filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            if db_session.query(Staff).get(user.id):
                session['role'] = 'staff'
            elif db_session.query(PrivateCustomer).get(user.id):
                session['role'] = 'private_customer'
            elif db_session.query(CorporateCustomer).get(user.id):
                session['role'] = 'corporate_customer'
            else:
                flash('Invalid user role.')
                return redirect(url_for('login'))

            if session['role'] in ['private_customer', 'corporate_customer']:
                return redirect(url_for('customer_dashboard'))
            elif session['role'] == 'staff':
                return redirect(url_for('staff_dashboard'))
        else:
            flash('User name or password is wrong.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Customer routes
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    customer = db_session.query(Customer).get(session['user_id'])
    return render_template('customer_dashboard.html', customer=customer)

@app.route('/customer/view_vegetables')
def view_vegetables():
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    veggies = db_session.query(Veggie).all()
    return render_template('view_vegetables.html', veggies=veggies)

@app.route('/customer/view_premade_boxes')
def view_premade_boxes():
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    premade_boxes = db_session.query(PremadeBox).all()
    return render_template('view_premade_boxes.html', premade_boxes=premade_boxes)












@app.route('/customer/place_order', methods=['GET', 'POST'])
def place_order():
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            customer = db_session.query(Customer).get(session['user_id'])
            delivery_option = request.form.get('delivery_option', 'pickup')
            order_number = str(datetime.datetime.now())
            order = Order(customer=customer, order_status='Pending', order_number=order_number, delivery_option=delivery_option)
            db_session.add(order)
            db_session.commit()

            selected_veggies = request.form.getlist('veggies')
            for veggie_id in selected_veggies:
                veggie = db_session.query(Veggie).get(veggie_id)
                if veggie:
                    quantity = int(request.form.get(f'quantity_{veggie_id}', 1))
                    if veggie.veg_type == 'weighted':
                        weight = float(request.form.get(f'weight_{veggie_id}', 1.0))
                        order_line = OrderLine(order=order, item=veggie, item_number=quantity, weight=weight)
                    else:
                        order_line = OrderLine(order=order, item=veggie, item_number=quantity)
                    db_session.add(order_line)

            selected_boxes = request.form.getlist('premade_boxes')
            for box_id in selected_boxes:
                box = db_session.query(PremadeBox).get(box_id)
                if box:
                    quantity = int(request.form.get(f'quantity_box_{box_id}', 1))
                    order_line = OrderLine(order=order, item=box, item_number=quantity)
                    db_session.add(order_line)
            db_session.commit()
            payment_amount = calculate_order_total(order, delivery_option, customer)

            if not customer.can_place_order(payment_amount):
                flash('Your account status does not allow placing this order.')
                db_session.rollback()
                return redirect(url_for('place_order'))

            payment_type = request.form.get('payment_type', 'account')
            if payment_type == 'account':
                customer.cust_balance -= payment_amount 
                payment = Payment(customer=customer, payment_amount=payment_amount, payment_type='account')
                db_session.add(payment)
                order.payment = payment
                db_session.commit()
            elif payment_type == 'credit_card':
                payment = CreditCardPayment(
                    customer=customer,
                    payment_amount=payment_amount,
                    payment_type='credit_card',
                    card_number=request.form['card_number'],
                    card_expiry_date=request.form['card_expiry_date'],
                    card_type=request.form['card_type']
                )
                customer.cust_balance -= payment_amount 
                db_session.add(payment)
                order.payment = payment
                db_session.commit()
            elif payment_type == 'debit_card':
                payment = DebitCardPayment(
                    customer=customer,
                    payment_amount=payment_amount,
                    payment_type='debit_card',
                    bank_name=request.form['bank_name'],
                    debit_card_number=request.form['debit_card_number']
                )
                customer.cust_balance -= payment_amount 
                db_session.add(payment)
                order.payment = payment
                db_session.commit()
            else:
                payment = Payment(customer=customer, payment_amount=payment_amount, payment_type=payment_type)
                customer.cust_balance -= payment_amount  
                db_session.add(payment)
                order.payment = payment
                db_session.commit()
            db_session.commit()
            flash('The order has been successfully placed.')
            return redirect(url_for('view_order', order_id=order.id))
        except Exception as e:
            db_session.rollback()
            flash(f'An error occurred while placing an order: {e}')
            return redirect(url_for('place_order'))
    else:
        veggies = db_session.query(Veggie).all()
        premade_boxes = db_session.query(PremadeBox).all()
        return render_template('place_order.html', veggies=veggies, premade_boxes=premade_boxes)





@app.route('/customer/view_order/<int:order_id>')
def view_order(order_id):
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    
    order = db_session.query(Order).get(order_id)
    if order is None or order.customer.id != session['user_id']:
        flash('Order not found or not authorized to access')
        return redirect(url_for('customer_dashboard'))
    total = calculate_order_total(order, order.delivery_option, order.customer)
    return render_template('view_order.html', order=order, total=total)




@app.route('/customer/cancel_order/<int:order_id>')
def cancel_order(order_id):
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    order = db_session.query(Order).get(order_id)
    if order and order.order_status == 'Pending' and order.customer.id == session['user_id']:
        try:
            payment_amount = calculate_order_total(order, order.delivery_option, order.customer)
            customer = order.customer
            customer.cust_balance += payment_amount

            payments = db_session.query(Payment).filter_by(customer_id=customer.id, payment_amount=-payment_amount).all()
            for payment in payments:
                db_session.delete(payment)

            db_session.delete(order)
            db_session.commit()
            flash('The order has been cancelled successfully.')
        except Exception as e:
            db_session.rollback()
            flash(f'An error occurred while canceling the order: {e}')
    else:
        flash('Unable to cancel the order')
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/view_past_orders')
def view_past_orders():
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    customer_id = session['user_id']
    current_orders = db_session.query(Order).filter(
        Order.order_customer == customer_id,
        Order.order_status.in_(['Pending', 'Processing'])
    ).all()
    past_orders = db_session.query(Order).filter(
        Order.order_customer == customer_id,
        Order.order_status =='Completed'
    ).all()
    return render_template('view_past_orders.html', current_orders=current_orders, past_orders=past_orders)

@app.route('/customer/view_details')
def view_customer_details():
    if 'user_id' not in session or session['role'] not in ['private_customer', 'corporate_customer']:
        return redirect(url_for('login'))
    customer = db_session.query(Customer).get(session['user_id'])
    return render_template('view_details.html', customer=customer)




# Employee routes
@app.route('/staff/dashboard')
def staff_dashboard():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    return render_template('staff_dashboard.html')

@app.route('/staff/view_items')
def staff_view_items():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    veggies = db_session.query(Veggie).all()
    premade_boxes = db_session.query(PremadeBox).all()
    return render_template('staff_view_items.html', veggies=veggies, premade_boxes=premade_boxes)

@app.route('/staff/view_current_orders')
def view_current_orders():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    current_orders = db_session.query(Order).filter(Order.order_status.in_(['Pending', 'Processing'])).all()
    return render_template('view_current_orders.html', orders=current_orders)

@app.route('/staff/view_order/<int:order_id>')
def staff_view_order(order_id):
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))

    order = db_session.query(Order).get(order_id)
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_current_orders'))
    source = request.args.get('source', 'current_orders')

    total = calculate_order_total(order, order.delivery_option, order.customer)

    return render_template('staff_view_order.html', order=order, total=total, source=source)

@app.route('/staff/view_past_orders')
def staff_view_past_orders():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    past_orders = db_session.query(Order).filter(Order.order_status != 'Pending').all()
    return render_template('staff_view_past_orders.html', orders=past_orders)

@app.route('/staff/update_order_status/<int:order_id>', methods=['GET', 'POST'])
def update_order_status(order_id):
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    order = db_session.query(Order).get(order_id)
    if order is None:
        flash('Order not found')
        return redirect(url_for('view_current_orders'))
    if request.method == 'POST':
        try:
            new_status = request.form['order_status']
            if new_status in ['Deleted', 'Cancelled']:
                # Calculate the total amount to refund
                total_amount = calculate_order_total(order, order.delivery_option, order.customer)
                customer = order.customer
                customer.cust_balance += total_amount

                if order.payment:
                    db_session.delete(order.payment)

                db_session.delete(order)
                db_session.commit()
                flash('Order has been deleted and customer balance refunded.')
                return redirect(url_for('view_current_orders'))
            else:
                order.order_status = new_status
                db_session.commit()
                flash('Order status has been successfully updated.')
                return redirect(url_for('view_current_orders'))
        except Exception as e:
            db_session.rollback()
            flash(f'Error updating order status: {e}')
            return redirect(url_for('update_order_status', order_id=order_id))
    return render_template('update_order_status.html', order=order)




@app.route('/staff/view_customers')
def view_customers():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    private_customers = db_session.query(PrivateCustomer).all()
    corporate_customers = db_session.query(CorporateCustomer).all()
    return render_template('view_customers.html', private_customers=private_customers, corporate_customers=corporate_customers)


@app.route('/staff/generate_sales_report')
def generate_sales_report():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))

    now = datetime.datetime.now()
    week_ago = now - datetime.timedelta(weeks=1)
    month_ago = now - datetime.timedelta(days=30)
    year_ago = now - datetime.timedelta(days=365)

    sales_week = db_session.query(func.sum(Payment.payment_amount)).filter(Payment.payment_date >= week_ago).scalar() or 0.0
    sales_month = db_session.query(func.sum(Payment.payment_amount)).filter(Payment.payment_date >= month_ago).scalar() or 0.0
    sales_year = db_session.query(func.sum(Payment.payment_amount)).filter(Payment.payment_date >= year_ago).scalar() or 0.0

    orders_week = db_session.query(func.count(Order.id)).filter(Order.order_date >= week_ago).scalar() or 0
    orders_month = db_session.query(func.count(Order.id)).filter(Order.order_date >= month_ago).scalar() or 0
    orders_year = db_session.query(func.count(Order.id)).filter(Order.order_date >= year_ago).scalar() or 0

    avg_order_week = sales_week / orders_week if orders_week else 0.0
    avg_order_month = sales_month / orders_month if orders_month else 0.0
    avg_order_year = sales_year / orders_year if orders_year else 0.0

    top_items = db_session.query(
        Item,
        func.sum(OrderLine.item_number).label('total_quantity')
    ).join(OrderLine, Item.id == OrderLine.item_id).join(Order, OrderLine.order_id == Order.id).filter(Order.order_date >= month_ago).group_by(Item.id).order_by(desc('total_quantity')).limit(5).all()

    private_sales = db_session.query(func.sum(Payment.payment_amount)).join(Customer).filter(
        Payment.payment_date >= month_ago,
        Customer.person_type == 'private_customer'
    ).scalar() or 0.0
    corporate_sales = db_session.query(func.sum(Payment.payment_amount)).join(Customer).filter(
        Payment.payment_date >= month_ago,
        Customer.person_type == 'corporate_customer'
    ).scalar() or 0.0
    return render_template(
        'sales_report.html',
        week=sales_week,
        month=sales_month,
        year=sales_year,
        orders_week=orders_week,
        orders_month=orders_month,
        orders_year=orders_year,
        avg_order_week=avg_order_week,
        avg_order_month=avg_order_month,
        avg_order_year=avg_order_year,
        top_items=top_items,
        private_sales=private_sales,
        corporate_sales=corporate_sales
    )

@app.route('/staff/view_popular_items')
def view_popular_items():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))

    popular_items = db_session.query(OrderLine.item_id, func.sum(OrderLine.item_number).label('total_quantity'))\
        .group_by(OrderLine.item_id)\
        .order_by(func.sum(OrderLine.item_number).desc()).all()

    items = [(db_session.query(Item).get(item_id), quantity) for item_id, quantity in popular_items]
    
    return render_template('view_popular_items.html', items=items)

@app.route('/staff/view_unpopular_items')
def view_unpopular_items():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    unpopular_items = db_session.query(OrderLine.item_id, func.sum(OrderLine.item_number).label('total_quantity'))\
        .group_by(OrderLine.item_id)\
        .order_by(func.sum(OrderLine.item_number)).limit(10).all()
    items = [(db_session.query(Item).get(item_id), quantity) for item_id, quantity in unpopular_items]
    return render_template('view_unpopular_items.html', items=items)

@app.route('/staff/place_order_for_customer', methods=['GET', 'POST'])
def staff_place_order():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            customer_id = request.form['customer_id']
            customer = db_session.query(Customer).get(customer_id)
            delivery_option = request.form.get('delivery_option', 'pickup')
            order_number = str(datetime.datetime.now())
            order = Order(customer=customer, staff_id=session['user_id'], order_status='Pending', order_number=order_number, delivery_option=delivery_option)
            db_session.add(order)
            db_session.commit()

            # Process selected vegetables
            selected_veggies = request.form.getlist('veggies')
            for veggie_id in selected_veggies:
                veggie = db_session.query(Veggie).get(veggie_id)
                if veggie:
                    quantity = int(request.form.get(f'quantity_{veggie_id}', 1))
                    if veggie.veg_type == 'weighted':
                        weight = float(request.form.get(f'weight_{veggie_id}', 1.0))
                        order_line = OrderLine(order=order, item=veggie, item_number=quantity, weight=weight)
                    else:
                        order_line = OrderLine(order=order, item=veggie, item_number=quantity)
                    db_session.add(order_line)

            # Process selected premade boxes
            selected_boxes = request.form.getlist('premade_boxes')
            for box_id in selected_boxes:
                box = db_session.query(PremadeBox).get(box_id)
                if box:
                    quantity = int(request.form.get(f'quantity_box_{box_id}', 1))
                    order_line = OrderLine(order=order, item=box, item_number=quantity)
                    db_session.add(order_line)
            db_session.commit()
            payment_amount = calculate_order_total(order, delivery_option, customer)

            # Apply discounts for corporate customers
            if isinstance(customer, CorporateCustomer):
                payment_amount *= (1 - customer.discount_rate)

            # Check if customer can place order
            if not customer.can_place_order(payment_amount):
                flash('Customer\'s account status does not allow placing this order.')
                db_session.rollback()
                return redirect(url_for('staff_place_order'))

            # Process payment
            payment_type = request.form.get('payment_type', 'account')
            if payment_type == 'account':
                customer.cust_balance -= payment_amount 
                payment = Payment(customer=customer, payment_amount=payment_amount, payment_type='account')
                db_session.add(payment)
                order.payment = payment
                db_session.commit()
            elif payment_type == 'credit_card':
                payment = CreditCardPayment(
                    customer=customer,
                    payment_amount=payment_amount,
                    payment_type='credit_card',
                    card_number=request.form['card_number'],
                    card_expiry_date=request.form['card_expiry_date'],
                    card_type=request.form['card_type']
                )
                customer.cust_balance -= payment_amount  
                db_session.add(payment)
                order.payment = payment
                db_session.commit()                
            elif payment_type == 'debit_card':
                payment = DebitCardPayment(
                    customer=customer,
                    payment_amount=payment_amount,
                    payment_type='debit_card',
                    bank_name=request.form['bank_name'],
                    debit_card_number=request.form['debit_card_number']
                )
                customer.cust_balance -= payment_amount  
                db_session.add(payment)
                order.payment = payment
                db_session.commit()  
            else:
                payment = Payment(customer=customer, payment_amount=payment_amount, payment_type=payment_type)
                customer.cust_balance -= payment_amount 
                db_session.add(payment)
                order.payment = payment
                db_session.commit()  
            db_session.commit()
            flash('The order has been successfully placed.')
            return redirect(url_for('staff_dashboard'))
        except Exception as e:
            db_session.rollback()
            flash(f'An error occurred while placing an order: {e}')
            return redirect(url_for('staff_place_order'))
    else:
        customers = db_session.query(Customer).all()
        veggies = db_session.query(Veggie).all()
        premade_boxes = db_session.query(PremadeBox).all()
        return render_template('staff_place_order.html', customers=customers, veggies=veggies, premade_boxes=premade_boxes)


if __name__ == '__main__':
    app.run(debug=True)
