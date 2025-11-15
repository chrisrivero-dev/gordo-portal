import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
import urllib.parse as up

# ============================================
# MUST BE FIRST — BEFORE ANY NAV BUTTONS
# ============================================
st.set_page_config(page_title="GORDO PORTAL", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ============================================
# NAVIGATION BAR (Bulletproof Streamlit Version)
# ============================================

def nav_button(label, target_page):
    active = (st.session_state.page == target_page)
    button_id = f"nav-{label}"

    # Invisible Streamlit button for click detection
    clicked = st.button(label, key=button_id)

    if clicked:
        st.session_state.page = target_page
        st.rerun()

    # Replace the Streamlit button with your styled HTML
    st.markdown(
        f"""
        <style>
        #{button_id} {{
            display: none;
        }}
        .{button_id}-styled {{
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            text-align: center;
            border: none;
            color: {'#007bff' if active else '#ffffff'};
            background: {'#ffffff20' if active else '#00000000'};
        }}
        .{button_id}-styled:hover {{
            background: #ffffff15;
            color: #69aaff;
        }}
        </style>
        <div class="{button_id}-styled">{label}</div>
        """,
        unsafe_allow_html=True
    )


# ============================================
# PAGE STATE HANDLER
# ============================================
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def set_page(page):
    st.session_state.page = page

# ==========================================================
# BASIC CONFIG
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "leads.csv")

NAV_PAGES = ["Dashboard", "Leads", "AI Follow-Up", "Reports"]

# ==========================================================
# UTILITIES
# ==========================================================
def safe_text(val):
    """Ensure text fields never blow up with floats or None."""
    if isinstance(val, str):
        return val.strip()
    if val is None or pd.isna(val):
        return ""
    return str(val).strip()


def get_logo_path():
    path = os.path.join(os.path.dirname(__file__), "logo3.png")
    return path if os.path.exists(path) else None


logo_path = get_logo_path()


def wa_link(text):
    return f"https://wa.me/?text={up.quote(text or '')}"


def inject_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        st.error(f"CSS NOT LOADED — PATH IS WRONG: {css_path}")

# ====== VALIDATION HELPERS ======
def normalize_phone(phone_raw: str):
    """Return (digits_only, formatted_phone) or ('', '') if empty."""
    phone_raw = (phone_raw or "").strip()
    if not phone_raw:
        return "", ""

    digits = re.sub(r"\D", "", phone_raw)
    if len(digits) != 10:
        return None, None  # invalid
    formatted = f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"
    return digits, formatted


def validate_email(email: str):
    """Basic email sanity check. Empty is allowed."""
    email = (email or "").strip()
    if not email:
        return True
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def is_duplicate_lead(df, customer, company, email, phone_digits):
    """Check for duplicate vs existing rows."""
    cust_norm = customer.strip().lower()
    comp_norm = company.strip().lower()

    df_cust = df["Customer"].fillna("").str.strip().str.lower()
    df_comp = df["Company"].fillna("").str.strip().str.lower()

    mask = (df_cust == cust_norm) & (df_comp == comp_norm)

    if email:
        df_email = df["Email"].fillna("").str.strip().str.lower()
        mask = mask | (df_email == email.strip().lower())

    if "Phone" in df.columns and phone_digits:
        existing_digits = (
            df["Phone"]
            .fillna("")
            .astype(str)
            .str.replace(r"\D", "", regex=True)
        )
        mask = mask | (existing_digits == phone_digits)

    dupes = df[mask]
    return not dupes.empty, dupes

# ==========================================================
# DATA HELPERS
# ==========================================================
@st.cache_data(ttl=30)
def load_data():
    """Load CSV or initialize it."""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    expected_columns = [
        "Date",
        "Customer",
        "Company",
        "Product Interest",
        "Status",
        "Notes",
        "AI Follow-Up Message",
        "WhatsApp Link",
        "Email",
        "Phone",
        "Last Contact",
    ]

    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=expected_columns)
        df.to_csv(CSV_PATH, index=False)
        return df

    df = pd.read_csv(CSV_PATH)

    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_columns]
    return df


def save_data(df):
    df.to_csv(CSV_PATH, index=False)

