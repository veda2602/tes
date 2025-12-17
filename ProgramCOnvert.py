import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="NLA Parser", layout="wide")
st.title("NLA Assembly Data Processor")

uploaded_file = st.file_uploader(
    "Upload file dw_assembly_detail_hdr (.xls)",
    type=["xls", "txt"]
)

if uploaded_file is not None:
    try:
        # Read file (tab-separated XML-like xls)
        data = pd.read_csv(uploaded_file, sep="\t", header=0)

        # Rename first column
        data = data.rename(
            columns={data.columns[0]: "col"}
        )

        pattern = '<ss:Cell><ss:Data ss:Type="String">P/N</ss:Data></ss:Cell>'

        # Find rows containing P/N
        match_indices = data.index[
            data["col"].astype(str).str.contains(pattern, regex=False, na=False)
        ]

        rows_to_keep = set()
        for idx in match_indices:
            rows_to_keep.update(range(idx, idx + 13))

        rows_to_keep = sorted(i for i in rows_to_keep if i < len(data))

        result = data.loc[rows_to_keep, "col"]

        # Clean XML tags
        result = (
            result
            .str.replace(r"<ss:Cell>", "", regex=True)
            .str.replace(r'<ss:Data ss:Type="String">', "", regex=True)
            .str.replace(r"</ss:Data>", "", regex=True)
            .str.replace(r"</ss:Cell>", "", regex=True)
            .str.replace(r"</ss:Row>", "", regex=True)
            .str.strip()
        )

        result = result.replace(r"^\s*$", np.nan, regex=True)
        result = result.dropna().reset_index(drop=True)

        st.success("Data berhasil diproses ✅")

        st.subheader("Hasil Ekstraksi")
        st.dataframe(result.to_frame(name="Value"), use_container_width=True)

        # Optional: download result
        csv = result.to_frame(name="Value").to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download hasil (CSV)",
            csv,
            file_name="nla_result.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error("Terjadi error saat memproses file")
        st.exception(e)
else:
    st.info("Silakan upload file terlebih dahulu")
