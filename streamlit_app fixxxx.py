import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Excel Filter", layout="centered")

st.title("📊 Excel XNXX")

# ================= FILE UPLOAD =================
uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx"]
)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Gagal membaca file Excel: {e}")
        st.stop()

    # ================= NORMALIZE COLUMN NAMES =================
    df.columns = [
        unicodedata.normalize("NFKD", str(c))
        .encode("ascii", "ignore")
        .decode("utf-8")
        for c in df.columns
    ]

    st.success("File berhasil dibaca")

    # ================= COLUMN SELECTION =================
    selected_column = st.selectbox(
        "Pilih kolom",
        df.columns
    )

    # ================= CLEAN BLANK VALUES =================
    # Buang NaN, string kosong, dan spasi
    df_clean = df[
        df[selected_column]
        .notna() &
        (df[selected_column].astype(str).str.strip() != "")
    ]

    # ================= MULTI VALUE SELECTION =================
    unique_values = (
        df_clean[selected_column]
        .astype(str)
        .unique()
        .tolist()
    )

    excluded_values = st.multiselect(
        "Pilih nilai yang ingin DIHILANGKAN (blank otomatis tidak ditampilkan)",
        options=unique_values
    )

    # ================= APPLY EXCLUDE FILTER =================
    if excluded_values:
        filtered_df = df_clean[
            ~df_clean[selected_column].astype(str).isin(excluded_values)
        ]
    else:
        filtered_df = df_clean.copy()

    # ================= RESULT =================
    if filtered_df.empty:
        st.warning("Tidak ada data tersisa setelah filter.")
    else:
        st.subheader("Preview Data")
        st.write(f"Jumlah baris: **{len(filtered_df)}**")
        st.dataframe(filtered_df, use_container_width=True)

        # ================= DOWNLOAD =================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="⬇️ Download hasil (Exclude + No Blanks)",
            data=output,
            file_name="filtered_exclude_no_blanks.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


