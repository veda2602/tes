import streamlit as st
import pandas as pd
import os
import io
import function
import numpy as np
import xlsxwriter

# ================= SIDEBAR =================
with st.sidebar:
    st.title("Procedures and Notes")
    with st.popover("Patch Notes v1.3.0"):
        st.write("1. Added Extraction Mode (Unrecord / All Messages)")
        st.write("2. Can export all WhatsApp messages")
        st.write("3. Original Unrecord logic preserved")

    st.subheader("App usage procedures:")
    st.write("1. Upload the txt file from the .zip file after exporting chat (include media)")
    st.write("2. Pick Stock Opname start & end date")
    st.write("3. Choose WhatsApp language, time format, and extraction mode")

# ================= MAIN =================
st.title("The Un-RECORDER App by Gz.")
st.write("Unrecord Data Processing Application, run in Streamlit")
st.warning("Does not work when chat is exported via iPhone (Only Android)")

# ================= INPUT =================
dataRaw = st.file_uploader("Choose File .txt/.zip Export WA", type=['txt', 'zip'])

oldDate = st.date_input("Stock Opname Start Date: (YYYY/MM/DD)", format='YYYY/MM/DD')
newDate = st.date_input("Stock Opname End Date: (YYYY/MM/DD)", format='YYYY/MM/DD')

waLanguage = st.radio("WhatsApp Language:", ["English", "Indonesian", "French"])
phoneTimeFormat = st.radio(
    "Phone Time Format:",
    ["24h", "12h"],
    captions=["Example: 15:24", "Example: 03:24 PM"]
)

# 🔥 NEW FEATURE
extractMode = st.radio(
    "Extraction Mode:",
    ["Unrecord Only", "All Messages"]
)

# ================= PROCESS =================
if dataRaw and st.button("Olah Data!", type="primary"):
    try:
        # ----- SAFE PATH FOR MASTER LOCATION -----
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        location_path = os.path.join(BASE_DIR, "Data Master Location.xlsx")

        if not os.path.exists(location_path):
            st.error("Data Master Location.xlsx not found!")
            st.stop()

        dataLocation = function.readLocationData(location_path)

        # ----- ORIGINAL PIPELINE -----
        dataRaw1 = function.decideType(dataRaw)
        datePattern, dateTimeSenderPattern, dateStructure = function.datePatternAndroid(
            phoneTimeFormat, waLanguage
        )

        processedData = function.readRawData(dataRaw1, datePattern)

        # ----- MODIFIED: GET ALL + UNRECORD -----
        allData, unrecordData = function.dataProcessing(
            processedData,
            dateTimeSenderPattern,
            oldDate,
            newDate,
            dateStructure,
            phoneTimeFormat,
            dataLocation,
            return_all=True   # 👈 IMPORTANT
        )

        # ----- SELECT OUTPUT -----
        if extractMode == "Unrecord Only":
            exportData = unrecordData
        else:
            exportData = allData

        # ----- FILE METADATA -----
        st.session_state['locationExport'] = exportData['STATION CODE'].mode(dropna=True)[0]
        st.session_state['periodeExport'] = exportData['PERIODE'].mode(dropna=True)[0]

        # ----- EXCEL OUTPUT -----
        output = io.BytesIO()
        with pd.ExcelWriter(
            output,
            engine='xlsxwriter',
            date_format='m/d/yyyy',
            datetime_format='m/d/yyyy HH:MM:SS'
        ) as writer:

            exportData.to_excel(writer, sheet_name='Exported Data', index=False)

            if extractMode == "All Messages":
                unrecordData.to_excel(writer, sheet_name='Unrecord Only', index=False)

        output.seek(0)
        st.session_state['outputData'] = output

        st.success("Data successfully processed!")

    except Exception as errorCode:
        st.error(f"Error: {errorCode}")

# ================= DOWNLOAD =================
if 'outputData' in st.session_state:
    st.download_button(
        label="Download Data",
        data=st.session_state['outputData'],
        file_name="Unrecord Data - %s - %s.xlsx" % (
            st.session_state['locationExport'],
            st.session_state['periodeExport']
        ),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
