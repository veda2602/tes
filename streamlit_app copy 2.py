import streamlit as st
import pandas as pd
import os
import io
import function
import numpy as np
import xlsxwriter

with st.sidebar:
    st.title("Procedures and Notes")
    with st.popover("Patch Notes v1.2.5"):
        st.write("1. Followed regulated Unrecord Format")
        st.write("2. Added column PN_DESCRIPTION and CATEGORY. If the report has said data it should pick the data.")
        st.write("3. Added other columns to follow the format in number 1.")
        st.write("4. Added embedded data master location.")
        st.write("5. Can process duplicated zip file")
        st.write("6. Fixed time")
    st.subheader("App usage procedures:")
    st.write("1. Upload the txt file from the .zip file after exporting chat (You must pick *include media* when exporting the chat file)")
    st.write("2. Pick the Stock Opname start date and end date (to prevent older Stock Opname data to be extracted), and pick the appropriate WhatsApp language and time format.")

st.title("The Un-RECORDER App by Gz.")
st.write("Unrecord Data Processing Application, run in Streamlit")
st.warning("Does not work when chat is exported via iPhone (Only Android)")

dataRaw = st.file_uploader("Choose File .txt/.zip Export WA", type=['txt', 'zip'])

oldDate = st.date_input("Stock Opname Start Date: (YYYY/MM/DD)", format='YYYY/MM/DD')
newDate = st.date_input("Stock Opname End Date: (YYYY/MM/DD)", format='YYYY/MM/DD')

waLanguage = st.radio("WhatsApp Language:",["English", "Indonesian", "French"])
phoneTimeFormat = st.radio("Phone Time Format:", ["24h", "12h"], captions=["Example: 15:24","Example: 03:24 PM"])

if dataRaw and oldDate and newDate and waLanguage and phoneTimeFormat:
    if st.button("Olah Data!", type="primary"):  
        try:
            dataLocation = function.readLocationData('Data Master Location.xlsx')
            
            dataRaw1 = function.decideType(dataRaw)
            datePattern, dateTimeSenderPattern, dateStructure = function.datePatternAndroid(phoneTimeFormat, waLanguage)
            processedData = function.readRawData(dataRaw1, datePattern)
            cleanData = function.dataProcessing(processedData, dateTimeSenderPattern, oldDate, newDate, dateStructure, phoneTimeFormat, dataLocation)

            locationExport = cleanData['LOCATION'].mode()
            periodeExport = cleanData['PERIODE'].mode()
            st.session_state['locationExport'] = cleanData['STATION CODE'].mode()[0]
            st.session_state['periodeExport'] = cleanData['PERIODE'].mode()[0]
            
            output = io.BytesIO()

            with pd.ExcelWriter(output, date_format='m/d/yyyy', datetime_format='m/d/yyyy HH:MM:SS', engine='xlsxwriter') as writer:
                cleanData.to_excel(writer, sheet_name='Data Unrecord', index=True)
            
            output.seek(0)
            st.session_state['outputData'] = output

        except Exception as errorCode:
            st.error(f"Error: {errorCode}")


    if 'outputData' in st.session_state:
        st.download_button(
            label="Download Data Unrecord",
            data=st.session_state['outputData'],
            file_name="Unrecord Data - %s - %s.xlsx" %(
                st.session_state['locationExport'], 
                st.session_state['periodeExport']),
            mime="text/csv"
        )