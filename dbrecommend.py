import sqlite3
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# 連接到 SQLite 資料庫
conn = sqlite3.connect('restaurant.db')
cursor = conn.cursor()

# 確認表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("資料表清單:", tables)

# 確認表結構
table_name = "orders"
cursor.execute(f"PRAGMA table_info({table_name});")
print(f"{table_name} 表結構:", cursor.fetchall())

# 從資料表中讀取數據
query = "SELECT * FROM orders"
df = pd.read_sql_query(query, conn)
print("原始數據:\n", df.head())

# 修改列名
df.rename(columns={"user_id": "customer_id", "item": "product_id"}, inplace=True)

# 構建客戶-產品矩陣
if not df.empty:
    customer_product_matrix = df.pivot_table(index='customer_id', columns='product_id', values='quantity', fill_value=0)
    print("客戶-產品矩陣:\n", customer_product_matrix.head())

    # 計算客戶相似度
    customer_similarity = cosine_similarity(customer_product_matrix)
    customer_similarity_df = pd.DataFrame(customer_similarity, index=customer_product_matrix.index, columns=customer_product_matrix.index)

    # 推薦函數
    def recommend_products(customer_id, top_n=5):
        similar_customers = customer_similarity_df[customer_id].sort_values(ascending=False).index[1:]
        recommendations = customer_product_matrix.loc[similar_customers].mean().sort_values(ascending=False).head(top_n)
        return recommendations
else:
    print("數據表為空，無法構建矩陣和進行推薦。")

conn.close()
