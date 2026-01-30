import streamlit as st
import hashlib
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# ============================================================================
# PERFORMANCE OPTIMIZATION: Use caching
# ============================================================================

@st.cache_data
def load_image_from_bytes(image_data):
    """Cache image loading to prevent repeated processing"""
    if image_data:
        try:
            return Image.open(io.BytesIO(image_data))
        except:
            return None
    return None

# ============================================================================
# DATA CLASSES AND MODELS
# ============================================================================

class MenuItem:
    """Represents a menu item in the restaurant"""
    def __init__(self, food_id, name, price, rating=4.0, image_data=None, category="Main Course", tags=None):
        self.food_id = food_id
        self.name = name
        self.price = price
        self.rating = rating
        self.image_data = image_data
        self.category = category
        self.tags = tags or []

class OrderHistory:
    """Represents a customer order"""
    def __init__(self, order_id, customer_name, items, total_amount, date, is_teacher):
        self.order_id = order_id
        self.customer_name = customer_name
        self.items = items
        self.total_amount = total_amount
        self.date = date
        self.is_teacher = is_teacher

# ============================================================================
# RECOMMENDATION ENGINE (Cached for performance)
# ============================================================================

class RecommendationEngine:
    """AI-powered food recommendation system"""
    
    @staticmethod
    @st.cache_data(ttl=60)
    def get_popular_items(_menu_items, _orders, limit=3):
        """Get most ordered items (cached for 60 seconds)"""
        item_counts = {}
        for order in _orders:
            for item, qty in order.items:
                item_counts[item.food_id] = item_counts.get(item.food_id, 0) + qty
        
        if not item_counts:
            return _menu_items[:limit]
        
        popular_ids = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        popular_items = [item for item in _menu_items if item.food_id in [pid[0] for pid in popular_ids]]
        return popular_items
    
    @staticmethod
    def get_highly_rated_items(menu_items, min_rating=4.3, limit=3):
        """Get highest rated items"""
        high_rated = sorted([item for item in menu_items if item.rating >= min_rating], 
                          key=lambda x: x.rating, reverse=True)
        return high_rated[:limit]
    
    @staticmethod
    def get_budget_friendly_items(menu_items, max_price=100, limit=3):
        """Get items within budget"""
        budget_items = sorted([item for item in menu_items if item.price <= max_price],
                             key=lambda x: x.price)
        return budget_items[:limit]

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': hashlib.sha256('admin123'.encode()).hexdigest(),
            'user': hashlib.sha256('user123'.encode()).hexdigest()
        }
    if 'menu_items' not in st.session_state:
        st.session_state.menu_items = load_default_menu()
    if 'orders' not in st.session_state:
        st.session_state.orders = []
    if 'order_index' not in st.session_state:
        st.session_state.order_index = 1
    if 'cart' not in st.session_state:
        st.session_state.cart = {}

def load_default_menu():
    """Load default menu items with images"""
    menu_data = [
        (1, "Burger", 70.23, 4.5, "Main Course", ['popular', 'non-veg']),
        (2, "Coffee", 70.20, 4.0, "Beverage", ['popular', 'hot']),
        (3, "Pizza", 237.26, 4.7, "Main Course", ['popular', 'vegetarian']),
        (4, "Pasta", 150.00, 4.3, "Main Course", ['vegetarian']),
        (5, "Sandwich", 80.50, 4.2, "Main Course", ['vegetarian']),
        (6, "Fries", 60.00, 4.0, "Side Dish", ['popular', 'vegetarian']),
        (7, "Salad", 90.00, 4.4, "Side Dish", ['vegetarian', 'healthy']),
        (8, "Ice Cream", 50.00, 4.6, "Dessert", ['popular', 'sweet']),
    ]
    
    menu_items = []
    images_path = "images"
    
    for food_id, name, price, rating, category, tags in menu_data:
        # Try to load image if exists
        img_file = os.path.join(images_path, f"{food_id}.jpg")
        img_data = None
        
        if os.path.exists(img_file):
            try:
                with open(img_file, 'rb') as f:
                    img_data = f.read()
            except Exception as e:
                print(f"Error loading image {img_file}: {e}")
        
        menu_items.append(MenuItem(food_id, name, price, rating, img_data, category, tags))
    
    return menu_items

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def show_login_page():
    """Display login/signup page"""
    st.title("🍔 ByteBite Food Ordering System")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", use_container_width=True):
            if username and password:
                hashed_pw = hash_password(password)
                if username in st.session_state.users and st.session_state.users[username] == hashed_pw:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please fill in all fields")
    
    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Username", key="signup_user")
        new_password = st.text_input("Password", type="password", key="signup_pass")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        if st.button("Sign Up", use_container_width=True):
            if new_username and new_password and confirm_password:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif new_username in st.session_state.users:
                    st.error("Username already exists")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    st.session_state.users[new_username] = hash_password(new_password)
                    st.success("User registered successfully! Please log in.")
            else:
                st.warning("Please fill in all fields")
    
    with st.expander("ℹ️ Demo Credentials"):
        st.info("Admin: `admin` / `admin123`\n\nUser: `user` / `user123`")

