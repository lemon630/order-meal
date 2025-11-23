import streamlit as st
import pandas as pd
import sqlite3
import json
import time
from datetime import datetime

# ==========================================
# 1. 数据库与核心逻辑 (后端保持稳定)
# ==========================================
DB_FILE = "restaurant.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 增加 description 字段用于详情页描述
    try:
        c.execute("ALTER TABLE menu ADD COLUMN description TEXT")
    except:
        pass  # 如果字段已存在忽略

    c.execute('''CREATE TABLE IF NOT EXISTS menu
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, price REAL, category TEXT, image TEXT, description TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  table_num INTEGER, items_json TEXT, total_price REAL, status TEXT, timestamp TEXT)''')

    # 初始化数据
    c.execute('SELECT count(*) FROM menu')
    if c.fetchone()[0] == 0:
        default_menu = [
            ("招牌菲力牛排", 50, "西餐", "https://images.unsplash.com/photo-1600891964092-4316c288032e?w=800",
             "精选澳洲谷饲牛肉，肉质鲜嫩多汁，搭配秘制黑胡椒酱。"),
            ("扬州炒饭", 20, "主食", "https://images.unsplash.com/photo-1603133872878-684f108fd118?w=800",
             "粒粒分明，配料丰富，经典的江南风味。"),
            ("糖醋里脊", 30, "苏菜", "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=800",
             "酸甜可口，色泽红亮，外酥里嫩，老少皆宜的经典名菜。"),
            ("砂锅土豆", 20, "家常", "https://images.unsplash.com/photo-1592417817098-8fd3d9eb14a5?w=800",
             "土豆软糯入味，砂锅慢炖，香气扑鼻。"),
            ("豚骨拉面", 20, "面食", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800",
             "浓郁骨汤，劲道面条，温暖你的胃。"),
            ("三文鱼寿司", 20, "日料", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=800",
             "新鲜三文鱼，口感肥美，芥末点缀。"),
        ]
        c.executemany('INSERT INTO menu (name, price, category, image, description) VALUES (?,?,?,?,?)', default_menu)
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
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO orders (table_num, items_json, total_price, status, timestamp) VALUES (?, ?, ?, ?, ?)",
              (table_num, items_json, total, "待处理", time_str))
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


def add_dish_to_db(name, price, category, image_url, desc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO menu (name, price, category, image, description) VALUES (?, ?, ?, ?, ?)",
              (name, price, category, image_url, desc))
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
# 2. 状态管理 (实现页面跳转)
# ==========================================

# 初始化 Session State
if 'page' not in st.session_state:
    st.session_state.page = 'home'  # 当前页面: home, detail, admin, cart
if 'selected_dish' not in st.session_state:
    st.session_state.selected_dish = None  # 当前选中的菜品 ID
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'table_num' not in st.session_state:
    st.session_state.table_num = 1


def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()


def view_dish(dish_id):
    st.session_state.selected_dish = dish_id
    st.session_state.page = 'detail'
    st.rerun()


# ==========================================
# 3. UI 样式 (复刻截图风格)
# ==========================================

st.set_page_config(page_title="餐厅在线点餐系统", layout="wide", page_icon="🥗")

