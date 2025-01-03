from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import pandas as pd

# 初始化 Flask 應用與資料庫
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 用於發送訊息
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 防止警告
db = SQLAlchemy(app)

# 用戶資料表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    image = db.Column(db.String(150))
    category = db.Column(db.String(50))

class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# 菜單資料
menu = {
    "中式糕點": [
        {"name": "綠豆糕", "image": "images/green_bean_cake.jpg"},
        {"name": "鳳梨酥", "image": "images/pineapple_cake.jpg"},
        {"name": "蛋黃酥", "image": "images/egg_yolk_cake.jpg"}
    ],
    "蛋糕": [
        {"name": "草莓蛋糕", "image": "images/strawberry_cake.jpg"},
        {"name": "巧克力蛋糕", "image": "images/chocolate_cake.jpg"},
        {"name": "紅絲絨蛋糕", "image": "images/red_velvet_cake.jpg"}
    ],
    "麵包": [
        {"name": "法式長棍", "image": "images/french_baguette.jpg"},
        {"name": "可頌麵包", "image": "images/croissant_bread.jpg"},
        {"name": "菠蘿包", "image": "images/pineapple_bun.jpg"}
    ]
}

# 確保資料表已經創建
with app.app_context():
    db.create_all()  # 這將會創建所有資料表
    
def get_recommendations(customer_id):
    conn = sqlite3.connect('restaurant_system.db')
    query = """
        SELECT user_id, product_id, SUM(quantity) as purchase_count
        FROM customer_orders
        GROUP BY user_id, product_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    customer_product_matrix = df.pivot_table(index='user_id', columns='product_id', values='purchase_count', fill_value=0)
    customer_similarity = cosine_similarity(customer_product_matrix)
    customer_similarity_df = pd.DataFrame(customer_similarity, index=customer_product_matrix.index, columns=customer_product_matrix.index)

    similar_customers = customer_similarity_df[customer_id].sort_values(ascending=False).index[1:]
    recommendations = customer_product_matrix.loc[similar_customers].mean().sort_values(ascending=False).head(5)
    return recommendations


@app.route('/recommend/<int:customer_id>')
def recommend(customer_id):
    recommendations = get_recommendations(customer_id)  # 獲取推薦結果
    return render_template('recommend.html', customer_id=customer_id, recommendations=recommendations)


# 首頁路由
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 檢查會員登入
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id  # 記錄用戶的 ID (登入後)
            return redirect(url_for('order'))  # 登入成功，跳轉到訂單頁面
        else:
            flash('登入失敗，請檢查帳號或密碼', 'danger')
    return render_template('home.html')  # 顯示登入頁面

# 訪客登入
@app.route('/guest')
def guest():
    session.pop('user_id', None)  # 確保登出任何已經存在的用戶 session
    return redirect(url_for('order'))  # 訪客直接進入訂單頁面


# 註冊頁面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 檢查帳號是否存在
        if User.query.filter_by(username=username).first():
            flash('該帳號已存在，請選擇其他帳號名稱', 'danger')
            return redirect(url_for('register'))  # 如果帳號已存在，重新導向到註冊頁

        # 創建新用戶
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('註冊成功！', 'success')
        return redirect(url_for('home'))  # 註冊成功後，返回首頁
    
    return render_template('register.html')  # 顯示註冊頁面

# 訂單頁面
@app.route('/order', methods=['GET', 'POST'])
def order():
    user_id = session.get('user_id')  # 取得登入用戶的 ID
    user = User.query.get(user_id) if user_id else None

    if request.method == 'POST':
        order_items = {}
        recommended_items = []  # 存儲推薦項目
        selected_categories = set()  # 存儲選擇的類別

        # 處理用戶選擇的商品
        for category, items in menu.items():
            order_items[category] = []
            for item in items:
                quantity = int(request.form.get(item['name'], 0))
                if quantity > 0:
                    order_items[category].append({
                        'name': item['name'],
                        'image': item['image'],
                        'quantity': quantity
                    })
                    selected_categories.add(category)

        # 根據所選類別推薦其他商品
        for category in selected_categories:
            for item in menu[category]:
                if item['name'] not in [i['name'] for i in order_items[category]]:
                    recommended_items.append(item)

        # 顯示訂單摘要
        return render_template(
            'order_summary.html',
            order_items=order_items,
            user=user,
            recommended_items=recommended_items
        )

    # 顯示訂單頁面
    return render_template('order.html', menu=menu, user=user, recommended_items=[])

@app.route('/add_to_order', methods=['POST'])
def add_to_order():
    item_name = request.form.get('item_name')
    # 在此處理將商品加入訂單的邏輯
    flash(f"已將 {item_name} 加入訂單！", "success")
    return redirect(url_for('order'))


if __name__ == '__main__':
    app.run(debug=True)
