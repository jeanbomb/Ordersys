from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 創建 Flask 應用和數據庫
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定義模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)

# 創建數據庫並添加測試數據
with app.app_context():
    db.create_all()  # 創建所有表

    # 添加用戶
    user = User(username='test_user', password='password123')
    db.session.add(user)

    # 添加商品
    products = [
        Product(name="綠豆糕", image="images/green_bean_cake.jpg", category="中式糕點"),
        Product(name="鳳梨酥", image="images/pineapple_cake.jpg", category="中式糕點"),
    ]
    db.session.add_all(products)
    db.session.commit()

print("用戶和商品已成功添加到資料庫！")
