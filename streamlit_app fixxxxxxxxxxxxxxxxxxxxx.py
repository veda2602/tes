import streamlit as st
import re

st.set_page_config(layout="wide")
st.title("NLA Excel Extractor + Filter (Safe XML)")

uploaded_file = st.file_uploader(
    "Upload file Excel XML (.xls)",
    type=["xls"]
)

# ================= UTIL FUNCTION =================
def get_cell_value(row_xml, cell_index):
    cells = re.findall(
        r"<ss:Data[^>]*>(.*?)</ss:Data>",
        row_xml,
        flags=re.DOTALL
    )
    if cell_index < len(cells):
        return re.sub("<.*?>", "", cells[cell_index]).strip()
    return ""

# ================= MAIN =================
if uploaded_file:
    xml = uploaded_file.read().decode("utf-8", errors="ignore")

    # Ambil semua Row utuh
    rows = re.findall(
        r"<ss:Row[^>]*>.*?</ss:Row>",
        xml,
        flags=re.DOTALL
    )

    pn_pattern = '<ss:Data ss:Type="String">P/N</ss:Data>'

    # ================= COLLECT FILTER OPTIONS =================
    filter_column_index = 2  # ⬅️ ganti jika mau filter kolom lain

    filter_values = []
    for r in rows:
        if pn_pattern in r:
            v = get_cell_value(r, filter_column_index)
            if v:
                filter_values.append(v)

    filter_values = sorted(set(filter_values))

    st.subheader("🔎 Filter Data")
    excluded_values = st.multiselect(
        "Pilih nilai yang ingin DIHILANGKAN",
        options=filter_values
    )

    # ================= FILTER ROWS =================
    kept_rows = []
    i = 0

    while i < len(rows):
        if pn_pattern in rows[i]:
            header_row = rows[i]
            filter_value = get_cell_value(header_row, filter_column_index)

            if filter_value not in excluded_values:
                kept_rows.extend(rows[i:i+13])

            i += 13
        else:
            i += 1

    # ================= REBUILD XML =================
    header = xml.split("<ss:Table>")[0] + "<ss:Table>"
    footer = "</ss:Table>" + xml.split("</ss:Table>")[1]

    final_xml = header + "\n".join(kept_rows) + footer

    # ================= INFO =================
    st.success(f"✅ Data siap didownload ({len(kept_rows)//13} item)")

    # ================= DOWNLOAD =================
    st.download_button(
        "⬇️ Download Excel (Layout Tetap Sama)",
        final_xml.encode("utf-8"),
        file_name="nla_layout_filtered.xls",
        mime="application/vnd.ms-excel"
    )
