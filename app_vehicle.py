import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
import io

st.set_page_config(
    page_title="Fleet Availability Planner",
    page_icon="🚛",
    layout="wide",
)

# ── Column mapping ──────────────────────────────────────────────
COL_DEPART = "Confirmed Depart DC Time"
COL_RETURN = "Confirmed Return DC Time"
ACCENT     = "#01bab4"
ACCENT_LIGHT = "#e6faf9"
ACCENT_MID   = "#b3eeec"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}
[data-testid="stAppViewContainer"] {{ background: #F8FAFC; }}
[data-testid="stHeader"] {{ background: transparent; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div > div {{
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    min-height: 40px !important;
    font-size: 13px !important;
}}
[data-testid="stMultiSelect"] > div > div:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px rgba(1,186,180,.12) !important;
}}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
    background: {ACCENT_LIGHT} !important;
    color: #007a75 !important;
    border-radius: 4px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}}

/* ── Run Analysis button — full width ── */
[data-testid="stSidebar"] [data-testid="stButton"],
[data-testid="stSidebar"] [data-testid="stButton"] > button,
[data-testid="stSidebar"] div:has(> [data-testid="stButton"]) {{
    width: 100% !important;
    display: block !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button {{
    background: #1E293B !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    width: 100% !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,.15) !important;
    transition: background .15s, box-shadow .15s !important;
    box-sizing: border-box !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
    background: #0F172A !important;
    box-shadow: 0 4px 12px rgba(0,0,0,.25) !important;
}}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {{
    background: #FFFFFF !important;
    color: #1E293B !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 18px !important;
    transition: all .15s !important;
}}
[data-testid="stDownloadButton"] > button:hover {{
    border-color: {ACCENT} !important;
    color: {ACCENT} !important;
}}

/* ── Level-1 expander (Date + Slot) ── */
[data-testid="stExpander"] {{
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.05) !important;
    margin-bottom: 10px !important;
    overflow: hidden !important;
}}
[data-testid="stExpander"] > details > summary {{
    padding: 18px 24px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    border-left: 4px solid #CBD5E1 !important;
    transition: background .15s, border-color .15s, color .15s !important;
}}
[data-testid="stExpander"] > details > summary:hover {{
    background: {ACCENT_LIGHT} !important;
    border-left-color: {ACCENT} !important;
}}
[data-testid="stExpander"] > details[open] > summary {{
    border-left-color: {ACCENT} !important;
    background: {ACCENT_LIGHT} !important;
    color: #005a57 !important;
}}

/* ── Level-2 expander (Carrier) ── */
[data-testid="stExpander"] [data-testid="stExpander"] {{
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-left: 3px solid #E2E8F0 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    margin-bottom: 6px !important;
}}
[data-testid="stExpander"] [data-testid="stExpander"] > details > summary {{
    padding: 12px 18px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #334155 !important;
    border-left: none !important;
    transition: background .15s, color .15s !important;
}}
[data-testid="stExpander"] [data-testid="stExpander"] > details > summary:hover {{
    background: {ACCENT_LIGHT} !important;
    color: #007a75 !important;
}}
[data-testid="stExpander"] [data-testid="stExpander"] > details[open] > summary {{
    background: {ACCENT_LIGHT} !important;
    color: #007a75 !important;
}}
[data-testid="stExpander"] [data-testid="stExpander"]:has(> details[open]) {{
    border-left-color: {ACCENT} !important;
}}
</style>
""", unsafe_allow_html=True)


# ─── COMPUTE ────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_availability(file_bytes: bytes):
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0)
    df.columns = df.columns.str.strip()

    required = {"Carrier Name", "Vehicle Reg", "Truck Type", "Truck Category",
                COL_DEPART, COL_RETURN}
    missing = required - set(df.columns)
    if missing:
        st.error(f"ไม่พบ column: {missing}"); st.stop()

    df = df.dropna(subset=["Vehicle Reg", "Carrier Name", COL_DEPART, COL_RETURN]).copy()
    df[COL_DEPART] = pd.to_datetime(df[COL_DEPART])
    df[COL_RETURN] = pd.to_datetime(df[COL_RETURN])
    df["Truck Category"] = df["Truck Category"].fillna("Unknown")

    vehicle_info = (
        df.groupby(["Carrier Name", "Vehicle Reg"])
        .agg(TruckType=("Truck Type",     lambda x: x.mode().iloc[0]),
             TruckCat  =("Truck Category", lambda x: x.mode().iloc[0]))
        .reset_index()
        .rename(columns={"TruckType": "Truck Type", "TruckCat": "Truck Category"})
    )
    v_carriers = vehicle_info["Carrier Name"].values
    v_regs     = vehicle_info["Vehicle Reg"].values
    v_types    = vehicle_info["Truck Type"].values
    v_cats     = vehicle_info["Truck Category"].values

    min_dt = df[COL_DEPART].min().floor("h")
    max_dt = df[COL_RETURN].max().floor("h")
    slots  = pd.date_range(min_dt, max_dt, freq="h")

    depart      = df[COL_DEPART].values
    ret         = df[COL_RETURN].values
    carrier_col = df["Carrier Name"].values
    vreg_col    = df["Vehicle Reg"].values

    day_names = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
                 4:"Friday",5:"Saturday",6:"Sunday"}
    records = []
    for slot_start in slots:
        slot_end    = slot_start + timedelta(hours=1)
        slot_end_np = np.datetime64(slot_end)
        busy_mask   = (depart < slot_end_np) & (ret >= slot_end_np)
        busy_set    = set(zip(carrier_col[busy_mask], vreg_col[busy_mask]))
        avail_idx   = [i for i,(c,v) in enumerate(zip(v_carriers,v_regs))
                       if (c,v) not in busy_set]
        time_slot   = f"{slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"
        for i in avail_idx:
            records.append({
                "Date":           slot_start.date(),
                "Day":            day_names[slot_start.weekday()],
                "Time Slot":      time_slot,
                "Carrier Name":   v_carriers[i],
                "Vehicle Reg":    v_regs[i],
                "Truck Category": v_cats[i],
                "Truck Type":     v_types[i],
            })
    result = pd.DataFrame(records) if records else pd.DataFrame(
        columns=["Date","Day","Time Slot","Carrier Name",
                 "Vehicle Reg","Truck Category","Truck Type"])
    return result, vehicle_info


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    exp = df.copy()
    exp["Date"] = pd.to_datetime(exp["Date"]).dt.strftime("%d/%m/%Y")
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        exp.to_excel(writer, index=False, sheet_name="Available Vehicles")
        ws, wb = writer.sheets["Available Vehicles"], writer.book
        hdr = wb.add_format({"bold":True,"bg_color":"#1E293B",
                             "font_color":"white","border":1})
        for c,n in enumerate(exp.columns): ws.write(0,c,n,hdr)
        for i,w in enumerate([13,10,14,40,18,14,22]): ws.set_column(i,i,w)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="background:#1E293B;padding:16px 20px 14px;
                margin:-1rem -1rem 1rem;display:flex;align-items:center;gap:12px">
      <span style="font-size:34px;line-height:1">🚛</span>
      <div>
        <div style="color:#FFF;font-size:15px;font-weight:800;line-height:1.1">Fleet Planner</div>
        <div style="color:#94A3B8;font-size:11px;margin-top:1px">Availability Analysis</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload Excel", type=["xlsx","xls"],
                                label_visibility="collapsed")

    if uploaded:
        with st.spinner("กำลังประมวลผล..."):
            avail_df, vehicle_info = compute_availability(uploaded.read())

        def flabel(text):
            st.markdown(
                f'<p style="font-size:11px;font-weight:700;color:#64748B;'
                f'text-transform:uppercase;letter-spacing:.8px;margin:14px 0 4px">'
                f'{text}</p>', unsafe_allow_html=True)

        # Date — empty by default
        flabel("📅 Date")
        dates_all = sorted(avail_df["Date"].unique())
        sel_dates = st.multiselect(
            "Date", options=dates_all, default=[],
            format_func=lambda d: pd.Timestamp(d).strftime("%d/%m/%Y (%a)"),
            placeholder="Select dates...",
            label_visibility="collapsed")

        # Time Slot — empty by default
        flabel("🕐 Time Slot")
        times_all = sorted(avail_df["Time Slot"].unique())
        sel_times = st.multiselect(
            "Time", options=times_all, default=[],
            placeholder="Select time slots...",
            label_visibility="collapsed")

        # Truck Category — pre-filled
        flabel("🚚 Truck Category")
        cats_all = sorted(avail_df["Truck Category"].unique())
        sel_cats = st.multiselect(
            "Truck Cat", options=cats_all, default=cats_all,
            label_visibility="collapsed")

        # Carrier — pre-filled
        flabel("🏢 Carrier")
        carriers_all = sorted(avail_df["Carrier Name"].unique())
        sel_carriers = st.multiselect(
            "Carrier", options=carriers_all, default=carriers_all,
            label_visibility="collapsed")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("🔎  Run Analysis", use_container_width=True):
            st.session_state["last_result"] = (sel_dates, sel_times, sel_cats, sel_carriers)


# ════════════════════════════════════════════════════════════════
#  MAIN — Welcome screen (no file uploaded)
# ════════════════════════════════════════════════════════════════
if not uploaded:
    # Centre column layout
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;font-size:60px;margin-bottom:8px'>🚛</div>",
            unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center;font-size:26px;font-weight:800;"
            "color:#1E293B;margin:0 0 6px'>Fleet Availability Planner</h1>",
            unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#64748B;font-size:14px;margin:0 0 28px'>"
            "Upload your Excel route file in the sidebar to get started</p>",
            unsafe_allow_html=True)

        # Required columns card using native st.markdown table-free approach
        st.markdown(
            f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;"
            f"padding:28px 32px;box-shadow:0 2px 8px rgba(0,0,0,.06)'>",
            unsafe_allow_html=True)

        st.markdown(
            "<p style='font-size:11px;font-weight:700;color:#64748B;"
            "text-transform:uppercase;letter-spacing:.8px;margin:0 0 18px'>"
            "📋 &nbsp;Required Excel Columns</p>",
            unsafe_allow_html=True)

        columns_list = [
            "Carrier Name",
            "Vehicle Reg",
            "Truck Type",
            "Truck Category",
            "Confirmed Depart DC Time",
            "Confirmed Return DC Time",
        ]
        for i, col_name in enumerate(columns_list, 1):
            st.markdown(
                f"<div style='padding:9px 0;border-bottom:1px solid #F1F5F9;"
                f"display:flex;align-items:center;gap:0'>"
                f"<span style='background:{ACCENT};color:#fff;border-radius:50%;"
                f"width:22px;height:22px;font-size:11px;font-weight:800;"
                f"text-align:center;line-height:22px;display:inline-block;"
                f"margin-right:12px;flex-shrink:0'>{i}</span>"
                f"<span style='font-size:14px;font-weight:600;color:#1E293B;"
                f"font-family:monospace'>{col_name}</span>"
                f"</div>",
                unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════
#  METRICS
# ════════════════════════════════════════════════════════════════
total_fleet    = len(vehicle_info)
unique_dates_n = avail_df["Date"].nunique()
total_carriers = avail_df["Carrier Name"].nunique()
min_date_str   = pd.Timestamp(avail_df["Date"].min()).strftime("%d %b %Y")
max_date_str   = pd.Timestamp(avail_df["Date"].max()).strftime("%d %b %Y")

st.markdown(f"""
<div style="background:#1E293B;border-radius:12px;padding:20px 28px;
            display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
  <div style="display:flex;align-items:center;gap:14px">
    <span style="font-size:32px">🚛</span>
    <div>
      <div style="color:#FFF;font-size:18px;font-weight:800;letter-spacing:-.3px">
        Fleet Availability Planner</div>
      <div style="color:#94A3B8;font-size:12px;margin-top:2px">
        Data: {min_date_str} – {max_date_str}</div>
    </div>
  </div>
  <div style="background:rgba(1,186,180,.2);color:#01bab4;
              border:1px solid rgba(1,186,180,.25);
              padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600">
    app_vehicle
  </div>
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px">
  <div style="background:#FFF;border:1px solid #E2E8F0;border-left:4px solid {ACCENT};
              border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;
                letter-spacing:.8px;margin-bottom:8px">Total Fleet</div>
    <div style="font-size:28px;font-weight:800;color:#1E293B;line-height:1">{total_fleet:,}</div>
    <div style="font-size:12px;color:#64748B;margin-top:4px">vehicles registered</div>
  </div>
  <div style="background:#FFF;border:1px solid #E2E8F0;border-left:4px solid #10B981;
              border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;
                letter-spacing:.8px;margin-bottom:8px">Days in Data</div>
    <div style="font-size:28px;font-weight:800;color:#1E293B;line-height:1">{unique_dates_n}</div>
    <div style="font-size:12px;color:#64748B;margin-top:4px">{min_date_str} – {max_date_str}</div>
  </div>
  <div style="background:#FFF;border:1px solid #E2E8F0;border-left:4px solid #F59E0B;
              border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;
                letter-spacing:.8px;margin-bottom:8px">Carriers</div>
    <div style="font-size:28px;font-weight:800;color:#1E293B;line-height:1">{total_carriers}</div>
    <div style="font-size:12px;color:#64748B;margin-top:4px">transport companies</div>
  </div>
  <div style="background:#FFF;border:1px solid #E2E8F0;border-left:4px solid #8B5CF6;
              border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;
                letter-spacing:.8px;margin-bottom:8px">Considering Period</div>
    <div style="font-size:15px;font-weight:800;color:#1E293B;line-height:1.3">{min_date_str}</div>
    <div style="font-size:12px;color:#64748B;margin-top:2px">to {max_date_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  WAIT / RESULTS
# ════════════════════════════════════════════════════════════════
if "last_result" not in st.session_state:
    st.markdown("""
    <div style="background:#FFF;border:1px solid #E2E8F0;border-radius:12px;
                padding:52px;text-align:center">
      <div style="font-size:32px;margin-bottom:12px">🔎</div>
      <div style="font-size:15px;font-weight:700;color:#1E293B;margin-bottom:6px">
        Ready to analyse</div>
      <div style="font-size:13px;color:#64748B">
        Select filters in the sidebar then click <strong>Run Analysis</strong></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

s_dates, s_times, s_cats, s_carriers = st.session_state["last_result"]

# Validate required filters
if not s_dates or not s_times:
    st.warning("⚠️  กรุณาเลือก **Date** และ **Time Slot** ก่อนกด Run Analysis")
    st.stop()

filtered = avail_df[
    avail_df["Date"].isin(s_dates) &
    avail_df["Time Slot"].isin(s_times) &
    avail_df["Truck Category"].isin(s_cats) &
    avail_df["Carrier Name"].isin(s_carriers)
].copy()

unique_veh = filtered["Vehicle Reg"].nunique()
h1, h2 = st.columns([7,1])
with h1:
    st.markdown(f"""
    <div style="margin-bottom:18px">
      <div style="font-size:17px;font-weight:800;color:#1E293B">📋 Availability Results</div>
      <div style="font-size:13px;color:#64748B;margin-top:3px">
        <strong style="color:{ACCENT}">{unique_veh:,}</strong> unique vehicles &nbsp;·&nbsp;
        <strong style="color:{ACCENT}">{len(filtered):,}</strong> vehicle-slots matched
      </div>
    </div>
    """, unsafe_allow_html=True)
with h2:
    if len(filtered) > 0:
        st.download_button("⬇ Export", data=to_excel_bytes(filtered),
                           file_name="vehicle_availability_export.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if len(filtered) == 0:
    st.markdown("""
    <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:10px;
                padding:28px;text-align:center">
      <div style="font-size:24px;margin-bottom:8px">⚠️</div>
      <div style="font-size:14px;font-weight:600;color:#92400E">
        No vehicles match all selected criteria</div>
      <div style="font-size:13px;color:#B45309;margin-top:4px">Try adjusting your filters</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── 3-Level Drill-down ─────────────────────────────────────────
for date_val in sorted(filtered["Date"].unique()):
    df_date = filtered[filtered["Date"] == date_val]
    date_d  = pd.Timestamp(date_val).strftime("%d %B %Y")
    day_d   = pd.Timestamp(date_val).strftime("%A")

    for slot in sorted(df_date["Time Slot"].unique()):
        df_slot    = df_date[df_date["Time Slot"] == slot]
        slot_count = df_slot["Vehicle Reg"].nunique()

        lv1 = (f"📅  {date_d}  ({day_d})"
               f"     🕐  {slot}"
               f"     🚛  {slot_count:,} vehicles available")
        with st.expander(lv1, expanded=False):
            for carrier in sorted(df_slot["Carrier Name"].unique()):
                df_c  = df_slot[df_slot["Carrier Name"] == carrier]
                c_cnt = df_c["Vehicle Reg"].nunique()
                lv2   = f"🏢  {carrier}     ·     {c_cnt} vehicles"
                with st.expander(lv2, expanded=False):
                    tbl = (
                        df_c[["Truck Category","Truck Type","Vehicle Reg"]]
                        .drop_duplicates(subset=["Vehicle Reg"])
                        .sort_values(["Truck Category","Vehicle Reg"])
                        .reset_index(drop=True)
                    )
                    rows_html = ""
                    for idx, row in tbl.iterrows():
                        bg = "#FFFFFF" if idx % 2 == 0 else "#e6faf9"
                        rows_html += f"""
                        <tr style="background:{bg}">
                          <td style="padding:11px 18px;color:#94A3B8;font-size:13px;
                                     font-weight:600;width:52px">{idx+1}</td>
                          <td style="padding:11px 18px;font-size:13px;font-weight:600;
                                     color:#1E293B">{row['Truck Category']}</td>
                          <td style="padding:11px 18px;font-size:12px;color:#64748B">
                            {row['Truck Type']}</td>
                          <td style="padding:11px 18px">
                            <span style="background:#e6faf9;color:#007a75;border-radius:5px;
                                         padding:4px 11px;font-family:'Courier New',monospace;
                                         font-size:12px;font-weight:700;
                                         border:1px solid #b3eeec">
                              {row['Vehicle Reg']}
                            </span>
                          </td>
                        </tr>"""

                    st.markdown(f"""
                    <div style="border:1px solid #E2E8F0;border-radius:8px;
                                overflow:hidden;margin:6px 0 8px">
                      <table style="width:100%;border-collapse:collapse">
                        <thead>
                          <tr style="background:#F1F5F9">
                            <th style="padding:10px 18px;text-align:left;font-size:11px;
                                       font-weight:700;color:#64748B;text-transform:uppercase;
                                       letter-spacing:.7px;border-bottom:1px solid #E2E8F0;
                                       width:52px">#</th>
                            <th style="padding:10px 18px;text-align:left;font-size:11px;
                                       font-weight:700;color:#64748B;text-transform:uppercase;
                                       letter-spacing:.7px;border-bottom:1px solid #E2E8F0">
                              Truck Category</th>
                            <th style="padding:10px 18px;text-align:left;font-size:11px;
                                       font-weight:700;color:#64748B;text-transform:uppercase;
                                       letter-spacing:.7px;border-bottom:1px solid #E2E8F0">
                              Truck Type</th>
                            <th style="padding:10px 18px;text-align:left;font-size:11px;
                                       font-weight:700;color:#64748B;text-transform:uppercase;
                                       letter-spacing:.7px;border-bottom:1px solid #E2E8F0">
                              Vehicle Reg</th>
                          </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                      </table>
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:28px 0 10px;color:#CBD5E1;font-size:12px">
  Fleet Availability Planner · app_vehicle
</div>
""", unsafe_allow_html=True)
