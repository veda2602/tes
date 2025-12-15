import streamlit as st
import pandas as pd
import os
import io
import function
import xlsxwriter

st.set_page_config(layout="wide")

# ================= SIDEBAR =================
with st.sidebar:
    st.title("Procedures and Notes")
    st.subheader("App usage procedures:")
    st.write("1. Upload WhatsApp export (.txt / .zip) from Android")
    st.write("2. Pick date range, language, time format")
    st.write("3. Choose extraction mode")

# ================= MAIN =================
st.title("The Un-RECORDER App by Gz.")
st.warning("Works ONLY with WhatsApp Android export")

dataRaw = st.file_uploader(
    "Choose File .txt/.zip Export WA",
    type=['txt', 'zip']
)

oldDate = st.date_input("Start Date (YYYY/MM/DD)")
newDate = st.date_input("End Date (YYYY/MM/DD)")

waLanguage = st.radio(
    "WhatsApp Language:",
    ["English", "Indonesian", "French"]
)

phoneTimeFormat = st.radio(
    "Phone Time Format:",
    ["24h", "12h"]
)

extractMode = st.radio(
    "Extraction Mode:",
    ["Unrecord Only", "All Messages"]
)

# ================= PROCESS =================
if dataRaw and st.button("Olah Data!", type="primary"):
    try:
        # --- Load master location ---
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        location_path = os.path.join(BASE_DIR, "Data Master Location.xlsx")

        if not os.path.exists(location_path):
            st.error("Data Master Location.xlsx NOT FOUND")
            st.stop()

        dataLocation = function.readLocationData(location_path)

        # --- Parse WhatsApp data ---
        raw = function.decideType(dataRaw)
        datePattern, dateTimeSenderPattern, dateStructure = \
            function.datePatternAndroid(phoneTimeFormat, waLanguage)

        processed = function.readRawData(raw, datePattern)

        allData, unrecordData = function.dataProcessing(
            processed,
            oldDate,
            newDate,
            dataLocation
        )

        exportData = unrecordData if extractMode == "Unrecord Only" else allData

        # --- Excel export ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            exportData.to_excel(writer, sheet_name="Exported Data", index=False)

            if extractMode == "All Messages":
                unrecordData.to_excel(
                    writer, sheet_name="Unrecord Only", index=False
                )

        output.seek(0)
        st.session_state["output"] = output

        st.success("Processing completed successfully!")

    except Exception as e:
        st.error(f"ERROR: {e}")

# ================= DOWNLOAD =================
if "output" in st.session_state:
    st.download_button(
        "Download Excel",
        st.session_state["output"],
        file_name="WA_Unrecord_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

