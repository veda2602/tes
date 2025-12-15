import streamlit as st
import pandas as pd
import io
import function

# ================= SIDEBAR =================
with st.sidebar:
    st.title("Procedures and Notes")
    with st.popover("Patch Notes v1.3.0"):
        st.write("1. Added extraction mode (Unrecord / All Messages)")
        st.write("2. Can export all WhatsApp messages")
        st.write("3. Unrecord logic preserved")

    st.subheader("App usage procedures:")
    st.write("1. Upload WhatsApp export (.txt or .zip) from Android")
    st.write("2. Choose date range, language, time format, and extraction mode")

# ================= MAIN =================
st.title("The Un-RECORDER App by Gz.")
st.write("WhatsApp Data Processing Application")
st.warning("Does not work when chat is exported via iPhone (Only Android)")

# ================= INPUT =================
dataRaw = st.file_uploader("Choose File .txt/.zip Export WA", type=['txt', 'zip'])

oldDate = st.date_input("Stock Opname Start Date", format='YYYY/MM/DD')
newDate = st.date_input("Stock Opname End Date", format='YYYY/MM/DD')

waLanguage = st.radio("WhatsApp Language:", ["English", "Indonesian", "French"])
phoneTimeFormat = st.radio(
    "Phone Time Format:",
    ["24h", "12h"],
    captions=["Example: 15:24", "Example: 03:24 PM"]
)

extractMode = st.radio(
    "Extraction Mode:",
    ["Unrecord Only", "All Messages"],
    help="Choose whether to export only Unrecorded data or all WhatsApp messages"
)

# ================= PROCESS =================
if dataRaw and st.button("Olah Data!", type="primary"):
    try:
        # Load master location
        dataLocation = function.readLocationData('./add_data/Data Master Location.xlsx')

        # Decide file type (txt / zip)
        dataRaw1 = function.decideType(dataRaw)

        # WhatsApp date pattern
        datePattern, dateTimeSenderPattern, dateStructure = function.datePatternAndroid(
            phoneTimeFormat, waLanguage
        )

        # Read raw WhatsApp messages
        processedData = function.readRawData(dataRaw1, datePattern)

        # Main processing
        allData, unrecordData = function.dataProcessing(
            processedData,
            dateTimeSenderPattern,
            oldDate,
            newDate,
            dateStructure,
            phoneTimeFormat,
            dataLocation,
            return_all=True
        )

        # Decide output
        if extractMode == "Unrecord Only":
            exportData = unrecordData
        else:
            exportData = allData

        # Metadata for filename
        locationExport = exportData['STATION CODE'].mode(dropna=True)[0]
        periodeExport = exportData['PERIODE'].mode(dropna=True)[0]

        # Excel output
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            exportData.to_excel(writer, sheet_name='Exported Data', index=False)

            if extractMode == "All Messages":
                unrecordData.to_excel(writer, sheet_name='Unrecord Only', index=False)

        output.seek(0)

        st.session_state['outputData'] = output
        st.session_state['filename'] = f"WA Data - {locationExport} - {periodeExport}.xlsx"

        st.success("Data successfully processed!")

    except Exception as e:
        st.error(f"Error: {e}")

# ================= DOWNLOAD =================
if 'outputData' in st.session_state:
    st.download_button(
        label="Download Excel",
        data=st.session_state['outputData'],
        file_name=st.session_state['filename'],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ================= FUNCTION DATA PROCESSING =================
# NOTE: PLACE THIS IN function.py
"""
def dataProcessing(rawData, dateTimeSenderPattern, oldDate, newDate,
                   dateStructure, phoneTimeFormat, dataLocation, return_all=False):

    df = rawData.copy()

    # --- Date filtering ---
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')
    df = df[(df['DATETIME'].dt.date >= oldDate) & (df['DATETIME'].dt.date <= newDate)]

    # --- Identify message type ---
    df['MESSAGE_TYPE'] = 'TEXT'
    df.loc[df['MESSAGE'].str.contains('<Media omitted>', na=False), 'MESSAGE_TYPE'] = 'MEDIA'

    # --- UNRECORD detection logic (example) ---
    df['IS_UNRECORD'] = False
    df.loc[df['MESSAGE'].str.contains('unrecord|stock opname', case=False, na=False), 'IS_UNRECORD'] = True

    # --- Category & PN Description ---
    df['CATEGORY'] = df['IS_UNRECORD'].map(lambda x: 'UNRECORDED' if x else 'GENERAL')
    df['PN_DESCRIPTION'] = df.apply(lambda x: x['MESSAGE'] if x['IS_UNRECORD'] else None, axis=1)

    # --- Location mapping ---
    df = df.merge(dataLocation, how='left', on='LOCATION')

    # --- Period ---
    df['PERIODE'] = df['DATETIME'].dt.strftime('%Y-%m')

    unrecord_df = df[df['IS_UNRECORD'] == True].reset_index(drop=True)

    if return_all:
        return df.reset_index(drop=True), unrecord_df

    return unrecord_df
"""
