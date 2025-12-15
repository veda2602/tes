import streamlit as st
import pandas as pd
import os
import io
import function
import numpy as np
import regex as re
import xlsxwriter
from zipfile import ZipFile
from pathlib import Path
import dickti

def datePatternAndroid(timeFormat, language): #Date Time Sender Framework to read
    match language:
        case "English":
            datePattern = r'^\d{1,2}/\d{1,2}/\d{2}'
            dateStructure = '%m/%d/%y'
            match timeFormat:
                case "12h":
                    dateTimeSenderPattern = r'(?P<DATE>\d{1,2}/\d{1,2}/\d{2}),\s*(?P<TIME>\d{1,2}:\d{2})\s*(?P<AMPM>AM|PM)\s*-\s*(?P<SENDER>.*?):' #TESTED
                case "24h":
                    dateTimeSenderPattern = r'(?P<DATE>\d{1,2}/\d{1,2}/\d{2}), (?P<TIME>\d{2}:\d{2}) - (?P<SENDER>.*?):' #TESTED
        case "Indonesian":
            datePattern = r'^\d{1,2}/\d{1,2}/\d{2}'
            dateStructure = '%d/%m/%y'
            match timeFormat:
                case "12h":
                    dateTimeSenderPattern = r'(?P<DATE>\d{1,2}/\d{1,2}/\d{2})\s*(?P<TIME>\d{1,2}.\d{2})\s*(?P<AMPM>AM|PM)\s*-\s*(?P<SENDER>.*?):' #NOT TESTED
                case "24h":
                    dateTimeSenderPattern = r'(?P<DATE>\d{1,2}/\d{1,2}/\d{2}) (?P<TIME>\d{2}.\d{2}) - (?P<SENDER>.*?):' #TESTED
        case "French":
            datePattern = r'^\d{2}/\d{2}/\d{4}'
            dateStructure = '%d/%m/%Y'
            match timeFormat:
                case "12h":
                    dateTimeSenderPattern = r'(?P<DATE>\d{2}/\d{2}/\d{4}),\s*(?P<TIME>\d{2}:\d{2})\s*(?P<AMPM>AM|PM)\s*-\s*(?P<SENDER>.*?):' #NOT TESTED
                case "24h":
                    dateTimeSenderPattern = r'(?P<DATE>\d{2}/\d{2}/\d{4}), (?P<TIME>\d{2}:\d{2}) - (?P<SENDER>.*?):' #NOT TESTED
    return datePattern, dateTimeSenderPattern, dateStructure

def readRawData(dataRaw, datePattern): #Reading Raw Data
    # New rows we'll build
    newRows = []
    currentRow = []

    for i, row in dataRaw.iterrows():
        content = str(row[0]).strip()

        if re.match(datePattern, content):
            # Start of a new message
            if currentRow:
                newRows.append(currentRow)
            currentRow = [content]
        else:
            # Continuation of previous message
            currentRow.append(content)

    # Append the last row
    if currentRow:
        newRows.append(currentRow)

    # Convert to DataFrame, fill missing columns
    maxLen = max(len(row) for row in newRows)
    normalizedRows = [row + [''] * (maxLen - len(row)) for row in newRows]
    columns = [f'col_{i+1}' for i in range(maxLen)]

    cleanData = pd.DataFrame(normalizedRows, columns=columns)

    # ONLY GETTING UNRECORDS
    # Keep rows where any cell contains 'UNRECORD' (case-insensitive)
    cleanData = cleanData[cleanData.apply(lambda row: row.astype(str).str.contains('UNRECORD', case=False).any(), axis=1)]

    # Reset index (optional)
    cleanData = cleanData.reset_index(drop=True)
    return cleanData

# EXTRACT DATA
def extractFieldFromText(text, field):
    pattern = rf'{field}\s*:\s*([^|\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extractQtyFromText(text):
    # Match QTY (or QTY FOUND, QTY ACTUAL) followed by optional colon/space, then digits, possibly followed by EA, PCS, etc.
    pattern = r'\b(QTY FOUND|QTY ACTUAL|QTY|QTY ACT)\b\s*:?\s*(\d+)\s*(EA|PCS)?'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(2))
    return np.nan

def extractBinEmroFromText(text):
    binEmro = extractFieldFromText(text, 'BIN EMRO')
    binActual = extractFieldFromText(text, 'BIN ACTUAL')
    binAct = extractFieldFromText(text, 'BIN ACT')
    bin_ = binActual if binActual else binAct if binAct else extractFieldFromText(text, 'BIN')
    return bin_, binEmro

def extractFieldFromRow(row, field):
    # Find columns in the row that contain the field keyword
    for col in row.index:
        cell = str(row[col])
        if pd.notna(cell) and re.search(fr'(?<![A-Za-z0-9]){field}\s*:\s*', cell, re.IGNORECASE):
            # Extract field value from this cell only
            if field == 'QTY':
                # Special case: extract QTY number
                QTY = extractQtyFromText(cell)
                if not np.isnan(QTY):
                    return QTY
            elif field == 'BIN':
                # Special case for BIN and BIN EMRO handled outside, skip here
                continue
            elif field == 'PN DESCRIPTION':
                continue
            else:
                val = extractFieldFromText(cell, field)
                if val:
                    return val
    return None if field != 'QTY' else np.nan

