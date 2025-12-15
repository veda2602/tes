import streamlit as st
import pandas as pd
import os
import io
import function
import xlsxwriter

# ================= SIDEBAR =================
with st.sidebar:
    st.title("Procedures and Notes")
    st.write("1. Upload WhatsApp export (.txt / .zip)")
    st.write("2. Choose date range")
    st.write("3. Choose extraction mode")

# ================= MAIN =================
st.title("The Un-RECORDER App by Gz.")
st.warning("Only works with WhatsApp Android export")

dataRaw = st.file_uploader(
    "Choose File .txt/.zip Export WA",
    type=["txt", "zip"]
)

oldDate = st.date_input("Stock Opname Start Date")
newDate = st.date_input("Stock Opname End Date")

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
# ================= PROCESS =================
if dataRaw and st.button("Olah Data!", type="primary"):
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        location_path = os.path.join(BASE_DIR, "Data Master Location.xlsx")

        if not os.path.exists(location_path):
            st.error("Data Master Location.xlsx NOT FOUND")
            st.stop()

        dataLocation = function.readLocationData(location_path)

        # 1️⃣ Read raw WA
        dataRaw1 = function.decideType(dataRaw)

        # 2️⃣ Get date patterns
        datePattern, dateTimeSenderPattern, dateStructure = (
            function.datePatternAndroid(phoneTimeFormat, waLanguage)
        )

        # 3️⃣ Read & split messages
        processedData = function.readRawData(
            dataRaw1,
            datePattern
        )

        # 4️⃣ PROCESS (INI YANG BENAR)
        cleanData = function.dataProcessing(
            processedData,
            dateTimeSenderPattern,
            oldDate,
            newDate,
            dateStructure,
            phoneTimeFormat,
            dataLocation
        )
# ================= FLAG UNRECORD =================
        cleanData["IS_UNRECORD"] = cleanData["MESSAGE RAW"].str.contains(
    "UNRECORD",
    case=False,
    na=False
)

        # ================= MODE =================
        if extractMode == "Unrecord Only":
            exportData = cleanData[cleanData["IS_UNRECORD"]].copy()
        else:
            exportData = cleanData.copy()

        # ================= EXPORT =================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            exportData.to_excel(
                writer,
                sheet_name="Exported Data",
                index=False
            )

        output.seek(0)
        st.session_state["output"] = output

        st.success("Data processed successfully")

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
