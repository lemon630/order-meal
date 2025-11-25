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
# 1. 后端逻辑 (保持稳定)
# ==========================================
DB_FILE = "restaurant.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    # 初始化默认数据
    c.execute('SELECT count(*) FROM menu')
    if c.fetchone()[0] == 0:
        default_menu = [
            ("经典牛肉汉堡", 45, "汉堡", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600",
             "澳洲安格斯牛肉，搭配秘制酱料。"),
            ("意式腊肠披萨", 88, "披萨", "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=600",
             "传统薄底，满满的芝士与腊肠。"),
            ("日式三文鱼寿司", 32, "寿司", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=600",
             "新鲜深海三文鱼，口感软糯。"),
            ("香脆炸薯条", 22, "小吃", "https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=600",
             "金黄酥脆，搭配番茄酱。"),
            ("草莓奶油蛋糕", 35, "甜点", "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=600",
             "甜蜜草莓，入口即化。"),
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


def process_uploaded_image(uploaded_file, target_width=600):
    try:
        image = Image.open(uploaded_file)
        w_percent = (target_width / float(image.size[0]))
        h_size = int((float(image.size[1]) * float(w_percent)))
        image = image.resize((target_width, h_size), Image.Resampling.LANCZOS)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception:
        return None


init_db()

# ==========================================
# 2. 状态管理
# ==========================================
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'table_num' not in st.session_state: st.session_state.table_num = 1
if 'current_category' not in st.session_state: st.session_state.current_category = '全部'
if 'page' not in st.session_state: st.session_state.page = 'dashboard'  # dashboard, admin


def add_to_cart(item_id):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id] += 1
    else:
        st.session_state.cart[item_id] = 1
    st.toast("✅ 已加入购物车")


def remove_from_cart(item_id):
    if item_id in st.session_state.cart:
        if st.session_state.cart[item_id] > 1:
            st.session_state.cart[item_id] -= 1
        else:
            del st.session_state.cart[item_id]
    st.rerun()


# ==========================================
# 3. 🎨 CSS 深度定制 (复刻设计图)
# ==========================================

st.set_page_config(page_title="Gourmet OS", layout="wide", page_icon="🔥")