# ==========================================================
# NAVBAR (Streamlit radio, styled like tabs)
# ==========================================================
def navbar():
    st.markdown("""
        <style>
        .top-nav {
            display: flex;
            justify-content: center;
            gap: 45px;
            padding: 16px 0 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 25px;
        }
        .nav-btn button {
            background: none;
            border: none;
            font-size: 18px;
            font-weight: 600;
            color: #bfbfbf;
            cursor: pointer;
            padding-bottom: 6px;
            transition: 0.25s;
        }
        .nav-btn button:hover {
            color: #FFD700;
        }
        .nav-btn-active {
            color: #FFD700 !important;
            border-bottom: 2px solid #FFD700;
            padding-bottom: 6px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="top-nav">', unsafe_allow_html=True)

    cols = st.columns(len(NAV_PAGES))

    for i, page in enumerate(NAV_PAGES):
        active_class = "nav-btn-active" if st.session_state.page == page else ""
        if cols[i].button(page, key=f"nav_{page}"):
            st.session_state.page = page
            st.rerun()

        cols[i].markdown(
            f"<div class='nav-btn {active_class}'></div>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
# HEADER
# ==========================================================
def header():
    inject_css()

    col_logo, col_title = st.columns([0.15, 0.85])

    with col_logo:
        st.image("logo3.png", width=85)

    with col_title:
        st.markdown(
            "<h1 style='color:#eab308; margin-bottom:6px; font-size:38px;'>GORDO PORTAL</h1>",
            unsafe_allow_html=True
        )

    navbar()

# ==========================================================
# PAGES
# ==========================================================
def dashboard_page(df):
    st.markdown("## Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="label">Active Orders</div>
            <div class="value">{(df['Status'] == 'Pending Order').sum()}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="label">Follow-Ups</div>
            <div class="value">{(df['Status'] == 'Follow-Up Needed').sum()}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="label">Hot Leads</div>
            <div class="value">{(df['Status'] == 'New Lead').sum()}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="label">Closed Deals</div>
            <div class="value">{(df['Status'] == 'Closed Deal').sum()}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("### Recent Activity")

    if len(df):
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True)
    else:
        st.info("No activity yet — add leads in the **Leads** page.")


def leads_page(df):
    st.markdown("## Leads")

    with st.expander("➕  Add New Lead", expanded=True):
        with st.form("lead_form"):
            c1, c2, c3 = st.columns(3)

            with c1:
                date = st.date_input("Date")
                customer = st.text_input("Customer")

            with c2:
                company = st.text_input("Company")
                product = st.text_input("Product Interest")

            with c3:
                status = st.selectbox(
                    "Status",
                    ["New Lead", "Follow-Up Needed", "Pending Order", "Closed Deal"],
                )
                email = st.text_input("Email (optional)")
                phone = st.text_input("Phone (optional)")

            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save Lead")

        if submitted:
            if not customer or not company:
                st.error("Please enter at least Customer and Company.")
                st.stop()

            if not email and not phone:
                st.error("Please provide at least one contact method (Email or Phone).")
                st.stop()

            if not validate_email(email):
                st.error("Email address looks invalid. Please check and try again.")
                st.stop()

            phone_digits, phone_formatted = "", ""
            if phone:
                phone_digits, phone_formatted = normalize_phone(phone)
                if phone_digits is None:
                    st.error("Phone number looks invalid. Expected 10 digits.")
                    st.stop()

            is_dup, dupes = is_duplicate_lead(df, customer, company, email, phone_digits)
            if is_dup:
                st.error("This lead looks like a duplicate. Check existing entries below.")
                st.dataframe(
                    dupes[
                        [
                            "Date",
                            "Customer",
                            "Company",
                            "Email",
                            "Phone",
                            "Status",
                        ]
                    ],
                    use_container_width=True,
                )
                st.stop()

            clean_customer = customer.strip().title()
            clean_company = company.strip().title()

            new_row = {
                "Date": str(date),
                "Customer": clean_customer,
                "Company": clean_company,
                "Product Interest": product.strip(),
                "Status": status,
                "Notes": notes.strip(),
                "AI Follow-Up Message": "",
                "WhatsApp Link": "",
                "Email": email.strip(),
                "Phone": phone_formatted,
                "Last Contact": "",
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success(f"Lead added for **{clean_customer}**")
            st.rerun()

    st.markdown("### All Leads")
    st.dataframe(df, use_container_width=True)

    return df

def ai_page(df):
    st.markdown("## AI Follow-Up Assistant")

    if df.empty:
        st.info("No leads yet — add one in the Leads tab.")
        return df

    options = []
    index_map = {}

    for i, row in df.iterrows():
        cust = safe_text(row.get("Customer"))
        comp = safe_text(row.get("Company"))
        prod = safe_text(row.get("Product Interest"))
        label = f"{i+1}. {cust} — {comp} — {prod}"
        options.append(label)
        index_map[label] = i

    selected_label = st.selectbox("Select Lead", options)
    idx = index_map[selected_label]
    lead = df.loc[idx]

    # ------------------------------------------
    # FIXED + PROFESSIONALLY STYLED AI CARD
    # ------------------------------------------
    summary_html = f"""
    <div class="ai-card" style="color:white;">
        <h4 style="color:#eab308; margin:0 0 10px 0; font-size:20px;">Lead Overview</h4>

        <div><strong>Customer:</strong> {safe_text(lead['Customer'])}</div>
        <div><strong>Company:</strong> {safe_text(lead['Company'])}</div>
        <div><strong>Product:</strong> {safe_text(lead['Product Interest'])}</div>
        <div><strong>Status:</strong> {safe_text(lead['Status'])}</div>
        <div><strong>Last Contact:</strong> {safe_text(lead['Last Contact'])}</div>
    </div>
    """

    st.components.v1.html(summary_html, height=220)
    # ------------------------------------------

    preset = st.selectbox(
        "Follow-up Style",
        [
            "Custom / Freestyle",
            "After Pricing Quote",
            "Check-In on Samples",
            "New Drop / Fresh Batch",
            "Re-Engage Cold Lead",
        ],
    )

    templates = {
        "After Pricing Quote": "Client asked about pricing — check in and answer questions.",
        "Check-In on Samples": "Follow up and ask how the sample performed.",
        "New Drop / Fresh Batch": "Notify the client about fresh inventory.",
        "Re-Engage Cold Lead": "Client went quiet — reopen the convo casually.",
    }

    default = templates.get(preset, "")
    notes = st.text_area("Notes / Context for AI", value=default, height=120)

    col1, col2 = st.columns([2, 1])

    with col1:
        generate = st.button("Generate Follow-Up", type="primary")

    with col2:
        wa_url = safe_text(lead.get("WhatsApp Link"))
        if wa_url.startswith("http"):
            st.link_button("Open WhatsApp Message", wa_url)
        else:
            st.button("Open WhatsApp Message", disabled=True)

    if generate:
        from ai_followup import generate_followup

        with st.spinner("Generating..."):
            msg = generate_followup(
                customer=safe_text(lead["Customer"]),
                company=safe_text(lead["Company"]),
                product=safe_text(lead["Product Interest"]),
                notes=notes,
            )

        df.at[idx, "AI Follow-Up Message"] = msg
        df.at[idx, "WhatsApp Link"] = wa_link(msg)
        df.at[idx, "Notes"] = notes
        df.at[idx, "Last Contact"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_data(df)
        st.success("AI message saved!")

    msg = safe_text(lead.get("AI Follow-Up Message"))
    if msg:
        st.markdown("### Latest AI Message")
        st.text_area("", msg, height=150)

    return df

def reports_page(df):
    st.markdown("## Reports")
    st.markdown(
        """
    <div class="report-card">
        <h4 style="margin-top:0; color:#eab308;">Reports Module – Coming Soon</h4>
        <p>This area will include:</p>
        <ul>
            <li>Lead conversion statistics</li>
            <li>Follow-up performance</li>
            <li>Closed deal history</li>
            <li>Order trends</li>
            <li>Monthly growth</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ==========================================================
# MAIN
# ==========================================================
def main():
    header()
    df = load_data()

    page = st.session_state.get("page", "Dashboard")
    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Leads":
        df = leads_page(df)
    elif page == "AI Follow-Up":
        df = ai_page(df)
    elif page == "Reports":
        reports_page(df)


if __name__ == "__main__":
    main()
