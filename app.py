from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect
from models import Customer, Staff, Vegetable, PremadeBox, Order, OrderItem, Base, engine, premade_box_vegetable
from sqlalchemy import case
from datetime import datetime, timedelta
from sqlalchemy import desc





app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 替换为一个安全的密钥

# 创建数据库会话
Session = sessionmaker(bind=engine)
db_session = Session()

@app.route('/')
def home():
    return render_template('home.html')  # 确保你有一个 home.html 模板


#登陆
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')  # 取得用户类型（customer或staff）

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
    
    return render_template('login.html')  # GET 请求时返回登录页面


#登出
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))  # 重定向到主页


# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 从表单中获取数据
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address', '')

        # 检查必需字段
        if not name or not email or not password:
            return render_template('register.html', error="Missing required fields: name, email, and password.")

        # 检查邮箱是否已存在
        existing_customer = db_session.query(Customer).filter_by(email=email).first()
        if existing_customer:
            # 如果邮箱已存在，显示错误信息并留在注册页面
            return render_template('register.html', error="This email is already registered. Please use a different email.")

        # 如果邮箱未注册，创建新客户
        new_customer = Customer(
            name=name,
            email=email,
            password=generate_password_hash(password),  # 确保密码经过加密存储
            address=address,
            account_balance=0.0
        )

        db_session.add(new_customer)

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return render_template('register.html', error="An error occurred while registering. Please try again.")

        # 注册成功后重定向到登录页面
        return redirect(url_for('login'))

    # 如果是 GET 请求，返回注册页面
    return render_template('register.html')  # 确保这个模板存在


@app.route('/customer_dashboard', methods=['GET'])
def customer_dashboard():
    customer_id = session.get('customer_id')
    if customer_id:
        customer = db_session.query(Customer).get(customer_id)
        if customer:
            return render_template('customer_dashboard.html', customer=customer)  # 渲染客户仪表盘
    return redirect(url_for('login'))  # 未登录则重定向


#查看order
@app.route('/view_orders', methods=['GET'])
def view_orders():
    staff_id = session.get('staff_id')
    customer_id = session.get('customer_id')

    if staff_id:
        # 员工用户的逻辑
        orders = db_session.query(Order).all()  # 获取所有订单
        return render_template('view_orders_staff.html', orders=orders)  # 渲染员工专用的订单页面

    elif customer_id:
        # 客户用户的逻辑
        orders = db_session.query(Order).filter_by(customer_id=customer_id).filter(Order.status != 'Cancelled').all()
        return render_template('view_orders.html', orders=orders)  # 渲染客户专用的订单页面

    return redirect(url_for('login'))  # 未登录则重定向