st.markdown("""
<style>
    /* 1. 核心配色: 深空灰黑背景 */
    .stApp {
        background-color: #1F1D2B;
    }

    /* 2. 侧边栏配色 */
    [data-testid="stSidebar"] {
        background-color: #1F1D2B;
        border-right: 1px solid #252836;
    }

    /* 3. 卡片样式 (拟态风格) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #252836;
        border: 1px solid #2D303E;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }

    /* 4. 字体颜色 */
    h1, h2, h3, h4, p, span, div, label {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    .secondary-text {
        color: #ABBBC2 !important;
        font-size: 14px;
    }

    /* 5. 按钮 - 活力橙 */
    div.stButton > button {
        background-color: #EA7C69;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(234, 124, 105, 0.3);
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #FF8E7A;
        transform: translateY(-2px);
    }

    /* 6. 搜索框 & 输入框 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #2D303E !important;
        color: white !important;
        border: 1px solid #393C49 !important;
        border-radius: 8px;
    }

    /* 7. 分类按钮 (自定义胶囊) */
    .category-btn {
        display: inline-block;
        background-color: #252836;
        color: #EA7C69;
        padding: 8px 16px;
        border-radius: 20px;
        margin-right: 10px;
        border: 1px solid #393C49;
        cursor: pointer;
        text-align: center;
        transition: 0.3s;
    }
    .category-btn:hover {
        background-color: #EA7C69;
        color: white;
    }
    .category-active {
        background-color: #EA7C69;
        color: white;
    }

    /* 8. 价格高亮 */
    .price-tag {
        color: #EA7C69 !important;
        font-weight: bold;
        font-size: 18px;
    }

    /* 9. 滚动条美化 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1F1D2B; 
    }
    ::-webkit-scrollbar-thumb {
        background: #393C49; 
        border-radius: 4px;
    }

    /* 隐藏顶部 padding */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 界面布局逻辑
# ==========================================

# --- A. 左侧侧边栏 (导航) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3448/3448636.png", width=60)  # Logo模拟
    st.markdown("### **Gourmet**")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🏠 首页大厅", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()
    if st.button("⚙️ 后台管理", use_container_width=True):
        st.session_state.page = 'admin'
        st.rerun()

    st.markdown("---")
    st.info("🔥 24小时营业中")

# --- B. 主内容区域 (Dashboard) ---
if st.session_state.page == 'dashboard':

    # 使用列布局：左边是菜单(3份宽)，右边是购物车(1.2份宽)
    col_menu, col_spacer, col_cart = st.columns([3, 0.1, 1.3])

    # === 左侧：菜单区 ===
    with col_menu:
        # 1. 顶部 Header
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown("## **欢迎回来, 请点餐 👋**")
            st.caption(f"📅 {datetime.now().strftime('%Y年%m月%d日')} | 发现今天的美味")
        with c2:
            search = st.text_input("🔍 搜索...", placeholder="想吃点什么?", label_visibility="collapsed")

        # 2. 分类筛选
        menu_df = get_menu_data()
        categories = ["全部"] + list(menu_df['category'].unique())

        # 模拟水平滚动分类栏
        st.markdown("<br>", unsafe_allow_html=True)
        cols_cat = st.columns(len(categories))
        for i, cat in enumerate(categories):
            with cols_cat[i]:
                # 简单的逻辑：点击按钮刷新页面并设置分类
                # 这里为了 UI 美观，用 Streamlit 原生按钮模拟
                if st.button(cat, key=f"cat_{i}", use_container_width=True):
                    st.session_state.current_category = cat
                    st.rerun()

        st.markdown("---")

        # 3. 菜品网格 (重点)
        st.markdown(
            f"### **{'🔥 热门推荐' if st.session_state.current_category == '全部' else st.session_state.current_category}**")

        # 筛选数据
        display_df = menu_df.copy()
        if st.session_state.current_category != '全部':
            display_df = display_df[display_df['category'] == st.session_state.current_category]
        if search:
            display_df = display_df[display_df['name'].str.contains(search, case=False)]

        # 网格渲染 (每行3个，为了保持卡片美观)
        dish_cols = st.columns(3)
        for index, row in display_df.iterrows():
            with dish_cols[index % 3]:
                # 卡片容器
                with st.container(border=True):
                    # 图片居中
                    try:
                        st.image(row['image'], use_container_width=True)
                    except:
                        st.image("https://via.placeholder.com/200", use_container_width=True)

                    st.markdown(f"**{row['name']}**")
                    st.markdown(f"<span class='secondary-text'>{row['category']}</span>", unsafe_allow_html=True)

                    c_price, c_add = st.columns([1, 1])
                    with c_price:
                        st.markdown(f"<span class='price-tag'>¥{int(row['price'])}</span>", unsafe_allow_html=True)
                    with c_add:
                        if st.button("➕", key=f"add_{row['id']}"):
                            add_to_cart(row['id'])

    # === 右侧：购物车区 (固定展示) ===
    with col_cart:
        # 模拟深色面板
        with st.container(border=True):
            st.markdown("### **🛒 订单详情**")
            st.caption(f"订单号 #{int(time.time()) % 10000}")

            # 配送/堂食切换 (视觉效果)
            st.radio("用餐方式", ["堂食 Dine In", "外带 To Go"], horizontal=True, label_visibility="collapsed")

            st.markdown("---")

            # 桌号选择
            st.markdown("**📍 选择桌号**")
            st.session_state.table_num = st.selectbox("", range(1, 21), label_visibility="collapsed")

            st.markdown("<br>", unsafe_allow_html=True)

            # 购物车列表
            if not st.session_state.cart:
                st.info("购物车是空的")
                st.image("https://cdn-icons-png.flaticon.com/512/2038/2038854.png", width=100)
            else:
                total_price = 0
                cart_items_for_db = []

                # 限制高度，防止列表过长
                with st.container(height=400):
                    for item_id, qty in st.session_state.cart.items():
                        item = menu_df[menu_df['id'] == item_id].iloc[0]
                        subtotal = item['price'] * qty
                        total_price += subtotal
                        cart_items_for_db.append({"name": item['name'], "price": item['price'], "qty": qty})

                        # 单行购物车项设计
                        c1, c2, c3 = st.columns([2, 1, 1])
                        with c1:
                            st.image(item['image'], width=40)
                            st.write(f"{item['name']}")
                            st.caption(f"¥{item['price']}")
                        with c2:
                            st.write(f"x {qty}")
                        with c3:
                            if st.button("🗑️", key=f"del_{item_id}"):
                                remove_from_cart(item_id)
                        st.markdown("---")

                # 底部结算区
                st.markdown("### **总计摘要**")

                sc1, sc2 = st.columns([2, 1])
                sc1.write("商品总额")
                sc2.write(f"¥{total_price}")

                sc1.write("服务费")
                sc2.write("¥0")

                st.markdown("---")

                ft1, ft2 = st.columns([1, 1])
                ft1.markdown("#### **总计**")
                ft2.markdown(f"<span class='price-tag'>¥{total_price}</span>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("🚀 确认下单 Payment", type="primary", use_container_width=True):
                    add_order_to_db(st.session_state.table_num, cart_items_for_db, total_price)
                    st.session_state.cart = {}  # 清空
                    st.balloons()
                    st.success("下单成功！厨师已收到。")
                    time.sleep(2)
                    st.rerun()

# ==========================================
# 5. 后台管理页面 (Admin)
# ==========================================
elif st.session_state.page == 'admin':
    st.markdown("## **⚙️ 后台管理控制台**")

    # 简单的密码保护
    pwd = st.sidebar.text_input("管理员密码", type="password")
    if pwd == "123456":
        tab1, tab2 = st.tabs(["📝 实时订单", "🥘 菜品 & 图片"])

        with tab1:
            if st.button("🔄 刷新订单列表"): st.rerun()
            orders = get_orders_data()
            if not orders: st.info("暂无订单")

            for order in orders:
                oid, otable, ojson, ototal, ostatus, otime = order

                # 订单卡片样式
                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 2, 2])
                    with c1:
                        st.markdown(f"**订单 #{oid}** | 桌号: {otable}")
                        st.caption(f"时间: {otime}")
                        # 展开详情
                        with st.expander("查看菜品详情"):
                            st.table(pd.DataFrame(json.loads(ojson)))
                    with c2:
                        st.markdown(f"#### ¥{ototal}")
                    with c3:
                        if "待" in ostatus:
                            st.warning(ostatus)
                            if st.button("✅ 完成", key=f"fin_{oid}"):
                                update_order_status(oid, "已完成")
                                st.rerun()
                        else:
                            st.success(ostatus)

        with tab2:
            st.markdown("### **添加新菜品**")
            with st.container(border=True):
                with st.form("add_dish_form"):
                    c1, c2 = st.columns(2)
                    n = c1.text_input("菜品名称")
                    p = c2.number_input("价格", min_value=1)
                    cat = c1.text_input("分类 (如: 汉堡, 披萨)")
                    desc = c2.text_input("描述")

                    st.markdown("**图片上传 (支持本地)**")
                    img_src = st.radio("来源", ["本地上传", "网络链接"], horizontal=True)
                    final_img = ""

                    if img_src == "本地上传":
                        up_file = st.file_uploader("选择图片", type=['png', 'jpg', 'jpeg'])
                        if up_file:
                            final_img = process_uploaded_image(up_file)
                            if final_img: st.image(final_img, width=100)
                    else:
                        url = st.text_input("图片 URL")
                        if url:
                            final_img = url
                            st.image(url, width=100)

                    if st.form_submit_button("发布菜品"):
                        if n and final_img:
                            add_dish_to_db(n, p, cat, final_img, desc)
                            st.success("发布成功！")
                            st.rerun()
                        else:
                            st.error("请补全信息")

            st.markdown("---")
            st.markdown("### **菜单列表**")
            df_menu = get_menu_data()
            for i, row in df_menu.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 4, 1])
                    c1.image(row['image'], width=50)
                    c2.markdown(f"**{row['name']}** - ¥{row['price']}")
                    if c3.button("删除", key=f"del_d_{row['id']}"):
                        delete_dish_from_db(row['id'])
                        st.rerun()

    else:
        st.warning("🔒 请在左侧输入密码 (123456)")














