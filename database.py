from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Customer, Vegetable, PremadeBox, Order, OrderItem  # 导入模型类

# 定义数据库连接字符串
DATABASE_URI = 'mysql+pymysql://root:@localhost/fresh_harvest'  # 使用你的数据库信息

# 创建数据库引擎
engine = create_engine(DATABASE_URI, echo=True)

# 创建所有表
Base.metadata.create_all(engine)

# 创建session
Session = sessionmaker(bind=engine)
session = Session()

# 示例：查询客户信息
customers = session.query(Customer).all()
for customer in customers:
    print(f"Customer: {customer.name}, Email: {customer.email}")

# 关闭会话
session.close()