@app.route('/view_order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id, customer_id=customer_id).first()
    if not order:
        return redirect(url_for('view_orders'))

    return render_template('view_order.html', order=order)


#取消订单
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

    # Redirect back to the orders page with a message
    return redirect(url_for('view_orders', message=message))




#查看蔬菜
@app.route('/vegetables', methods=['GET'])
def get_vegetables():
    staff_id = session.get('staff_id')

    if staff_id:
        vegetables = db_session.query(Vegetable).all()
        return render_template('vegetables_staff.html', vegetables=vegetables)  # 渲染员工专用的蔬菜页面

    # 如果是客户
    customer_id = session.get('customer_id')
    if customer_id:
        vegetables = db_session.query(Vegetable).all()  # 也可以返回同样的蔬菜
        return render_template('vegetables.html', vegetables=vegetables)

    return redirect(url_for('login'))  # 未登录则重定向


@app.route('/view_premade_boxes', methods=['GET'])
def view_premade_boxes():
    staff_id = session.get('staff_id')
    customer_id = session.get('customer_id')

    # 仅查询默认的预制盒
    boxes = db_session.query(PremadeBox).filter_by(is_default=True).all()
    
    # 检查是否查询到了数据
    if not boxes:
        print("No default boxes found!")

    if staff_id:
        # 员工用户的逻辑
        return render_template('view_premade_boxes_staff.html', boxes=boxes)  # 渲染员工专用的预制盒页面

    elif customer_id:
        # 客户用户的逻辑
        return render_template('view_premade_boxes.html', boxes=boxes)  # 渲染客户专用的预制盒页面

    return redirect(url_for('login'))  # 未登录则重定向






# profile
@app.route('/profile', methods=['GET'])
def profile():
    customer_id = session.get('customer_id')
    if customer_id:
        customer = db_session.query(Customer).get(customer_id)
        if customer:
            return render_template('profile.html', customer=customer)  # 渲染 profile 页面
    return redirect(url_for('login'))  # 未登录则重定向到登录页面

# 下单路由
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

    # 计算购物车总重量和金额
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

    # 创建新订单对象
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

    # 将购物车中的商品添加到订单项中
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

    # 清空购物车并重定向到 checkout 页面
    session.pop('cart', None)
    return redirect(url_for('checkout', order_id=order.id))







# 结账页面路由
@app.route('/checkout/<int:order_id>', methods=['GET', 'POST'])
def checkout(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id).first()
    if not order:
        return redirect(url_for('cart'))

    if request.method == 'POST':
        # 获取用户选择的配送方式
        delivery_method = request.form.get('delivery_method')

        # 验证配送方式
        if delivery_method not in ['pickup', 'delivery']:
            return jsonify({'message': 'Invalid delivery method'}), 400

        # 仅在订单配送方式为 'pending' 且选择为 'delivery' 时更新配送费，防止重复添加
        if order.delivery_method == 'pending':
            order.delivery_method = delivery_method
            if delivery_method == 'delivery':
                order.delivery_fee = 10.0  # 设置配送费
            else:
                order.delivery_fee = 0.0  # 设置为无配送费

            # 更新订单总金额（仅在第一次选择配送方式时更新）
            order.total_amount += order.delivery_fee

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return jsonify({'message': 'An error occurred while updating the order.', 'error': str(e)}), 500

        # 在用户点击按钮后重定向到选择支付方式页面
        return redirect(url_for('select_payment', order_id=order.id))

    return render_template('checkout.html', order=order)

# 选支付
@app.route('/select_payment/<int:order_id>', methods=['GET', 'POST'])
def select_payment(order_id):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    # 查询订单，确保获取最新的数据
    order = db_session.query(Order).filter_by(id=order_id).first()

    if not order:
        return redirect(url_for('cart'))

    # 确保金额包含配送费，使用订单中的 total_amount
    total_amount = order.total_amount

    error_message = None  # 初始化错误信息为空

    if request.method == 'POST':
        payment_type = request.form.get('payment_type')

        # 验证支付方式是否有效
        if payment_type not in ['credit_card', 'debit_card', 'account']:
            error_message = 'Invalid payment type'
        else:
            # 账户余额检查
            if payment_type == 'account':
                customer = db_session.query(Customer).get(customer_id)
                if customer.account_balance < total_amount:
                    error_message = 'Insufficient account balance.'
                else:
                    # 支付方式选择完成后跳转到确认支付页面
                    return redirect(url_for('confirm_payment', order_id=order.id, payment_type=payment_type))

            # 如果选择了信用卡或借记卡，直接跳转到确认支付页面
            if payment_type in ['credit_card', 'debit_card']:
                return redirect(url_for('confirm_payment', order_id=order.id, payment_type=payment_type))

    return render_template('select_payment.html', order=order, total_amount=total_amount, error_message=error_message)

# 确认支付
@app.route('/confirm_payment/<int:order_id>/<payment_type>', methods=['GET', 'POST'])
def confirm_payment(order_id, payment_type):
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    order = db_session.query(Order).filter_by(id=order_id).first()
    customer = db_session.query(Customer).get(customer_id)

    # 确保总金额包括配送费，使用订单中的 total_amount
    total_amount = order.total_amount

    if request.method == 'POST':
        try:
            # 如果支付方式是账户余额，确保余额足够
            if payment_type == 'account':
                if customer.account_balance < total_amount:
                    return jsonify({'message': 'Insufficient account balance.'}), 400
                customer.account_balance -= total_amount

            # 更新订单支付方式和状态
            order.payment_method = payment_type
            order.status = 'Completed'
            order.order_date = datetime.now()

            db_session.commit()
            # 跳转到交易完成页面
            return redirect(url_for('transaction_complete', order_id=order.id))
        except Exception as e:
            db_session.rollback()
            return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

    return render_template('confirm_payment.html', order=order, payment_type=payment_type, total_amount=total_amount)



#支付完成
@app.route('/transaction_complete/<int:order_id>')
def transaction_complete(order_id):
    order = db_session.query(Order).filter_by(id=order_id).first()
    if not order:
        return redirect(url_for('view_orders'))

    return render_template('transaction_complete.html', order=order)


#添加购物车
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    product_type = request.form.get('product_type')
    quantity = int(request.form.get('quantity', 1))

    if 'cart' not in session:
        session['cart'] = []

    # 获取商品详情
    product = None
    if product_type == 'vegetable':
        product = db_session.query(Vegetable).get(product_id)
    elif product_type == 'premade_box':
        product = db_session.query(PremadeBox).get(product_id)

    if not product:
        return jsonify({'message': 'Product not found'}), 404

    # 将商品添加到购物车
    session['cart'].append({
        'product_id': product_id,
        'product_type': product_type,
        'quantity': quantity,
        'weight': getattr(product, 'weight', 0) * quantity  # 计算总重量
    })

    session.modified = True
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:item_index>', methods=['POST'])
def remove_from_cart(item_index):
    cart_items = session.get('cart', [])
    if 0 <= item_index < len(cart_items):
        del cart_items[item_index]
        session['cart'] = cart_items
        session.modified = True
    return redirect(url_for('cart'))


#购物车内容
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    products = []

    for item in cart_items:
        product = None
        if item['product_type'] == 'vegetable':
            product = db_session.query(Vegetable).get(item['product_id'])
            product_price = product.price_per_kg if product else 0  # 使用正确的属性名并处理 None
        elif item['product_type'] == 'premade_box':
            product = db_session.query(PremadeBox).get(item['product_id'])
            product_price = product.price if product else 0  # 预制盒的价格属性并处理 None

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




@app.route('/staff_dashboard', methods=['GET'])
def staff_dashboard():
    staff_id = session.get('staff_id')
    if staff_id:
        staff = db_session.query(Staff).get(staff_id)
        if staff:
            return render_template('staff_dashboard.html', staff=staff)  # 渲染员工仪表盘
    return redirect(url_for('login'))  # 未登录则重定向





@app.route('/topup', methods=['GET', 'POST'])
def topup():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))  # 如果未登录，重定向到登录页面

    error_message = None
    success_message = None

    if request.method == 'POST':
        try:
            # 获取充值金额
            topup_amount = float(request.form.get('topup_amount'))
            
            # 校验充值金额必须大于0
            if topup_amount <= 0:
                error_message = "Please enter a valid amount greater than zero."
            else:
                # 获取当前客户对象
                customer = db_session.query(Customer).get(customer_id)

                # 更新账户余额
                customer.account_balance += topup_amount

                # 提交更改
                db_session.commit()

                # 设置成功信息
                success_message = f"Successfully topped up ${topup_amount:.2f} to your account."

        except ValueError:
            error_message = "Invalid input. Please enter a valid number."
        except Exception as e:
            db_session.rollback()
            error_message = f"An error occurred while processing your top-up. Error: {str(e)}"

    return render_template('topup.html', error_message=error_message, success_message=success_message)


