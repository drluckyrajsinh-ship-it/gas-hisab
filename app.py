import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import socket
import qrcode
from io import BytesIO

# Page Configuration & Clean Digital Styling
st.set_page_config(page_title="Vaishali Indane - Stock & Hisab Portal", page_icon="⛽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "daily_hisab_data.csv"
STOCK_FILE = "stock_inventory.csv"
CONFIG_FILE = "agency_settings.json"

# ==========================================
# 1. SETTINGS & DATABASE INIT
# ==========================================
default_config = {
    "agency_name": "Vaishali Indane",
    "admin_pin": "1234",
    "delivery_boys": ["Rameshbhai", "Sureshbhai", "Maheshbhai", "Kamleshbhai"],
    "rates": {
        "14.2 Kg Domestic": 820,
        "19 Kg Commercial": 1850,
        "10 Kg Composite": 600,
        "10 Kg Extralite": 650,
        "5 Kg Chhotu": 315,
        "Gas Stove": 2500,
        "Suraksha Hose": 250,
        "Cylinder Trolly": 450
    }
}

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = default_config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def save_config(new_config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_config, f, indent=4)

REQUIRED_COLS = [
    "Tarikh", "Samay", "Delivery_Boy", "Summary_Details", 
    "Total_Cylinders", "Total_Bill_Amount", "Cash_Jama", 
    "Online_UPI", "Kul_Jama", "Plus_Minus_Fariq", 
    "N_500", "N_200", "N_100", "N_50", "N_20", "N_10",
    "Note_Details"
]

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = 0 if "N_" not in col and col != "Note_Details" and col != "Summary_Details" else ("" if col in ["Note_Details", "Summary_Details"] else 0)
else:
    df = pd.DataFrame(columns=REQUIRED_COLS)

# Stock Inventory Init
if os.path.exists(STOCK_FILE):
    stock_df = pd.read_csv(STOCK_FILE)
else:
    stock_data = []
    for item in config["rates"].keys():
        stock_data.append({"Item_Name": item, "Opening_Stock": 50, "Added_Stock": 0, "Sold_Stock": 0, "Closing_Stock": 50})
    stock_df = pd.DataFrame(stock_data)
    stock_df.to_csv(STOCK_FILE, index=False)

def get_base_url():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:8501"
    except Exception:
        return "http://localhost:8501"

query_params = st.query_params
active_page = query_params.get("page", "admin")
boy_param = query_params.get("boy", "")

if active_page == "entry":
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
else:
    st.sidebar.title(f"⛽ {config['agency_name']}")
    menu = st.sidebar.radio(
        "Navigation Menu:", 
        [
            "🖥️  Admin Dashboard", 
            "📦  Stock Inventory & Products",
            "📊  Monthly Analytics", 
            "👤  Delivery Boy Report", 
            "⚙️  Agency Settings", 
            "💾  Backup & Restore",
            "🔗  Generate Links"
        ],
        format_func=lambda x: x
    )

# ==========================================
# SCREEN 1: DELIVERY BOY MOBILE ENTRY FORM
# ==========================================
if active_page == "entry":
    selected_boy = boy_param if boy_param in config["delivery_boys"] else (config["delivery_boys"][0] if config["delivery_boys"][0] else "Delivery Boy")
    
    st.header(f"⛽ {config['agency_name']} - Digital Portal")
    st.subheader(f"📝 Daily Delivery Entry: **{selected_boy}**")
    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📦 Cylinders & Allied Products Dispatch")
        quantities = {}
        total_bill_amount = 0
        total_item_count = 0
        summary_list = []

        for item_name, rate in config["rates"].items():
            qty = st.number_input(f"{item_name} (Price: ₹{rate})", min_value=0, value=0, step=1)
            quantities[item_name] = qty
            if qty > 0:
                subtotal = qty * rate
                total_bill_amount += subtotal
                total_item_count += qty
                summary_list.append(f"{qty}x {item_name} (₹{subtotal})")

        st.info(f"📦 **Total Items:** {total_item_count} | 🧾 **Total Bill:** ₹ **{total_bill_amount}**")

    with col_right:
        st.markdown("### 💵 Cash Denomination & Online Payment")
        nc1, nc2 = st.columns(2)
        with nc1:
            n500 = st.number_input("₹ 500 Notes ×", min_value=0, value=0, step=1)
            n200 = st.number_input("₹ 200 Notes ×", min_value=0, value=0, step=1)
            n100 = st.number_input("₹ 100 Notes ×", min_value=0, value=0, step=1)
        with nc2:
            n50  = st.number_input("₹ 50 Notes ×", min_value=0, value=0, step=1)
            n20  = st.number_input("₹ 20 Notes ×", min_value=0, value=0, step=1)
            n10  = st.number_input("₹ 10 Notes ×", min_value=0, value=0, step=1)

            st.markdown(f"""
            **Cash Subtotal:**
            * 500×{n500} = ₹{n500*500}
            * 200×{n200} = ₹{n200*200}
            * 100×{n100} = ₹{n100*100}
            * 50/20/10 = ₹{(n50*50)+(n20*20)+(n10*10)}
            """)

        total_cash = (n500*500) + (n200*200) + (n100*100) + (n50*50) + (n20*20) + (n10*10)
        st.success(f"💵 **Total Cash Collected:** ₹ {total_cash}")

        online_upi = st.number_input("📲 Online / UPI Payment (₹)", min_value=0, value=0, step=50)

    st.markdown("---")
    st.subheader("📊 Financial Reconciliation (Bill vs Collection)")
    total_received = total_cash + online_upi
    plus_minus = total_received - total_bill_amount

    m1, m2, m3 = st.columns(3)
    m1.metric("🧾 Total Bill Amount", f"₹ {total_bill_amount}")
    m2.metric("💰 Total Collection", f"₹ {total_received}")
    if plus_minus == 0:
        m3.metric("⚖️ Balance Status", "₹ 0 (Exact Match)", "✔️ Balanced")
    elif plus_minus < 0:
        m3.metric("⚠️ Shortage", f"- ₹ {abs(plus_minus)}", delta_color="inverse")
    else:
        m3.metric("➕ Excess", f"+ ₹ {plus_minus}")

    summary_str = ", ".join(summary_list) if summary_list else "No deliveries"
    note_summary = f"500:{n500}, 200:{n200}, 100:{n100}, 50:{n50}, 20:{n20}, 10:{n10}"

    if st.button("✅ Submit Daily Report", type="primary", use_container_width=True):
        if total_item_count == 0 and total_received == 0:
            st.warning("⚠️ Please enter item or collection details!")
        else:
            now = datetime.now()
            row_data = {
                "Tarikh": now.strftime("%Y-%m-%d"),
                "Samay": now.strftime("%I:%M %p"),
                "Delivery_Boy": selected_boy,
                "Summary_Details": summary_str,
                "Total_Cylinders": total_item_count,
                "Total_Bill_Amount": total_bill_amount,
                "Cash_Jama": total_cash,
                "Online_UPI": online_upi,
                "Kul_Jama": total_received,
                "Plus_Minus_Fariq": plus_minus,
                "N_500": n500, "N_200": n200, "N_100": n100,
                "N_50": n50, "N_20": n20, "N_10": n10,
                "Note_Details": note_summary
            }
            for item, q in quantities.items():
                row_data[item] = q
                if q > 0 and os.path.exists(STOCK_FILE):
                    st_df = pd.read_csv(STOCK_FILE)
                    if item in st_df['Item_Name'].values:
                        st_df.loc[st_df['Item_Name'] == item, 'Sold_Stock'] += q
                        st_df['Closing_Stock'] = st_df['Opening_Stock'] + st_df['Added_Stock'] - st_df['Sold_Stock']
                        st_df.to_csv(STOCK_FILE, index=False)

            new_row = pd.DataFrame([row_data])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.balloons()
            st.success("🎉 Hisab successfully submitted to office server!")

# ==========================================
# SCREEN 2: OFFICE ADMIN DASHBOARD
# ==========================================
elif menu == "🖥️  Admin Dashboard":
    st.header(f"🖥️ {config['agency_name']} - Admin Control Center")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    
    if pin == config["admin_pin"]:
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            selected_date = st.date_input("📅 Select Date", datetime.now()).strftime("%Y-%m-%d")
        with col_t2:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()

        daily_df = df[df["Tarikh"] == selected_date]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📦 Total Items Sold", f"{daily_df['Total_Cylinders'].sum()}")
        c2.metric("🧾 Bill Amount", f"₹ {daily_df['Total_Bill_Amount'].sum()}")
        c3.metric("💵 Total Cash", f"₹ {daily_df['Cash_Jama'].sum()}")
        c4.metric("📲 Total Online", f"₹ {daily_df['Online_UPI'].sum()}")
        c5.metric("⚖️ Net Difference", f"₹ {daily_df['Plus_Minus_Fariq'].sum()}")

        st.markdown("---")
        st.subheader(f"📋 Date: {selected_date} - Delivery Summary Overview")
        if not daily_df.empty:
            st.dataframe(daily_df, use_container_width=True)
        else:
            st.info("No records found for this date.")

        if not daily_df.empty:
            st.markdown("### 📄 Export, Print & WhatsApp Share")
            
            report_text = f"*{config['agency_name']} Daily Report* (%0A)Date: {selected_date}%0A- Total Items: {daily_df['Total_Cylinders'].sum()}%0A- Total Bill: Rs.{daily_df['Total_Bill_Amount'].sum()}%0A- Cash: Rs.{daily_df['Cash_Jama'].sum()}%0A- Online: Rs.{daily_df['Online_UPI'].sum()}"
            whatsapp_url = f"https://api.whatsapp.com/send?text={report_text}"

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                report_html = f"""
                <h2>{config['agency_name']} - Daily Report</h2>
                <p><b>Date:</b> {selected_date}</p>
                <hr>
                {daily_df.to_html(index=False)}
                <script>window.print();</script>
                """
                st.download_button(
                    label="📥 Download Report as PDF/HTML",
                    data=report_html,
                    file_name=f"Vaishali_Indane_Report_{selected_date}.html",
                    mime="text/html"
                )
            with col_btn2:
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:600; cursor:pointer;">💬 Share on WhatsApp</button></a>', unsafe_allow_html=True)
            with col_btn3:
                if st.button("🖨️ Print Direct Report"):
                    st.components.v1.html("<script>window.print();</script>", height=0)

        with st.expander("🗑️ Delete Selected Entry"):
            if not daily_df.empty:
                row_del = st.selectbox("Select Entry to Delete:", daily_df.index, format_func=lambda x: f"{daily_df.loc[x, 'Samay']} - {daily_df.loc[x, 'Delivery_Boy']}")
                if st.button("❌ Delete Entry"):
                    df = df.drop(index=row_del).reset_index(drop=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success("Record deleted successfully!")
                    st.rerun()
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")

# ==========================================
# SCREEN 3: STOCK INVENTORY & PRODUCTS
# ==========================================
elif menu == "📦  Stock Inventory & Products":
    st.header("📦 Stock Inventory & Closing Stock Board")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    
    if pin == config["admin_pin"]:
        st.subheader("📊 Live Stock Board (Cylinders & Allied Products)")
        if os.path.exists(STOCK_FILE):
            st_df = pd.read_csv(STOCK_FILE)
            st_df['Closing_Stock'] = st_df['Opening_Stock'] + st_df['Added_Stock'] - st_df['Sold_Stock']
            st.dataframe(st_df, use_container_width=True)

        st.markdown("---")
        st.subheader("➕ Add New Stock (Purchase / Receipt)")
        with st.form("stock_form"):
            s_item = st.selectbox("Select Product", list(config["rates"].keys()))
            add_qty = st.number_input("Add Stock Quantity", min_value=0, value=0, step=1)
            submitted_stock = st.form_submit_button("Update Stock Inventory")

            if submitted_stock:
                st_df = pd.read_csv(STOCK_FILE)
                if s_item in st_df['Item_Name'].values:
                    st_df.loc[st_df['Item_Name'] == s_item, 'Added_Stock'] += add_qty
                else:
                    new_row = pd.DataFrame([{"Item_Name": s_item, "Opening_Stock": 0, "Added_Stock": add_qty, "Sold_Stock": 0, "Closing_Stock": add_qty}])
                    st_df = pd.concat([st_df, new_row], ignore_index=True)
                
                st_df['Closing_Stock'] = st_df['Opening_Stock'] + st_df['Added_Stock'] - st_df['Sold_Stock']
                st_df.to_csv(STOCK_FILE, index=False)
                st.success(f"Successfully added {add_qty} units to {s_item} stock!")
                st.rerun()
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")

# ==========================================
# SCREEN 4: MONTHLY ANALYTICS
# ==========================================
elif menu == "📊  Monthly Analytics":
    st.header("📊 Monthly Performance & Sales Analytics")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    
    if pin == config["admin_pin"]:
        if not df.empty:
            df['YearMonth'] = pd.to_datetime(df['Tarikh']).dt.to_period('M').astype(str)
            available_months = sorted(df['YearMonth'].unique(), reverse=True)

            selected_month = st.selectbox("📅 Select Month:", available_months)
            monthly_df = df[df['YearMonth'] == selected_month]

            st.subheader(f"📊 Summary for Period: {selected_month}")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📦 Total Items Sold", f"{monthly_df['Total_Cylinders'].sum()}")
            m2.metric("🧾 Total Revenue", f"₹ {monthly_df['Total_Bill_Amount'].sum()}")
            m3.metric("💵 Total Cash", f"₹ {monthly_df['Cash_Jama'].sum()}")
            m4.metric("📲 Total Online", f"₹ {monthly_df['Online_UPI'].sum()}")

            st.markdown("---")
            st.subheader("📋 Monthly Detailed Ledger:")
            st.dataframe(monthly_df.drop(columns=['YearMonth']), use_container_width=True)

            month_html = f"""
            <h2>{config['agency_name']} - Monthly Analytics ({selected_month})</h2>
            <hr>
            {monthly_df.drop(columns=['YearMonth']).to_html(index=False)}
            """
            st.download_button(
                label="📥 Download Monthly Report as PDF/HTML",
                data=month_html,
                file_name=f"Vaishali_Indane_Monthly_{selected_month}.html",
                mime="text/html"
            )
        else:
            st.info("No transaction data available.")
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")

# ==========================================
# SCREEN 5: DELIVERY BOY REPORT
# ==========================================
elif menu == "👤  Delivery Boy Report":
    st.header("👤 Delivery Boy Wise Ledger & Cash Breakdown")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    
    if pin == config["admin_pin"]:
        selected_date = st.date_input("📅 Select Date", datetime.now()).strftime("%Y-%m-%d")
        daily_df = df[df["Tarikh"] == selected_date]

        if not daily_df.empty:
            selected_boy_rep = st.selectbox("👤 Select Delivery Boy:", config["delivery_boys"])
            boy_df = daily_df[daily_df["Delivery_Boy"] == selected_boy_rep]

            if not boy_df.empty:
                st.subheader(f"📊 Ledger for: {selected_boy_rep} ({selected_date})")
                st.dataframe(boy_df, use_container_width=True)

                st.markdown("---")
                st.subheader(f"💵 Cash Denomination Breakdown for {selected_boy_rep}")
                
                b_500 = int(boy_df['N_500'].sum())
                b_200 = int(boy_df['N_200'].sum())
                b_100 = int(boy_df['N_100'].sum())
                b_50  = int(boy_df['N_50'].sum())
                b_20  = int(boy_df['N_20'].sum())
                b_10  = int(boy_df['N_10'].sum())

                boy_denom_table = pd.DataFrame({
                    "Currency Note": ["₹ 500", "₹ 200", "₹ 100", "₹ 50", "₹ 20", "₹ 10"],
                    "Count": [b_500, b_200, b_100, b_50, b_20, b_10],
                    "Total Value (₹)": [b_500*500, b_200*200, b_100*100, b_50*50, b_20*20, b_10*10]
                })
                st.table(boy_denom_table)
                st.success(f"💵 Total Cash Collected: ₹ {boy_df['Cash_Jama'].sum()} | 📲 Total Online: ₹ {boy_df['Online_UPI'].sum()}")
            else:
                st.info(f"No records found for {selected_boy_rep} on this date.")
        else:
            st.info("No entries recorded for this date.")
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")

# ==========================================
# SCREEN 6: AGENCY SETTINGS
# ==========================================
elif menu == "⚙️  Agency Settings":
    st.header("⚙️ System Configuration & Rates")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    
    if pin == config["admin_pin"]:
        s1, s2 = st.columns(2)
        with s1:
            st.subheader("🏷️ Update Product Rates")
            new_rates = {}
            for item, r in config["rates"].items():
                new_rates[item] = st.number_input(f"{item} Rate (₹)", min_value=0, value=int(r), step=5)
            if st.button("💾 Save Rates"):
                config["rates"] = new_rates
                save_config(config)
                st.success("Rates updated successfully!")
        with s2:
            st.subheader("👷 Manage Delivery Personnel")
            b_rem = st.selectbox("Remove Personnel:", ["-- Select --"] + config["delivery_boys"])
            if st.button("🗑️ Remove"):
                if b_rem != "-- Select --":
                    config["delivery_boys"].remove(b_rem)
                    save_config(config)
                    st.rerun()
            new_b = st.text_input("New Personnel Name:")
            if st.button("➕ Add Personnel"):
                if new_b.strip() and new_b not in config["delivery_boys"]:
                    config["delivery_boys"].append(new_b.strip())
                    save_config(config)
                    st.rerun()
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")

# ==========================================
# SCREEN 7: BACKUP & RESTORE
# ==========================================
elif menu == "💾  Backup & Restore":
    st.header("💾 Data Backup & Restore Center")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    
    if pin == config["admin_pin"]:
        st.subheader("📤 Download Data Backup")
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                st.download_button(
                    label="📥 Download Database Backup (CSV)",
                    data=f,
                    file_name=f"Vaishali_Indane_Backup_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv"
                )
        
        st.markdown("---")
        st.subheader("📥 Restore Data from Backup")
        uploaded_file = st.file_uploader("Upload previously downloaded CSV backup file", type=["csv"])
        if uploaded_file is not None:
            restore_df = pd.read_csv(uploaded_file)
            restore_df.to_csv(DATA_FILE, index=False)
            st.success("Database restored successfully! Please refresh or restart app.")
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")

# ==========================================
# SCREEN 8: LINK GENERATOR
# ==========================================
elif menu == "🔗  Generate Links":
    st.header("🔗 Mobile Portal Link Generator")
    pin = st.sidebar.text_input("🔑 Admin Password", type="password")
    if pin == config["admin_pin"]:
        base_url = get_base_url()
        st.write("Share these dedicated entry links or QR codes with your delivery staff via WhatsApp:")
        for boy in config["delivery_boys"]:
            b_link = f"{base_url}/?page=entry&boy={boy}"
            st.info(f"**{boy} Dedicated Portal Link:**\n`{b_link}`")
    else:
        st.warning("🔒 Please enter Admin Password `1234` in the sidebar.")
