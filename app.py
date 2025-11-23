import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime

# ==========================================
# 1. 数据库逻辑 (适配云端)
# ==========================================
DB_FILE = "restaurant.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, price REAL, category TEXT, image TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  table_num INTEGER, items_json TEXT, total_price REAL, status TEXT, timestamp TEXT)''')

    # 初始化默认数据
    c.execute('SELECT count(*) FROM menu')
    if c.fetchone()[0] == 0:
        default_menu = [
            ("熔岩芝士牛肉堡", 88, "主菜", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800"),
            ("加州阳光鲜橙汁", 32, "饮品", "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=800"),
            ("西西里罗勒意面", 68, "主食", "https://images.unsplash.com/photo-1621996346529-cd287300f69a?w=800"),
            ("脆皮炸鸡分享桶", 55, "小吃", "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=800"),
        ]
        c.executemany('INSERT INTO menu (name, price, category, image) VALUES (?,?,?,?)', default_menu)
        conn.commit()
    conn.close()


def get_menu_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM menu", conn)
    conn.close()
    return df


def add_order_to_db(table_num, items, total):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    items_json = json.dumps(items, ensure_ascii=False)
    time_str = datetime.now().strftime("%H:%M")
    c.execute("INSERT INTO orders (table_num, items_json, total_price, status, timestamp) VALUES (?, ?, ?, ?, ?)",
              (table_num, items_json, total, "新订单 ⚡", time_str))
    conn.commit()
    conn.close()


def get_orders_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def update_order_status(order_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()


def add_dish_to_db(name, price, category, image_url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO menu (name, price, category, image) VALUES (?, ?, ?, ?)", (name, price, category, image_url))
    conn.commit()
    conn.close()


def delete_dish_from_db(dish_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM menu WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()


init_db()

# ==========================================
# 2. 🍊 活力橙 UI 设计 (CSS)
# ==========================================

st.set_page_config(page_title="Sunshine Order", layout="wide", page_icon="🍊")

st.markdown("""
<style>
    /* 1. 活力橙渐变背景 */
    .stApp {
        background: linear-gradient(135deg, #FF9966 0%, #FF5E62 100%);
        background-attachment: fixed;
    }

    /* 2. 标题颜色：白色，带阴影 */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        font-family: 'Segoe UI', sans-serif;
    }

    /* 3. 卡片毛玻璃效果 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 15px;
        border: none; /* 去掉边框，用阴影替代 */
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    }

    /* 4. 按钮：鲜艳的橙红色 */
    div.stButton > button {
        background: linear-gradient(to right, #FF512F, #DD2476);
        color: white !important;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(221, 36, 118, 0.4);
        transition: transform 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
    }

    /* 5. 侧边栏：半透明白 */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.9);
    }
    section[data-testid="stSidebar"] h1, p, span, label {
        color: #FF5E62 !important;
        text-shadow: none;
    }

    /* 6. 价格标签 */
    .price-tag {
        color: #FF512F;
        font-size: 26px;
        font-weight: 900;
    }

    /* 7. 分类胶囊 */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: #333 !important;
        border-radius: 10px;
    }

    /* 修复输入框文字颜色 */
    .stTextInput input {
        color: #333 !important;
    }
    p, label {
        color: #333 !important;
    }
    /* 特例：侧边栏的文字保持橙色 */
    section[data-testid="stSidebar"] p {
         color: #FF5E62 !important;
    }
</style>
""", unsafe_allow_html=True)

if 'cart' not in st.session_state:
    st.session_state.cart = {}

# ==========================================
# 3. 业务逻辑
# ==========================================

# 侧边栏
st.sidebar.markdown("# 🍊 橙意厨房")
mode = st.sidebar.radio("MENU", ["🥄 顾客点单", "👨‍🍳 厨师后台"])
st.sidebar.markdown("---")
st.sidebar.info("💡 手机同步查看订单")

if mode == "🥄 顾客点单":
    st.markdown("## 🌞 今天想吃点什么？")

    # 顶部透明卡片
    with st.container(border=True):
        col_t1, col_t2 = st.columns([1, 4])
        with col_t1:
            st.markdown("### 📍 桌号")
        with col_t2:
            table_num = st.selectbox("", range(1, 21), label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    menu_df = get_menu_data()

    c_left, c_right = st.columns([2.5, 1])

    with c_left:
        cats = ["全部"] + list(menu_df['category'].unique())
        selected_cat = st.pills("✨ 热门分类", cats, default="全部")

        if selected_cat != "全部":
            menu_df = menu_df[menu_df['category'] == selected_cat]

        st.markdown("<br>", unsafe_allow_html=True)

        cols = st.columns(2)
        for index, row in menu_df.iterrows():
            with cols[index % 2]:
                with st.container(border=True):
                    try:
                        st.image(row['image'], use_container_width=True)
                    except:
                        st.image("https://via.placeholder.com/400x300?text=Delicious", use_container_width=True)

                    st.markdown(f"#### {row['name']}")
                    st.caption(f"{row['category']}")

                    c_price, c_btn = st.columns([1, 1.2])
                    with c_price:
                        st.markdown(f"<div class='price-tag'>¥{int(row['price'])}</div>", unsafe_allow_html=True)
                    with c_btn:
                        if st.button("🔥 加入", key=f"add_{row['id']}", use_container_width=True):
                            if row['id'] in st.session_state.cart:
                                st.session_state.cart[row['id']] += 1
                            else:
                                st.session_state.cart[row['id']] = 1
                            st.toast(f"已添加 {row['name']} 😋")

    with c_right:
        with st.container(border=True):
            st.markdown("### 🧾 购物车")
            if not st.session_state.cart:
                st.info("快去选点好吃的！")
            else:
                total = 0
                for item_id, qty in st.session_state.cart.items():
                    item_row = menu_df[menu_df['id'] == item_id]
                    if not item_row.empty:
                        item = item_row.iloc[0]
                        total += item['price'] * qty

                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{item['name']}**")
                        c2.markdown(f"x{qty}")
                        if c3.button("🗑️", key=f"del_{item_id}"):
                            if st.session_state.cart[item_id] > 1:
                                st.session_state.cart[item_id] -= 1
                            else:
                                del st.session_state.cart[item_id]
                            st.rerun()

                st.divider()
                st.markdown(f"<h3 style='text-align: right; color: #FF512F;'>¥{total}</h3>", unsafe_allow_html=True)

                if st.button("🚀 立即下单", type="primary", use_container_width=True):
                    cart_items = []
                    for pid, pqty in st.session_state.cart.items():
                        prow = menu_df[menu_df['id'] == pid].iloc[0]
                        cart_items.append({"name": prow['name'], "qty": pqty, "price": prow['price']})

                    add_order_to_db(table_num, cart_items, total)
                    st.session_state.cart = {}
                    st.balloons()
                    st.success("订单已飞向厨房！👨‍🍳")

elif mode == "👨‍🍳 厨师后台":
    st.markdown("## 🔒 后台管理")
    pwd = st.sidebar.text_input("管理员密码", type="password")

    # 🔔 默认密码: 123456
    if pwd == "123456":
        with st.container(border=True):
            tab1, tab2 = st.tabs(["📝 订单监控", "🥘 菜品管理"])

            with tab1:
                if st.button("🔄 刷新数据"):
                    st.rerun()
                orders = get_orders_data()
                if not orders:
                    st.info("暂无订单")

                for order in orders:
                    oid, otable, ojson, ototal, ostatus, otime = order
                    # 根据状态显示不同样式
                    if "新" in ostatus:
                        st.warning(f"🔔 [新] {otime} | 桌号 {otable} | ¥{ototal}")
                    else:
                        st.success(f"✅ [完] {otime} | 桌号 {otable} | ¥{ototal}")

                    with st.expander("查看详情"):
                        items = json.loads(ojson)
                        st.table(pd.DataFrame(items))
                        if "新" in ostatus:
                            if st.button("出餐完成", key=f"done_{oid}"):
                                update_order_status(oid, "已出餐 ✅")
                                st.rerun()

            with tab2:
                st.markdown("#### 上架新菜")
                with st.form("add_dish"):
                    n = st.text_input("菜名")
                    p = st.number_input("价格", min_value=1)
                    c = st.selectbox("分类", ["主菜", "饮品", "主食", "小吃"])
                    i = st.text_input("图片链接 (Unsplash URL)")
                    if st.form_submit_button("发布"):
                        if not i: i = "https://via.placeholder.com/300"
                        add_dish_to_db(n, p, c, i)
                        st.success("发布成功！")
                        st.rerun()

                st.divider()
                st.markdown("#### 现有菜单")
                cur_menu = get_menu_data()
                st.dataframe(cur_menu[['name', 'price', 'category']], hide_index=True)

                # 简单删除功能
                del_id = st.number_input("输入要删除的ID", min_value=0)
                if st.button("删除该ID菜品"):
                    delete_dish_from_db(del_id)
                    st.rerun()
    else:
        st.error("请输入密码进入后台")