@app.route('/view_customers', methods=['GET'])
def view_customers():
    customers = db_session.query(Customer).all()
    return render_template('view_customers.html', customers=customers)




@app.route('/generate_sales_report', methods=['GET'])
def generate_sales_report():
    # 设置时间范围
    today = datetime.today()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)
    one_year_ago = today - timedelta(days=365)

    # 计算一周、一个月和一年的总销售额
    def calculate_sales(start_date):
        return db_session.query(func.sum(OrderItem.price * OrderItem.quantity)).\
            join(Order, OrderItem.order_id == Order.id).\
            filter(Order.order_date >= start_date, Order.status == 'Completed').scalar() or 0

    week_sales = calculate_sales(one_week_ago)
    month_sales = calculate_sales(one_month_ago)
    year_sales = calculate_sales(one_year_ago)

    # 获取最受欢迎的商品（按销量排序，限前5个）
    popular_items = db_session.query(
        OrderItem.product_id,
        OrderItem.product_type,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).group_by(OrderItem.product_id, OrderItem.product_type).\
        order_by(desc('total_quantity')).\
        limit(5).all()

    # 转换最受欢迎的商品信息，适合模板渲染
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

    # 销售分类（按商品类型）
    vegetable_sales = db_session.query(func.sum(OrderItem.price * OrderItem.quantity)).\
        join(Order, OrderItem.order_id == Order.id).\
        filter(OrderItem.product_type == 'vegetable', Order.status == 'Completed').scalar() or 0

    premade_box_sales = db_session.query(func.sum(OrderItem.price * OrderItem.quantity)).\
        join(Order, OrderItem.order_id == Order.id).\
        filter(OrderItem.product_type == 'premade_box', Order.status == 'Completed').scalar() or 0

    # 渲染模板，并传递动态数据
    return render_template(
        'sales_report.html',
        week_sales=week_sales,
        month_sales=month_sales,
        year_sales=year_sales,
        popular_products=popular_products,
        vegetable_sales=vegetable_sales,
        premade_box_sales=premade_box_sales
    )


