import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import socket
import qrcode
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="Vaishali Indane - Daily Hisab", page_icon="⛽", layout="wide")

DATA_FILE = "daily_hisab_data.csv"
CONFIG_FILE = "agency_settings.json"

# ==========================================
# 1. SETTINGS & DATABASE INIT
# ==========================================
default_config = {
    "agency_name": "Vaishali Indane Gas Service",
    "admin_pin": "1234",
    "delivery_boys": ["Rameshbhai", "Sureshbhai", "Maheshbhai", "Kamleshbhai"],
    "rates": {
        "14.2 Kg Domestic": 820,
        "19 Kg Commercial": 1850,
        "5 Kg Chhotu": 315
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
    "Tarikh", "Samay", "Delivery_Boy", "Cylinder_Type", "Rate",
    "Upadela_Full", "Delivery_Thayel", "Parat_Full", 
    "Jama_Empty", "Baki_Empty", "Total_Rakkam", 
    "Cash_Jama", "Online_UPI", "Kul_Jama", "Plus_Minus_Fariq", 
    "N_500", "N_200", "N_100", "N_50", "N_20", "N_10", "Coins",
    "Note_Details", "Remarks"
]

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = 0 if "N_" not in col and col != "Remarks" and col != "Note_Details" else ("" if col in ["Remarks", "Note_Details"] else 0)
else:
    df = pd.DataFrame(columns=REQUIRED_COLS)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

query_params = st.query_params
active_page = query_params.get("page", "admin")
boy_param = query_params.get("boy", "")

# ==========================================
# SIDEBAR / ADMIN NAVIGATION
# ==========================================
if active_page == "entry":
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
else:
    st.sidebar.title(f"⛽ {config['agency_name']}")
    menu = st.sidebar.radio(
        "Menu Pasand Karo:", 
        ["💻 Office Admin Dashboard (PC)", "⚙️ Naam & Bhav Settings (Edit)", "📱 Delivery Boy Link Generator"]
    )

# ==========================================
# SCREEN 1: DELIVERY BOY ALAG LINK ENTRY FORM
# ==========================================
if active_page == "entry":
    selected_boy = boy_param if boy_param in config["delivery_boys"] else (config["delivery_boys"][0] if config["delivery_boys"][0] else "Delivery Boy")
    
    st.header(f"⛽ {config['agency_name']}")
    st.subheader(f"📝 Hisab Entry: **{selected_boy}**")
    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 1️⃣ Cylinder Vigat")
        cyl_types = list(config["rates"].keys())
        cyl_type = st.selectbox("🛢️ Cylinder Type", cyl_types)
        
        default_rate = int(config["rates"].get(cyl_type, 820))
        st.info(f"🏷️ **{cyl_type} no Bhav:** ₹ {default_rate}")

        full_taken = st.number_input("📤 Savare Upadela Bharela (Full Out)", min_value=0, value=0, step=1)
        delivered = st.number_input("✅ Aaje Delivery Thayela (Sold)", min_value=0, value=0, step=1)
        empty_collected = st.number_input("📥 Grahak pase thi Aavela Khali (Empty In)", min_value=0, value=0, step=1)

        full_return = full_taken - delivered
        empty_diff = empty_collected - delivered
        total_bill_amount = delivered * default_rate

        st.markdown("#### 📊 Cylinder Hisab (Live):")
        c1, c2 = st.columns(2)
        c1.metric("🔙 Parat Bharela Jama", f"{full_return} Cyl")
        if empty_diff < 0:
            c2.metric("⚠️ Khali Baki", f"{abs(empty_diff)} Ghat", delta=f"{empty_diff}", delta_color="normal")
        elif empty_diff > 0:
            c2.metric("➕ Extra Khali", f"+{empty_diff}", delta=f"+{empty_diff}")
        else:
            c2.metric("✔️ Khali Hisab", "0 Baki")

    with col_right:
        st.markdown("### 2️⃣ Rokda Noto (Denomination) & Online")
        
        nc1, nc2 = st.columns(2)
        with nc1:
            n500 = st.number_input("₹ 500 ni Note ×", min_value=0, value=0, step=1)
            n200 = st.number_input("₹ 200 ni Note ×", min_value=0, value=0, step=1)
            n100 = st.number_input("₹ 100 ni Note ×", min_value=0, value=0, step=1)
            n50  = st.number_input("₹ 50 ni Note ×", min_value=0, value=0, step=1)
        with nc2:
            n20  = st.number_input("₹ 20 ni Note ×", min_value=0, value=0, step=1)
            n10  = st.number_input("₹ 10 ni Note ×", min_value=0, value=0, step=1)
            coins = st.number_input("🪙 Sikka / Coins (₹)", min_value=0, value=0, step=1)

            st.markdown(f"""
            **Noto Total:**
            * 500×{n500} = ₹{n500*500}
            * 200×{n200} = ₹{n200*200}
            * 100×{n100} = ₹{n100*100}
            * 50×{n50} = ₹{n50*50}
            * 20/10/Coins = ₹{(n20*20)+(n10*10)+coins}
            """)

        total_cash = (n500*500) + (n200*200) + (n100*100) + (n50*50) + (n20*20) + (n10*10) + coins
        st.success(f"💵 **Kul Rokda (Cash):** ₹ {total_cash}")

        online_upi = st.number_input("📲 Online / UPI / GPay Jama (₹)", min_value=0, value=0, step=50)
        remarks = st.text_input("📝 Remarks (Baki Grahak nu naam)")

    st.markdown("---")
    st.subheader("🧮 Plus-Minus (+ / -) Final Hisab")
    
    total_received = total_cash + online_upi
    plus_minus = total_received - total_bill_amount

    m1, m2, m3, _ = st.columns(4)
    m1.metric("1. Kul Bill Rakkam", f"₹ {total_bill_amount}")
    m2.metric("2. Kul Jama (Cash+UPI)", f"₹ {total_received}")
    
    if plus_minus == 0:
        m3.metric("3. Fariq (+/-)", "₹ 0 (Exact)")
    elif plus_minus < 0:
        m3.metric("3. Paisa Ghat (-)", f"- ₹ {abs(plus_minus)}", delta_color="inverse")
    else:
        m3.metric("3. Vadhare Jama (+)", f"+ ₹ {plus_minus}")

    note_summary = f"500:{n500}, 200:{n200}, 100:{n100}, 50:{n50}, 20:{n20}, 10:{n10}, Coin:{coins}"

    if st.button("✅ Submit Hisab", type="primary", use_container_width=True):
        if full_taken < delivered:
            st.error("❌ Bhul: Upadela karta Delivery vadhare na hoi shake!")
        elif delivered == 0 and total_received == 0:
            st.warning("⚠️ Kripya vigat bharo!")
        else:
            now = datetime.now()
            new_row = pd.DataFrame([{
                "Tarikh": now.strftime("%Y-%m-%d"),
                "Samay": now.strftime("%I:%M %p"),
                "Delivery_Boy": selected_boy,
                "Cylinder_Type": cyl_type,
                "Rate": default_rate,
                "Upadela_Full": full_taken,
                "Delivery_Thayel": delivered,
                "Parat_Full": full_return,
                "Jama_Empty": empty_collected,
                "Baki_Empty": delivered - empty_collected,
                "Total_Rakkam": total_bill_amount,
                "Cash_Jama": total_cash,
                "Online_UPI": online_upi,
                "Kul_Jama": total_received,
                "Plus_Minus_Fariq": plus_minus,
                "N_500": n500, "N_200": n200, "N_100": n100,
                "N_50": n50, "N_20": n20, "N_10": n10, "Coins": coins,
                "Note_Details": note_summary,
                "Remarks": remarks
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.balloons()
            st.success(f"🎉 Tamaro hisab safaltapurvak save thai gayo che!")

# ==========================================
# SCREEN 2: ADMIN DASHBOARD (WITH DENOMINATION TABLE)
# ==========================================
elif menu == "💻 Office Admin Dashboard (PC)":
    st.header(f"🖥️ {config['agency_name']} - Master Dashboard")
    pin = st.sidebar.text_input("🔑 Admin Password Nakho", type="password")
    
    if pin == config["admin_pin"]:
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            selected_date = st.date_input("📅 Tarikh", datetime.now()).strftime("%Y-%m-%d")
        with col_t2:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()

        daily_df = df[df["Tarikh"] == selected_date]

        # Top Summary Metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📦 Total Delivery", f"{daily_df['Delivery_Thayel'].sum()} Cyl")
        c2.metric("🧾 Kul Bill Rakkam", f"₹ {daily_df['Total_Rakkam'].sum()}")
        c3.metric("💵 Total Rokda", f"₹ {daily_df['Cash_Jama'].sum()}")
        c4.metric("📲 Total Online", f"₹ {daily_df['Online_UPI'].sum()}")
        net_diff = daily_df['Plus_Minus_Fariq'].sum()
        c5.metric("⚖️ Net Plus/Minus", f"₹ {net_diff}")

        st.markdown("---")
        st.subheader(f"📋 Tarikh: {selected_date} - Delivery Boy Hisab Summary")
        if not daily_df.empty:
            display_cols = ["Samay", "Delivery_Boy", "Cylinder_Type", "Delivery_Thayel", "Total_Rakkam", "Cash_Jama", "Online_UPI", "Plus_Minus_Fariq", "Remarks"]
            st.dataframe(daily_df[display_cols], use_container_width=True)
        else:
            st.info("Aaje haju koi entry nathi.")

        # ==========================================
        # MASTER CASH DENOMINATION SUMMARY
        # ==========================================
        st.markdown("---")
        st.subheader("💵 Total Cash Galla — Noto (Denomination) Master Report")
        if not daily_df.empty:
            tot_500 = int(daily_df['N_500'].sum())
            tot_200 = int(daily_df['N_200'].sum())
            tot_100 = int(daily_df['N_100'].sum())
            tot_50  = int(daily_df['N_50'].sum())
            tot_20  = int(daily_df['N_20'].sum())
            tot_10  = int(daily_df['N_10'].sum())
            tot_coins = int(daily_df['Coins'].sum())

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                denom_table = pd.DataFrame({
                    "Note / Sikka": ["₹ 500", "₹ 200", "₹ 100", "₹ 50", "₹ 20", "₹ 10", "Coins"],
                    "Kul Sankhya (Count)": [tot_500, tot_200, tot_100, tot_50, tot_20, tot_10, tot_coins],
                    "Total Rakkam (₹)": [
                        tot_500*500, tot_200*200, tot_100*100, tot_50*50, tot_20*20, tot_10*10, tot_coins
                    ]
                })
                st.table(denom_table)
            with d_col2:
                grand_tot_cash = daily_df['Cash_Jama'].sum()
                grand_tot_online = daily_df['Online_UPI'].sum()
                st.info(f"""
                **💰 Galla Final Summary:**
                * **Kul Rokda (Cash from Notes):** ₹ {grand_tot_cash}
                * **Kul Online (UPI / GPay):** ₹ {grand_tot_online}
                * **Grand Total Jama:** ₹ {grand_tot_cash + grand_tot_online}
                """)
        else:
            st.write("Aaje koi cash entry nathi.")

        # Delete Entry Option
        with st.expander("🗑️ Khoti Entry Delete Karo"):
            if not daily_df.empty:
                row_del = st.selectbox(
                    "Entry Pasand Karo:", daily_df.index,
                    format_func=lambda x: f"{daily_df.loc[x, 'Samay']} - {daily_df.loc[x, 'Delivery_Boy']} (Cash: ₹{daily_df.loc[x, 'Cash_Jama']})"
                )
                if st.button("❌ Delete Selected Entry"):
                    df = df.drop(index=row_del).reset_index(drop=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success("Entry delete thai gai!")
                    st.rerun()

        # Excel Download
        csv = daily_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Aajno Hisab Excel ma Download Karo",
            data=csv,
            file_name=f"Gas_Hisab_{selected_date}.csv",
            mime="text/csv",
        )
    else:
        st.warning("🔒 Password `1234` nakho.")

# ==========================================
# SCREEN 3: SETTINGS & INDIVIDUAL LINKS
# ==========================================
elif menu == "⚙️ Naam & Bhav Settings (Edit)":
    st.header("⚙️ Delivery Boy Alag Link & Settings")
    pin = st.sidebar.text_input("🔑 Admin Password Nakho", type="password")
    
    if pin == config["admin_pin"]:
        local_ip = get_local_ip()

        st.subheader("🔗 Har ek Delivery Boy ni Alag Link ane QR Code:")
        st.write("Tame niche aapeli link WhatsApp par delivery boy ne mokli shako cho, athva QR scan karavi shako cho:")

        for boy in config["delivery_boys"]:
            boy_link = f"http://{local_ip}:8501/?page=entry&boy={boy}"
            with st.expander(f"👤 {boy} ni Alag Link & QR"):
                st.code(boy_link, language="text")
                st.caption(f"Aa link open karta j {boy} nu naam automatic select thai jashe.")
                
                # QR Generation for each boy
                qr = qrcode.QRCode(version=1, box_size=4, border=1)
                qr.add_data(boy_link)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.image(buf.getvalue(), width=150, caption=f"{boy} no QR Code")

        st.markdown("---")
        s1, s2 = st.columns(2)
        with s1:
            st.subheader("🏷️ Bhav (Rate) Set Karo")
            new_rates = {}
            for cyl, r in config["rates"].items():
                new_rates[cyl] = st.number_input(f"{cyl} (₹)", min_value=0, value=int(r), step=5)
            if st.button("💾 Rate Save Karo"):
                config["rates"] = new_rates
                save_config(config)
                st.success("Bhav save thai gaya!")

        with s2:
            st.subheader("👷 Delivery Boy Management")
            b_rem = st.selectbox("Naam Kadho:", ["-- Select --"] + config["delivery_boys"])
            if st.button("🗑️ Kadhi Nakho"):
                if b_rem != "-- Select --":
                    config["delivery_boys"].remove(b_rem)
                    save_config(config)
                    st.success("Nikali gayu!")
                    st.rerun()
            
            new_b = st.text_input("Nava Boy nu Naam:")
            if st.button("➕ Umero"):
                if new_b.strip() and new_b not in config["delivery_boys"]:
                    config["delivery_boys"].append(new_b.strip())
                    save_config(config)
                    st.success("Umerai gayu!")
                    st.rerun()
    else:
        st.warning("🔒 Password `1234` nakho.")

# ==========================================
# SCREEN 4: LINK GENERATOR MENU
# ==========================================
elif menu == "📱 Delivery Boy Link Generator":
    st.header("📱 Delivery Boy WhatsApp Link Generator")
    local_ip = get_local_ip()
    st.write("Tamara delivery boy na mobile ma WhatsApp par sidhi link moklavo:")
    
    for boy in config["delivery_boys"]:
        b_link = f"http://{local_ip}:8501/?page=entry&boy={boy}"
        st.info(f"**{boy} ni Link:**\n`{b_link}`")