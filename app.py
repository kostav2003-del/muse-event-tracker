# app.py  —  Muse Leads Tracker (Streamlit)
# run:  streamlit run app.py
import streamlit as st
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="Muse Leads Tracker", layout="wide")

DATA_PATH = "leads.csv"
STAGES = ["Νέο","Προσφορά","Ραντεβού","Προφ. Συμφωνία","Booked","Lost"]
SOURCES = ["Direct","Instagram","Google","Referral","Planner","Other"]
REASONS_LOST = ["Budget","Διαθεσιμότητα","Υπηρεσίες","Άλλος χώρος","No response","Other"]
VENUES = ["Muse Urban Venue","Couleur Locale"]

# --- Load / init data ---
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=[
        "Ημ_Αιτήματος","Όνομα","Email","Τηλέφωνο","Τύπος",
        "Ημ_Εκδήλωσης","Πηγή","Χώρος","Στάδιο","Booked",
        "Next_Action","Next_Action_Date","Reason_Lost","Budget_Range","Priority","Σχόλια"
    ])

def save_df(): df.to_csv(DATA_PATH, index=False)

st.title("Muse Urban Venue — Event Request Tracker")

# --- Sidebar filters ---
with st.sidebar:
    st.header("Φίλτρα")
    f_stage = st.multiselect("Στάδιο", STAGES, default=STAGES)
    f_source = st.multiselect("Πηγή", SOURCES, default=SOURCES)
    f_venue = st.multiselect("Χώρος", VENUES, default=VENUES)
    f_booked = st.selectbox("Booked", ["Όλα","Ναι","Όχι"])
    # filter
    fdf = df.copy()
    if not fdf.empty:
        fdf = fdf[fdf["Στάδιο"].isin(f_stage)]
        fdf = fdf[fdf["Πηγή"].isin(f_source)]
        fdf = fdf[fdf["Χώρος"].isin(f_venue)]
        if f_booked != "Όλα":
            fdf = fdf[fdf["Booked"] == (f_booked=="Ναι")]

# --- KPIs ---
col1,col2,col3,col4 = st.columns(4)
total = len(fdf)
booked = int(fdf["Booked"].sum()) if not fdf.empty else 0
conv = (booked/total*100) if total else 0
overdue = 0
if not fdf.empty and "Next_Action_Date" in fdf.columns:
    try:
        tmp = fdf.copy()
        tmp["Next_Action_Date"] = pd.to_datetime(tmp["Next_Action_Date"], errors="coerce")
        overdue = int(((tmp["Next_Action_Date"] < pd.Timestamp.today()) & (tmp["Booked"]==False)).sum())
    except: pass

col1.metric("Σύνολο Leads", total)
col2.metric("Booked", booked)
col3.metric("Conversion", f"{conv:.1f}%")
col4.metric("Καθυστερημένα Follow-ups", overdue)

st.markdown("---")

# --- Add / Edit form ---
with st.expander("➕ Προσθήκη / Επεξεργασία Lead", expanded=False):
    mode = st.radio("Λειτουργία", ["Νέο Lead","Επεξεργασία Υπάρχοντος"], horizontal=True)
    if mode == "Επεξεργασία Υπάρχοντος" and len(df)>0:
        idx = st.selectbox("Διάλεξε lead", df.index, format_func=lambda i: f"{df.at[i,'Όνομα']} — {df.at[i,'Ημ_Εκδήλωσης']}")
    else:
        idx = None

    colA,colB,colC = st.columns(3)
    with colA:
        him = st.date_input("Ημερομηνία Αιτήματος", value=date.today())
        name = st.text_input("Ονοματεπώνυμο")
        email = st.text_input("Email")
        tel = st.text_input("Τηλέφωνο")
        etype = st.text_input("Τύπος Εκδήλωσης (π.χ. Wedding, Birthday, Corporate)")
    with colB:
        evdate = st.date_input("Ημερομηνία Εκδήλωσης")
        source = st.selectbox("Πηγή", SOURCES)
        venue = st.selectbox("Χώρος", VENUES)
        stage = st.selectbox("Στάδιο", STAGES)
        booked_flag = st.checkbox("Booked", value=(stage=="Booked"))
    with colC:
        next_act = st.text_input("Next Action (π.χ. Call / Send revised offer)")
        next_date = st.date_input("Next Action Date", value=date.today())
        reason = st.selectbox("Reason Lost", [""]+REASONS_LOST)
        budget = st.selectbox("Budget Range", ["","<2k","2-4k","4-6k","6k+"])
        priority = st.selectbox("Priority", ["","A","B","C"])
    notes = st.text_area("Σχόλια")

    if st.button("💾 Αποθήκευση"):
        row = {
            "Ημ_Αιτήματος": str(him),
            "Όνομα": name, "Email": email, "Τηλέφωνο": tel, "Τύπος": etype,
            "Ημ_Εκδήλωσης": str(evdate), "Πηγή": source, "Χώρος": venue,
            "Στάδιο": stage, "Booked": bool(booked_flag),
            "Next_Action": next_act, "Next_Action_Date": str(next_date),
            "Reason_Lost": reason, "Budget_Range": budget, "Priority": priority,
            "Σχόλια": notes
        }
        if mode=="Επεξεργασία Υπάρχοντος" and idx is not None:
            for k,v in row.items(): df.at[idx,k]=v
        else:
            df.loc[len(df)] = row
        save_df()
        st.success("Αποθηκεύτηκε!")

# --- Table ---
st.subheader("Leads")
st.dataframe(fdf.sort_values(by="Ημ_Αιτήματος", ascending=False), use_container_width=True)

# --- Simple summaries ---
st.markdown("### Σύνοψη ανά Πηγή & Στάδιο")
if not fdf.empty:
    st.dataframe(
        pd.crosstab(fdf["Πηγή"], fdf["Στάδιο"]).assign(_Σύνολο=lambda x: x.sum(axis=1)),
        use_container_width=True
    )