@app.route('/create_premade_box', methods=['GET', 'POST'])
def create_premade_box():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('login'))

    if request.method == 'GET':
        vegetables = db_session.query(Vegetable).all()
        max_weights = {'small': 5.0, 'medium': 10.0, 'large': 20.0}  # 添加不同大小对应的最大重量信息
        return render_template('create_premade_box.html', vegetables=vegetables, max_weights=max_weights)

    # POST 请求处理
    box_size = request.form.get('size')
    selected_vegetable_ids = request.form.getlist('vegetable_ids')
    selected_vegetables = []

    for veg_id in selected_vegetable_ids:
        weight = request.form.get(f'weight_{veg_id}')
        if weight:
            selected_vegetables.append({'vegetable_id': int(veg_id), 'weight': float(weight)})

    if not box_size or not selected_vegetables:
        return jsonify({'message': 'Invalid input data'}), 400

    max_weights = {'small': 5.0, 'medium': 10.0, 'large': 20.0}
    max_weight = max_weights.get(box_size)

    # 检查选中的蔬菜总重量是否超过盒子最大重量限制
    total_weight = sum(item['weight'] for item in selected_vegetables)
    if total_weight > max_weight:
        # 如果超出最大重量限制，则返回错误并重新渲染页面
        vegetables = db_session.query(Vegetable).all()
        max_weights = {'small': 5.0, 'medium': 10.0, 'large': 20.0}
        error_message = f"Total weight exceeds the maximum allowed weight for {box_size} box ({max_weight} kg). Please reduce the weight."
        return render_template('create_premade_box.html', vegetables=vegetables, max_weights=max_weights, error=error_message)

    # 计算价格逻辑
    def calculate_premade_box_price(selected_vegetables, base_price):
        total_price = base_price  # 初始价格为盒子的基础价格

        for item in selected_vegetables:
            vegetable = db_session.query(Vegetable).get(item['vegetable_id'])
            if not vegetable:
                raise ValueError(f"Vegetable with ID {item['vegetable_id']} not found")

            weight = item['weight']
            price_for_vegetable = vegetable.price_per_kg * weight
            total_price += price_for_vegetable

        return total_price

    base_price = 10.0  # 可以根据需求设置基础价格
    calculated_price = calculate_premade_box_price(selected_vegetables, base_price)

    premade_box = PremadeBox(
        name=f'Custom {box_size.capitalize()} Box',
        size=box_size,
        max_weight=max_weight,
        base_price=base_price,
        price=calculated_price,
        description=None  # 可根据需要添加描述
    )

    db_session.add(premade_box)
    db_session.commit()  # 确保 `premade_box` 已经保存并有了 ID

    # 将预制盒添加到购物车
    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({
        'product_id': premade_box.id,
        'product_type': 'premade_box',
        'quantity': 1,  # 默认数量为1
        'weight': total_weight
    })

    session.modified = True

    return redirect(url_for('cart'))  # 返回购物车页面



@app.route('/clear_session')
def clear_session():
    session.clear()
    return "Session cleared!"









if __name__ == '__main__':
    app.run(debug=True)