# ============================================================================
# USER PANEL - ORDERING
# ============================================================================

def show_user_panel():
    """Display user ordering panel"""
    st.title("🍽️ Order Your Favorite Food")
    
    # Customer info - Using session state to persist
    col1, col2 = st.columns([2, 1])
    with col1:
        customer_name = st.text_input("Your Name", key="customer_name")
    with col2:
        user_type = st.radio("You are:", ["Student", "Teacher"], horizontal=True)
    
    st.markdown("---")
    
    # Show recommendations
    show_quick_recommendations()
    
    st.subheader("📋 Our Menu")
    
    # Category filter
    categories = ["All"] + sorted(list(set([item.category for item in st.session_state.menu_items])))
    selected_category = st.selectbox("Filter by Category:", categories, key="category_filter")
    
    # Filter items
    filtered_items = st.session_state.menu_items
    if selected_category != "All":
        filtered_items = [item for item in st.session_state.menu_items if item.category == selected_category]
    
    # Display menu - OPTIMIZED: Only show current page
    items_per_page = 6
    total_pages = (len(filtered_items) - 1) // items_per_page + 1
    
    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1), key="menu_page") - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_items))
    page_items = filtered_items[start_idx:end_idx]
    
    # Display items in grid
    cols = st.columns(3)
    for idx, item in enumerate(page_items):
        with cols[idx % 3]:
            display_menu_item(item)
    
    st.markdown("---")
    
    # Cart summary
    if st.session_state.cart:
        st.subheader("🛒 Your Cart")
        display_cart_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Clear Cart", type="secondary"):
                st.session_state.cart = {}
                st.rerun()
        with col3:
            if st.button("Place Order", type="primary"):
                if customer_name:
                    place_order(customer_name, user_type == "Teacher")
                else:
                    st.error("Please enter your name")

def show_quick_recommendations():
    """Show compact recommendations"""
    if not st.session_state.orders:
        return
    
    with st.expander("✨ Recommended For You", expanded=False):
        popular = RecommendationEngine.get_popular_items(
            st.session_state.menu_items, 
            st.session_state.orders, 
            limit=3
        )
        
        if popular:
            cols = st.columns(len(popular))
            for col, item in zip(cols, popular):
                with col:
                    st.write(f"**{item.name}**")
                    st.caption(f"₹{item.price:.2f} • ⭐{item.rating}")
                    if st.button("Add", key=f"rec_{item.food_id}", use_container_width=True):
                        st.session_state.cart[item.food_id] = st.session_state.cart.get(item.food_id, 0) + 1
                        st.rerun()

