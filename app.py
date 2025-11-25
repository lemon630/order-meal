import streamlit as st
import pandas as pd
import sqlite3
import json
import time
import base64
import io
from PIL import Image
from datetime import datetime

# ==========================================
# 1. 数据库与核心逻辑
# ==========================================
DB_FILE = "restaurant.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 尝试增加 description 字段 (兼容旧版本)
    try:
        c.execute("ALTER TABLE menu ADD COLUMN description TEXT")
    except:
        pass

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
            ("熔岩芝士牛肉堡", 88, "主菜", "https://images.unsplash.com/photo-1571062635316-2485521e14af?w=800",
             "精选澳洲谷饲牛肉，搭配浓郁切达芝士。"),
            ("夏日深蓝气泡水", 32, "饮品", "https://images.unsplash.com/photo-1575822369671-b0e633d71958?w=800",
             "清爽柠檬汁搭配蓝柑糖浆。"),
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


def add_dish_to_db(name, price, category, image_data, desc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO menu (name, price, category, image, description) VALUES (?, ?, ?, ?, ?)",
              (name, price, category, image_data, desc))
    conn.commit()
    conn.close()


def delete_dish_from_db(dish_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM menu WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()


# --- 图片处理工具函数 ---
def process_uploaded_image(uploaded_file, target_width=600):
    """
    读取上传的图片，调整大小，并转换为Base64字符串用于存储
    target_width: 目标宽度，默认600像素，防止数据库过大
    """
    try:
        image = Image.open(uploaded_file)

        # 计算新高度，保持比例
        w_percent = (target_width / float(image.size[0]))
        h_size = int((float(image.size[1]) * float(w_percent)))

        # 调整大小
        image = image.resize((target_width, h_size), Image.Resampling.LANCZOS)

        # 转换为字节流
        buffered = io.BytesIO()
        # 统一转为 PNG 格式保存
        image.save(buffered, format="PNG")

        # 转换为 Base64 字符串
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        return None


init_db()

# ==========================================
# 2. 状态管理
# ==========================================
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_dish' not in st.session_state:
    st.session_state.selected_dish = None
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'table_num' not in st.session_state:
    st.session_state.table_num = 1
if 'current_category' not in st.session_state:
    st.session_state.current_category = '全部'


def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()


def view_dish(dish_id):
    st.session_state.selected_dish = dish_id
    st.session_state.page = 'detail'
    st.rerun()


def filter_by_category(category_name):
    st.session_state.current_category = category_name
    st.session_state.page = 'home'
    st.rerun()


# ==========================================
# 3. UI 样式
# ==========================================

st.set_page_config(page_title="餐厅在线点餐系统", layout="wide", page_icon="🥗")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    .main-title { color: #2E7D32; font-size: 32px; font-weight: bold; margin-bottom: 20px; }

    /* 导航按钮 */
    .nav-btn button {
        background-color: #26C6DA; 
        color: white; border: none; border-radius: 5px; font-weight: bold;
        padding: 8px 15px; margin: 0 5px 10px 0;
    }
    .nav-btn button:hover { background-color: #00ACC1; }

    .stTextInput input { border: 1px solid #ddd; border-radius: 0px; }

    /* 分类筛选按钮 */
    .category-btn {
        background-color: #4CAF50; color: white; padding: 10px 15px;
        border-radius: 8px; text-align: center; font-weight: bold;
    }

    /* 菜品展示 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #eee; border-radius: 8px; padding: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .dish-name { font-size: 16px; font-weight: 500; color: #333; margin-top: 5px; }
    .dish-price { color: #D32F2F; font-weight: bold; font-size: 18px; }
    .detail-price-val { color: #D32F2F; font-size: 24px; font-weight: bold; }

    div.stButton > button { background-color: #26C6DA; color: white; border: none; border-radius: 5px; }
    div.stButton > button:hover { background-color: #00ACC1; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. 页面组件
# ==========================================

def render_navbar():
    st.markdown("<div class='main-title'>餐厅在线点餐系统</div>", unsafe_allow_html=True)
    nav_items = [("首页", "home"), ("我的餐车", "cart"), ("订单信息", "login")]
    with st.container():
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        cols = st.columns(len(nav_items))
        for i, (label, target) in enumerate(nav_items):
            with cols[i]:
                if st.button(label, key=f"nav_{i}", use_container_width=True):
                    st.session_state.page = target
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


render_navbar()
st.markdown("---")

# --- 首页 ---
if st.session_state.page == 'home':
    sc1, sc2 = st.columns([4, 1])
    with sc1:
        search_term = st.text_input("输入菜品名称...", key="search_input", label_visibility="collapsed")
    with sc2:
        if st.button("🔍 搜索", type="primary", use_container_width=True):
            st.rerun()

    st.markdown("### 🌿 经典菜品类名")
    menu_df = get_menu_data()
    categories = ["全部"] + list(menu_df['category'].unique())
    cat_cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        with cat_cols[i]:
            if st.button(cat, key=f"cat_{cat}", use_container_width=True):
                filter_by_category(cat)

    st.markdown("<br>", unsafe_allow_html=True)

    display_df = menu_df.copy()
    if st.session_state.current_category != '全部':
        display_df = display_df[display_df['category'] == st.session_state.current_category]
    if search_term:
        display_df = display_df[display_df['name'].str.contains(search_term, case=False)]
        st.markdown(f"#### 🔍 搜索结果: {search_term}")
    else:
        st.markdown(f"#### 🔥 推荐菜品 ({st.session_state.current_category})")

    dish_cols = st.columns(5)
    if display_df.empty:
        st.info("暂无该分类菜品")

    for index, row in display_df.iterrows():
        with dish_cols[index % 5]:
            with st.container(border=True):
                try:
                    st.image(row['image'], use_container_width=True)
                except:
                    st.image("https://via.placeholder.com/200", use_container_width=True)

                st.markdown(f"<div class='dish-name'>{row['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dish-price'>¥ {int(row['price'])}</div>", unsafe_allow_html=True)
                if st.button("查看详情", key=f"view_{row['id']}", use_container_width=True):
                    view_dish(row['id'])

# --- 详情页 ---
elif st.session_state.page == 'detail':
    if st.session_state.selected_dish is None:
        go_to('home')
    menu_df = get_menu_data()
    dish = menu_df[menu_df['id'] == st.session_state.selected_dish].iloc[0]

    if st.button("⬅ 返回首页"):
        go_to('home')
    st.markdown("---")

    d_col1, d_col2 = st.columns([1, 1.5])
    with d_col1:
        try:
            st.image(dish['image'], use_container_width=True)
        except:
            st.image("https://via.placeholder.com/400", use_container_width=True)
    with d_col2:
        st.markdown(f"## {dish['name']}")
        desc_text = dish['description'] if dish['description'] else "美味推荐。"
        st.markdown(f"<span style='color:#D32F2F; font-size: 14px;'>描述：{desc_text}</span>", unsafe_allow_html=True)
        st.markdown(f"价格：<span class='detail-price-val'>¥ {int(dish['price'])}</span>", unsafe_allow_html=True)
        st.markdown(f"促销：<span style='color:red'>9 折</span>", unsafe_allow_html=True)

        c_q1, c_q2 = st.columns([1, 3])
        with c_q1:
            qty = st.number_input("数量", min_value=1, value=1, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("加入餐车", type="primary"):
            if dish['id'] in st.session_state.cart:
                st.session_state.cart[dish['id']] += qty
            else:
                st.session_state.cart[dish['id']] = qty
            st.toast(f"已加入 {qty} 份 {dish['name']}")

# --- 购物车 ---
elif st.session_state.page == 'cart':
    st.markdown("### 🛒 我的餐车")
    if not st.session_state.cart:
        st.info("购物车是空的")
        if st.button("去点餐"):
            go_to('home')
    else:
        menu_df = get_menu_data()
        total_price = 0
        cart_details = []
        for item_id, qty in st.session_state.cart.items():
            item_row = menu_df[menu_df['id'] == item_id]
            if not item_row.empty:
                item = item_row.iloc[0]
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
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 确认下单", type="primary", use_container_width=True):
                add_order_to_db(st.session_state.table_num, cart_details, total_price)
                st.session_state.cart = {}
                st.balloons()
                st.success("下单成功！")
                time.sleep(2)
                go_to('home')

# --- 登录与后台 ---
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
            with st.expander(f"[{ostatus}] 桌号 {otable} - ¥{ototal} ({otime})"):
                st.table(pd.DataFrame(json.loads(ojson)))
                if "待" in ostatus:
                    if st.button("完成订单", key=f"finish_{oid}"):
                        update_order_status(oid, "已完成")
                        st.rerun()

    with tab2:
        st.write("#### 添加新菜品")
        with st.form("add_dish_form"):
            n = st.text_input("名称")
            p = st.number_input("价格", min_value=1)
            c = st.text_input("分类 (如: 川菜, 饮品)")
            d = st.text_input("描述")

            # --- 图片上传区域 ---
            st.markdown("---")
            st.write("🖼️ **图片设置** (二选一)")
            img_mode = st.radio("选择图片来源", ["使用网络链接 (URL)", "上传本地图片"], horizontal=True)

            final_img_str = ""

            if img_mode == "使用网络链接 (URL)":
                img_url = st.text_input("输入图片链接")
                if img_url:
                    final_img_str = img_url
                    st.image(img_url, width=200, caption="预览")
            else:
                uploaded_file = st.file_uploader("选择本地图片 (jpg/png)", type=['jpg', 'png', 'jpeg'])
                # 添加调整大小的滑块
                img_width = st.slider("调整图片宽度 (像素) - 防止数据库过大", 200, 1000, 600)

                if uploaded_file is not None:
                    # 处理图片
                    processed_img = process_uploaded_image(uploaded_file, img_width)
                    if processed_img:
                        final_img_str = processed_img
                        st.success(f"图片处理成功！宽度已调整为 {img_width}px")
                        st.image(final_img_str, caption="预览 (已压缩)", width=300)
                    else:
                        st.error("图片处理失败，请重试")

            st.markdown("---")

            if st.form_submit_button("确认添加菜品"):
                if not n:
                    st.error("请输入菜名")
                elif not final_img_str:
                    st.warning("请设置一张图片")
                else:
                    add_dish_to_db(n, p, c, final_img_str, d)
                    st.success(f"✅ 成功添加: {n}")
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")
        st.write("现有菜品")
        current_menu = get_menu_data()
        st.dataframe(current_menu[['id', 'name', 'price', 'category']], hide_index=True)

        del_id = st.number_input("输入要删除的ID", min_value=0)
        if st.button("删除该ID菜品"):
            delete_dish_from_db(del_id)
            st.rerun()