def extractAllFromRow(row):
    loc = extractFieldFromRow(row, 'LOC')
    pn = extractFieldFromRow(row, 'PN')
    sn = extractFieldFromRow(row, 'SN')
    remark = extractFieldFromRow(row, 'REMARK')
    remarks = extractFieldFromRow(row, 'REMARKS')
    category = extractFieldFromRow(row, 'CATEGORY')
    # For BIN and BIN EMRO, look for columns containing them and extract separately
    bin_, binEmro = None, None
    pn_description = None
    for col in row.index:
        cell = str(row[col])
        if pd.notna(cell):
            if re.search(r'BIN EMRO\s*:\s*', cell, re.IGNORECASE):
                binEmro = extractFieldFromText(cell, 'BIN EMRO')
            if re.search(r'BIN ACTUAL\b\s*:\s*', cell, re.IGNORECASE):
                bin_ = extractFieldFromText(cell, 'BIN ACTUAL')
            if re.search(r'BIN ACT\b\s*:\s*', cell, re.IGNORECASE):
                bin_ = extractFieldFromText(cell, 'BIN ACT')
            # If no BIN ACTUAL found, fallback to BIN
            if not bin_ and re.search(r'BIN\s*:\s*', cell, re.IGNORECASE):
                bin_ = extractFieldFromText(cell, 'BIN')
        
    for col in row.index:
            cell = str(row[col])
            if pd.notna(cell):
                if re.search(r'PN DESCRIPTION\s*:\s*', cell, re.IGNORECASE):
                    pn_description = extractFieldFromText(cell, 'PN DESCRIPTION')
                if re.search(r'DESCRIPTION\s*:\s*', cell, re.IGNORECASE):
                    pn_description = extractFieldFromText(cell, 'DESCRIPTION')
                if re.search(r'DESC\s*:\s*', cell, re.IGNORECASE):
                    pn_description = extractFieldFromText(cell, 'DESC')

    return pd.Series({
        'LOC': loc,
        'BIN ACTUAL/FOUND': bin_,
        'BIN EMRO': binEmro,
        'PN': pn,
        'SN': sn,
        'REMARK': remark,
        'REMARKS': remarks,
        'PN DESCRIPTION': pn_description,
        'CATEGORY': category
    })

def extractQtyAndUom(row):
    for cell in row:
        if isinstance(cell, str):
            match = re.search(r'\b(QTY FOUND|QTY ACTUAL|QTY|QTY ACT)\b\s*:?\s*(\d+)\s*([A-Z]+)?', cell, re.IGNORECASE)
            if match:
                return pd.Series([match.group(2), match.group(3)])
    return pd.Series([None, None])

def normalizeFileName(uploadedName: str) -> str:
    """
    Removes ' (number)' from an uploaded filename such as:
    'data (1).txt' -> 'data.txt'
    """
    p = uploadedName.name
    name, ext = os.path.splitext(p)
    # Remove trailing " (number)" using regex
    cleanedStem = re.sub(r" \(\d+\)$", "", name)

    return cleanedStem

def decideType(dataRaw):
    dataRawFile = dataRaw.name
    dataRawType = os.path.splitext(dataRawFile)[1]
    if dataRawType == '.txt':
        dataRaw1 = readTxtFromTxt(dataRaw)
    elif dataRawType == '.zip':
        dataRaw1 = readTxtFromZip(dataRaw)
    return dataRaw1

def readTxtFromTxt(dataRaw):
    if dataRaw is not None:
        dataRaw1 = pd.read_fwf(dataRaw, encoding='utf-8')
        return dataRaw1
    
def readTxtFromZip(dataRaw):
    dataRawNameNormalized = normalizeFileName(dataRaw)
    dataTxtInZip = os.path.splitext(dataRawNameNormalized)[0] + ".txt"
    if dataRaw is not None:
        zipBytes = io.BytesIO(dataRaw.getvalue())
        with ZipFile(zipBytes, 'r') as myZip:
            if dataRawNameNormalized:
                with myZip.open(dataTxtInZip, "r") as data:
                # The data is read as bytes, decode it to string for pandas.read_fwf
                # and wrap it in io.StringIO
                    decodedData = io.StringIO(data.read().decode('utf-8'))
                    dataTxt = pd.read_fwf(decodedData, encoding='utf-8')
                    return dataTxt

def readLocationData(dataLocationRaw):
    dataLocation = pd.read_excel(dataLocationRaw, skiprows=1)
    dataLocation = dataLocation[['LOCATION', 'LOCATION DESCRIPTION', 'STATION CODE']]
    return dataLocation