# 注入 CSS：白底绿调，模仿截图 1 和 2
st.markdown("""
<style>
    /* 全局背景设为白色 */
    .stApp {
        background-color: #FFFFFF;
    }

    /* 顶部标题 - 绿色 */
    .main-title {
        color: #2E7D32;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* 导航栏按钮模拟 */
    .nav-btn {
        color: #555;
        font-size: 16px;
        padding: 10px;
        cursor: pointer;
        text-align: center;
    }
    .nav-btn:hover {
        color: #2E7D32;
        font-weight: bold;
    }

    /* 搜索框样式 */
    .stTextInput input {
        border: 1px solid #ddd;
        border-radius: 0px;
    }

    /* 分类按钮 - 绿色圆角矩形 (截图1中间部分) */
    .category-btn {
        background-color: #4CAF50; /* 鲜艳的绿 */
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
    }

    /* 菜品卡片 */
    .dish-card-img {
        border-radius: 8px;
        object-fit: cover;
    }
    .dish-name {
        font-size: 16px;
        font-weight: 500;
        color: #333;
        margin-top: 5px;
    }
    .dish-price {
        color: #D32F2F; /* 红色价格 */
        font-weight: bold;
        font-size: 18px;
    }

    /* 详情页样式 (截图2) */
    .detail-title {
        font-size: 28px;
        font-weight: bold;
        color: #333;
    }
    .detail-desc {
        color: #D32F2F; /* 描述部分的红色文字 */
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 20px;
    }
    .detail-price-lbl {
        color: #666;
    }
    .detail-price-val {
        color: #D32F2F;
        font-size: 24px;
        font-weight: bold;
    }

    /* 自定义按钮颜色 */
    div.stButton > button {
        background-color: #26C6DA; /* 青色按钮 (截图2中的加入餐车) */
        color: white;
        border: none;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        background-color: #00ACC1;
    }

    /* 隐藏默认侧边栏，我们用顶部导航代替 */
    [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. 页面组件渲染
# ==========================================

# --- 顶部导航栏 (模拟截图顶部) ---
def render_navbar():
    c1, c2, c3 = st.columns([2, 5, 2])
    with c1:
        st.markdown("<div class='main-title'>餐厅在线点餐系统</div>", unsafe_allow_html=True)
    with c2:
        # 模拟导航链接
        cols = st.columns(7)
        nav_items = [("首页", "home"), ("系统公告", "home"), ("在线交流", "home"),
                     ("我的餐车", "cart"), ("订单信息", "admin"), ("餐饮评价", "home"), ("个人信息", "home")]
        for i, (label, target) in enumerate(nav_items):
            with cols[i]:
                if st.button(label, key=f"nav_{i}", use_container_width=True):
                    # 如果需要密码校验的页面
                    if target == "admin":
                        st.session_state.page = "login"
                    else:
                        st.session_state.page = target
                    st.rerun()


render_navbar()
st.markdown("---")

# ==========================================
# PAGE: 首页 (Home)
# ==========================================
if st.session_state.page == 'home':

    # 1. 搜索栏区域
    sc1, sc2 = st.columns([4, 1])
    with sc1:
        search_term = st.text_input("搜索菜名", placeholder="输入菜品名称...", label_visibility="collapsed")
    with sc2:
        st.button("🔍 搜索", type="primary", use_container_width=True)

    # 2. 经典菜品类名 (绿色方块)
    st.markdown("### 🌿 经典菜品类名")
    menu_df = get_menu_data()
    categories = list(menu_df['category'].unique())

    # 显示前6个分类作为绿色按钮
    cat_cols = st.columns(6)
    for i, cat in enumerate(categories[:6]):
        with cat_cols[i]:
            # 使用 Streamlit 的 container 模拟带颜色的块
            st.markdown(f"""
            <div style="background-color: #4CAF50; color: white; padding: 10px; border-radius: 8px; text-align: center; cursor: pointer;">
                {cat}菜
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. 菜品展示 (推荐菜品 / 热销菜品)
    if search_term:
        menu_df = menu_df[menu_df['name'].str.contains(search_term)]
        st.markdown(f"#### 🔍 搜索结果: {search_term}")
    else:
        st.markdown("#### 🔥 推荐菜品 / 热销菜品")

    # 网格布局展示菜品
    dish_cols = st.columns(5)  # 一行5个，模仿截图

    for index, row in menu_df.iterrows():
        with dish_cols[index % 5]:
            with st.container(border=True):
                # 图片点击跳转详情 (逻辑上用按钮覆盖图片实现)
                try:
                    st.image(row['image'], use_container_width=True)
                except:
                    st.image("https://via.placeholder.com/200", use_container_width=True)

                st.markdown(f"<div class='dish-name'>{row['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dish-price'>¥ {int(row['price'])}</div>", unsafe_allow_html=True)

                # 点击查看详情
                if st.button("查看详情", key=f"view_{row['id']}", use_container_width=True):
                    view_dish(row['id'])

# ==========================================
# PAGE: 详情页 (Detail) - 复刻截图 2
# ==========================================
elif st.session_state.page == 'detail':
    if st.session_state.selected_dish is None:
        go_to('home')

    # 获取当前菜品数据
    menu_df = get_menu_data()
    dish = menu_df[menu_df['id'] == st.session_state.selected_dish].iloc[0]

    # 顶部面包屑
    if st.button("⬅ 返回首页"):
        go_to('home')

    st.markdown("---")

    # 左右布局：左图，右信息
    d_col1, d_col2 = st.columns([1, 1.5])

    with d_col1:
        try:
            st.image(dish['image'], use_container_width=True)
        except:
            st.image("https://via.placeholder.com/400", use_container_width=True)
        # 缩略图模拟
        st.image(dish['image'], width=60)

    with d_col2:
        st.markdown(f"<div class='detail-title'>{dish['name']} 👍 2</div>", unsafe_allow_html=True)

        # 描述文字 (模仿截图红色文字)
        desc_text = dish['description'] if dish['description'] else "这道菜色泽红亮，口感鲜美，是本店的招牌推荐菜肴。选用上等食材，经过大厨精心烹饪，味道醇厚。"
        st.markdown(f"<div class='detail-desc'>描述：{desc_text}</div>", unsafe_allow_html=True)

        st.markdown(
            f"<span class='detail-price-lbl'>价格：</span> <span class='detail-price-val'>¥ {int(dish['price'])}</span>",
            unsafe_allow_html=True)
        st.markdown(f"<span class='detail-price-lbl'>促销：</span> <span style='color:red'>9 折</span>",
                    unsafe_allow_html=True)

        # 数量选择
        c_q1, c_q2 = st.columns([1, 3])
        with c_q1:
            qty = st.number_input("数量", min_value=1, value=1, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # 加入购物车按钮 (青色)
        if st.button("加入餐车", type="primary"):
            if dish['id'] in st.session_state.cart:
                st.session_state.cart[dish['id']] += qty
            else:
                st.session_state.cart[dish['id']] = qty
            st.success(f"已将 {qty} 份 {dish['name']} 加入餐车！")
            time.sleep(1)  # 稍微停顿
            go_to('home')  # 返回首页继续点单

    # 底部评论区 (模拟)
    st.markdown("---")
    st.markdown("#### 菜品评价 (2)")

    with st.container(border=True):
        st.markdown("**user** &nbsp;&nbsp;&nbsp; <span style='color:gray'>味道真心不错</span>", unsafe_allow_html=True)
        st.caption("2024-08-05 20:32:22")

    with st.container(border=True):
        st.markdown("**user** &nbsp;&nbsp;&nbsp; <span style='color:gray'>真的很喜欢，下次还来</span>",
                    unsafe_allow_html=True)
        st.caption("2024-08-05 20:32:30")

# ==========================================
# PAGE: 购物车 (Cart)
# ==========================================
elif st.session_state.page == 'cart':
    st.markdown("### 🛒 我的餐车")
    if not st.session_state.cart:
        st.info("购物车是空的，快去首页选购吧！")
        if st.button("去点餐"):
            go_to('home')
    else:
        menu_df = get_menu_data()
        total_price = 0
        cart_details = []

        # 显示购物车表格
        for item_id, qty in st.session_state.cart.items():
            item = menu_df[menu_df['id'] == item_id].iloc[0]
            subtotal = item['price'] * qty
            total_price += subtotal
            cart_details.append({"name": item['name'], "price": item['price'], "qty": qty, "subtotal": subtotal})

            with st.container(border=True):
                cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 1])
                cc1.markdown(f"**{item['name']}**")
                cc2.markdown(f"¥{item['price']}")
                cc3.markdown(f"x {qty}")
                if cc4.button("删除", key=f"del_cart_{item_id}"):
                    del st.session_state.cart[item_id]
                    st.rerun()

        st.divider()
        st.markdown(f"### 总计: <span style='color:red'>¥{total_price}</span>", unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.session_state.table_num = st.selectbox("选择桌号", range(1, 21), key="cart_table")
        with col_b2:
            st.markdown("<br>", unsafe_allow_html=True)  # 占位
            if st.button("🚀 确认下单", type="primary", use_container_width=True):
                add_order_to_db(st.session_state.table_num, cart_details, total_price)
                st.session_state.cart = {}
                st.balloons()
                st.success("下单成功！正在为您制作...")
                time.sleep(2)
                go_to('home')

# ==========================================
# PAGE: 登录页 (Login)
# ==========================================
elif st.session_state.page == 'login':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### 🔐 管理员登录")
        pwd = st.text_input("请输入密码", type="password")
        if st.button("登录"):
            if pwd == "123456":
                go_to('admin')
            else:
                st.error("密码错误")
        if st.button("返回首页"):
            go_to('home')

# ==========================================
# PAGE: 后台管理 (Admin)
# ==========================================
elif st.session_state.page == 'admin':
    st.markdown("### 👨‍💻 订单管理系统")
    if st.button("⬅ 退出登录"):
        go_to('home')

    tab1, tab2 = st.tabs(["订单处理", "菜品管理"])

    with tab1:
        if st.button("刷新订单"):
            st.rerun()
        orders = get_orders_data()
        for order in orders:
            oid, otable, ojson, ototal, ostatus, otime = order
            color = "green" if "已" in ostatus else "red"
            with st.expander(f"[{ostatus}] 桌号 {otable} - ¥{ototal} ({otime})"):
                st.table(pd.DataFrame(json.loads(ojson)))
                if "待" in ostatus:
                    if st.button("完成订单", key=f"finish_{oid}"):
                        update_order_status(oid, "已完成")
                        st.rerun()

    with tab2:
        st.write("添加新菜品")
        with st.form("add_dish_form"):
            n = st.text_input("名称")
            p = st.number_input("价格", min_value=1)
            c = st.text_input("分类 (如: 川菜, 饮品)")
            i = st.text_input("图片链接")
            d = st.text_input("描述")
            if st.form_submit_button("添加"):
                add_dish_to_db(n, p, c, i, d)
                st.success("添加成功")
                st.rerun()

        st.markdown("---")
        st.write("现有菜品")
        current_menu = get_menu_data()
        for idx, row in current_menu.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"{row['name']} - ¥{row['price']}")
            if c3.button("删除", key=f"del_dish_{row['id']}"):
                delete_dish_from_db(row['id'])
                st.rerun()