def display_menu_item(item):
    """Display menu item - OPTIMIZED"""
    with st.container():
        # Only load image if exists
        if item.image_data:
            img = load_image_from_bytes(item.image_data)
            if img:
                st.image(img, use_container_width=True)
        else:
            st.markdown(f"<div style='background-color: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center;'>📷 No Image</div>", unsafe_allow_html=True)
        
        st.markdown(f"**{item.name}**")
        st.caption(f"{item.category}")
        st.write(f"₹{item.price:.2f} • ⭐{item.rating}")
        
        # Quick add/remove buttons instead of number input
        current_qty = st.session_state.cart.get(item.food_id, 0)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("−", key=f"minus_{item.food_id}", disabled=current_qty == 0):
                if current_qty > 1:
                    st.session_state.cart[item.food_id] = current_qty - 1
                else:
                    st.session_state.cart.pop(item.food_id, None)
                st.rerun()
        with col2:
            st.markdown(f"<center>{current_qty}</center>", unsafe_allow_html=True)
        with col3:
            if st.button("+", key=f"plus_{item.food_id}"):
                st.session_state.cart[item.food_id] = current_qty + 1
                st.rerun()

def display_cart_summary():
    """Display cart summary"""
    total = 0
    cart_items = []
    
    for food_id, qty in st.session_state.cart.items():
        item = next((m for m in st.session_state.menu_items if m.food_id == food_id), None)
        if item:
            subtotal = item.price * qty
            total += subtotal
            cart_items.append({
                "Item": item.name,
                "Qty": qty,
                "Price": f"₹{item.price:.2f}",
                "Total": f"₹{subtotal:.2f}"
            })
    
    if cart_items:
        st.dataframe(pd.DataFrame(cart_items), use_container_width=True, hide_index=True)
        st.markdown(f"### Total: ₹{total:.2f}")

def place_order(customer_name, is_teacher):
    """Place order"""
    items_ordered = []
    total = 0
    
    for food_id, qty in st.session_state.cart.items():
        item = next((m for m in st.session_state.menu_items if m.food_id == food_id), None)
        if item:
            items_ordered.append((item, qty))
            total += item.price * qty
    
    if items_ordered:
        order_date = datetime.now().strftime("%d-%m-%Y %H:%M")
        order = OrderHistory(
            st.session_state.order_index,
            customer_name,
            items_ordered,
            total,
            order_date,
            is_teacher
        )
        st.session_state.orders.append(order)
        st.session_state.order_index += 1
        st.session_state.cart = {}
        
        st.success(f"✅ Order #{order.order_id} placed successfully!")
        st.balloons()
        
        # Clear cache to update recommendations
        RecommendationEngine.get_popular_items.clear()

# ============================================================================
# ADMIN PANEL
# ============================================================================

def show_admin_panel():
    """Display admin panel"""
    st.title("⚙️ Admin Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Orders", len(st.session_state.orders))
    with col2:
        revenue = sum(o.total_amount for o in st.session_state.orders)
        st.metric("Revenue", f"₹{revenue:.2f}")
    with col3:
        st.metric("Menu Items", len(st.session_state.menu_items))
    with col4:
        avg = revenue / len(st.session_state.orders) if st.session_state.orders else 0
        st.metric("Avg Order", f"₹{avg:.2f}")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📋 Menu", "📦 Orders", "📊 Analytics"])
    
    with tab1:
        show_menu_management()
    with tab2:
        show_order_management()
    with tab3:
        show_analytics()

def show_menu_management():
    """Menu management"""
    st.subheader("Add New Dish")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Dish Name")
        price = st.number_input("Price (₹)", min_value=0.0, step=1.0)
    with col2:
        category = st.selectbox("Category", ["Main Course", "Beverage", "Side Dish", "Dessert"])
        rating = st.number_input("Rating", 0.0, 5.0, 4.0, 0.1)
    
    image = st.file_uploader("Image (optional)", type=['png', 'jpg', 'jpeg'])
    
    if st.button("Add Dish", use_container_width=True):
        if name and price > 0:
            img_data = image.read() if image else None
            new_id = max([i.food_id for i in st.session_state.menu_items], default=0) + 1
            new_item = MenuItem(new_id, name, price, rating, img_data, category)
            st.session_state.menu_items.append(new_item)
            st.success(f"✅ Added {name}")
            st.rerun()
        else:
            st.error("Fill required fields")
    
    st.markdown("---")
    st.subheader("Current Menu")
    
    for item in st.session_state.menu_items:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{item.name}** - {item.category} - ₹{item.price:.2f} - ⭐{item.rating}")
        with col3:
            if st.button("Delete", key=f"del_{item.food_id}"):
                st.session_state.menu_items.remove(item)
                st.rerun()

