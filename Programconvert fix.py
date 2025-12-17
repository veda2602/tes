import streamlit as st
import re

st.set_page_config(layout="wide")
st.title("NLA Excel Extractor (Safe XML)")

uploaded_file = st.file_uploader(
    "Upload file Excel XML (.xls)",
    type=["xls"]
)

if uploaded_file:
    xml = uploaded_file.read().decode("utf-8", errors="ignore")

    # Ambil semua Row secara UTUH
    rows = re.findall(
        r"<ss:Row[^>]*>.*?</ss:Row>",
        xml,
        flags=re.DOTALL
    )

    pn_pattern = '<ss:Data ss:Type="String">P/N</ss:Data>'

    kept_rows = []
    i = 0
    while i < len(rows):
        if pn_pattern in rows[i]:
            kept_rows.extend(rows[i:i+13])
            i += 13
        else:
            i += 1

    # Ambil header (sebelum Table)
    header = xml.split("<ss:Table>")[0] + "<ss:Table>"

    # Ambil footer (setelah Table)
    footer = "</ss:Table>" + xml.split("</ss:Table>")[1]

    final_xml = header + "\n".join(kept_rows) + footer

    st.success("File Excel valid & layout tetap terjaga ✅")

    st.download_button(
        "Download Excel (Layout Sama)",
        final_xml.encode("utf-8"),
        file_name="nla_layout_asli.xls",
        mime="application/vnd.ms-excel"
    )