def dataProcessing(cleanData, dateTimeSenderPattern, dateOld, dateNew, dateStructure, phoneTimeFormat, dataLocation):
    # Extract the values into separate columns
    cleanDataExtracted = cleanData.iloc[:,0].str.extract(dateTimeSenderPattern)

    match phoneTimeFormat:
        case '12h':
            # Add the new columns to the original dataframe
            cleanData[['DATE', 'TIME', 'AM/PM', 'SENDER']] = cleanDataExtracted
            cleanData['TIME'] = cleanData['TIME'] + " " + cleanData['AM/PM']
            cleanData['TIME'] = pd.to_datetime(cleanData['TIME'], format='%I:%M %p').dt.strftime('%H:%M')
        case '24h':
            cleanData[['DATE', 'TIME', 'SENDER']] = cleanDataExtracted

    # DATE FILTER
    # Convert DATE column to datetime format (from string like '30/05/2025')
    cleanData['DATE'] = pd.to_datetime(cleanData['DATE'], format=dateStructure, errors='coerce')

    # Filter rows by date range
    dateOld = pd.to_datetime(dateOld)
    dateNew = pd.to_datetime(dateNew)
    cleanData = cleanData[(cleanData['DATE'] >= dateOld) & (cleanData['DATE'] <= dateNew)]
    
    # Reset index (optional)
    cleanData = cleanData.reset_index(drop=True)

    # Replace empty strings with NaN
    cleanData = cleanData.replace('', np.nan)
    
    # Drop columns where all values are NaN
    cleanData = cleanData.dropna(axis=1, how='all')
    cleanData['QTY'] = cleanData.apply(lambda row: extractQtyFromText(' '.join(row.astype(str))), axis=1)
    
    
    cleanData[['QTY', 'UOM']] = cleanData.apply(extractQtyAndUom, axis=1)
    cleanData['QTY'] = pd.to_numeric(cleanData['QTY'], errors='coerce')

    # Apply to your dataframe
    newCols = cleanData.apply(extractAllFromRow, axis=1)

    cleanData = pd.concat([cleanData, newCols], axis=1)

    # CHANGING QTY IF QTY IS ZERO
    cleanData['QTY'] = pd.to_numeric(cleanData['QTY'], errors='coerce')
    cleanData['QTY'] = cleanData['QTY'].replace('', np.nan)
    cleanData['QTY'] = cleanData['QTY'].fillna(1)
    
    # Replace blank strings with NaN to unify missing value treatment
    cleanData['REMARK'].replace('', np.nan, inplace=True)

    # For rows where LOC1 is NaN (including original blanks), fill with LOC2
    cleanData['REMARK'] = cleanData['REMARK'].fillna(cleanData['REMARKS'])

    # Drop LOC2
    cleanData = cleanData.drop(columns='REMARKS')

    # MERGE MESSAGE PARTS

    # Identify all columns that start with 'col_'
    messageCols = [col for col in cleanData.columns if col.startswith('col_')]

    # Concatenate only non-null and non-empty strings from the message columns
    cleanData['MESSAGE RAW'] = cleanData[messageCols].astype(str).apply(
        lambda row: ' '.join(val for val in row if val and val.strip().lower() != 'nan'),
        axis=1
    )

    # Optional: Trim leading/trailing whitespace
    cleanData['MESSAGE RAW'] = cleanData['MESSAGE RAW'].str.strip()
    cleanData = cleanData.drop(columns=[col for col in cleanData.columns if col.startswith('col_')])
    
    cleanData = cleanData.rename({'LOC':'LOCATION'}, axis=1)
    cleanData1 = cleanData.merge(dataLocation, how='left', on='LOCATION')
    cleanData1['MONTH'] = cleanData1['DATE'].dt.month_name()
    cleanData1['PIC'] = ''
    cleanData1['PENANGGUNG JAWAB'] = ''
    cleanData1['OWNER'] = ''
    cleanData1['CLASS'] = cleanData1['STATION CODE'].map(dickti.locationClass)
    cleanData1['PERIODE'] = cleanData1['DATE'].min().strftime('%d %B') + " - " + cleanData1['DATE'].max().strftime('%d %B %Y')
    cleanData1['PENYELESAIAN'] = ''
    cleanData1['STATUS'] = 'OPEN'
    cleanData = cleanData1.drop_duplicates(subset=['PN', 'SN', 'REMARK', 'TIME'], keep='first')
    cleanData = cleanData.reset_index(drop=True)
    cleanData['NO'] = cleanData.index + 1
    cleanData['TIME'] = pd.to_timedelta(cleanData['TIME'] + ':00')
    cleanData['DATE'] = cleanData['DATE'] + cleanData['TIME']
    cleanData['DATE (YYYY/MM/DD)'] = cleanData['DATE'].dt.strftime('%Y/%m/%d %H:%M:%S')
    cleanData = cleanData[['MONTH', 'PIC', 'PENANGGUNG JAWAB', 'OWNER', 'LOCATION DESCRIPTION', 'CLASS', 'PERIODE', 'STATION CODE', 'NO', 'LOCATION', 'BIN ACTUAL/FOUND', 'PN', 'SN', 'PN DESCRIPTION', 'CATEGORY', 'QTY', 'UOM', 'DATE', 'SENDER', 'REMARK', 'PENYELESAIAN', 'STATUS', 'BIN EMRO', 'MESSAGE RAW']]
    
    return cleanData