def show_order_management():
    """Order management"""
    st.subheader("Orders")
    
    if not st.session_state.orders:
        st.info("No orders yet")
        return
    
    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export CSV"):
            export_csv()
    with col2:
        if st.button("📥 Export PDF"):
            export_pdf()
    
    st.markdown("---")
    
    # Simple order list
    for order in reversed(st.session_state.orders[-10:]):  # Show last 10 only
        with st.expander(f"Order #{order.order_id} - {order.customer_name} - ₹{order.total_amount:.2f}"):
            st.write(f"**Date:** {order.date}")
            st.write(f"**Type:** {'Teacher' if order.is_teacher else 'Student'}")
            st.write("**Items:**")
            for item, qty in order.items:
                st.write(f"- {item.name} x{qty}")
            
            if st.button("Delete", key=f"del_order_{order.order_id}"):
                st.session_state.orders.remove(order)
                st.rerun()

def show_analytics():
    """Analytics dashboard"""
    if not st.session_state.orders:
        st.info("No data yet")
        return
    
    # Popular items
    st.subheader("Most Popular Items")
    item_counts = {}
    for order in st.session_state.orders:
        for item, qty in order.items:
            item_counts[item.name] = item_counts.get(item.name, 0) + qty
    
    df = pd.DataFrame(list(item_counts.items()), columns=['Item', 'Orders'])
    df = df.sort_values('Orders', ascending=False).head(5)
    st.bar_chart(df.set_index('Item'))
    
    # Customer types
    st.subheader("Customer Distribution")
    teachers = sum(1 for o in st.session_state.orders if o.is_teacher)
    students = len(st.session_state.orders) - teachers
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Teachers", teachers)
    with col2:
        st.metric("Students", students)

def export_csv():
    """Export to CSV"""
    data = []
    for o in st.session_state.orders:
        items_str = "; ".join([f"{i.name}x{q}" for i, q in o.items])
        data.append({
            "Order ID": o.order_id,
            "Customer": o.customer_name,
            "Type": "Teacher" if o.is_teacher else "Student",
            "Items": items_str,
            "Total": o.total_amount,
            "Date": o.date
        })
    
    csv = pd.DataFrame(data).to_csv(index=False)
    st.download_button("Download CSV", csv, "orders.csv", "text/csv")

def export_pdf():
    """Export to PDF"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "ByteBite Orders Report")
    y -= 30
    
    c.setFont("Helvetica", 10)
    for o in st.session_state.orders:
        items = ", ".join([f"{i.name}x{q}" for i, q in o.items])
        line = f"#{o.order_id}: {o.customer_name} - {items} - ₹{o.total_amount:.2f}"
        c.drawString(50, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = 750
    
    c.save()
    buffer.seek(0)
    st.download_button("Download PDF", buffer, "orders.pdf", "application/pdf")

# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(
        page_title="ByteBite",
        page_icon="🍔",
        layout="wide"
    )
    
    # Minimal CSS
    st.markdown("""
        <style>
        .stButton>button {width: 100%;}
        div[data-testid="metric-container"] {
            background: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        with st.sidebar:
            st.title("🍔 ByteBite")
            st.write(f"**{st.session_state.username}**")
            st.markdown("---")
            
            page = st.radio("Menu", ["🍽️ Order", "⚙️ Admin"], label_visibility="collapsed")
            
            st.markdown("---")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.cart = {}
                st.rerun()
        
        if page == "🍽️ Order":
            show_user_panel()
        else:
            show_admin_panel()

if __name__ == "__main__":
    main()