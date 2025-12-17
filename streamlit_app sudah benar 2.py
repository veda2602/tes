import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Excel Filter", layout="centered")
st.title("📊 Excel Filter (Multi File – Single Filter)")

# ================= FILE UPLOAD =================
uploaded_files = st.file_uploader(
    "Upload satu atau lebih file Excel (format harus sama)",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:

    # ================= READ FIRST FILE (REFERENCE) =================
    df_ref = pd.read_excel(uploaded_files[0])
    df_ref.columns = [
        unicodedata.normalize("NFKD", str(c))
        .encode("ascii", "ignore")
        .decode("utf-8")
        for c in df_ref.columns
    ]

    # ================= FILTER SETUP =================
    selected_column = st.selectbox(
        "Pilih kolom filter (berlaku untuk semua file)",
        df_ref.columns
    )

    df_ref_clean = df_ref[
        df_ref[selected_column].notna() &
        (df_ref[selected_column].astype(str).str.strip() != "")
    ]

    unique_values = df_ref_clean[selected_column].astype(str).unique().tolist()

    excluded_values = st.multiselect(
        "Pilih nilai yang ingin DIHILANGKAN",
        options=unique_values
    )

    processed_dfs = []

    # ================= PROCESS FILES =================
    for uploaded_file in uploaded_files:

        df = pd.read_excel(uploaded_file)
        df.columns = [
            unicodedata.normalize("NFKD", str(c))
            .encode("ascii", "ignore")
            .decode("utf-8")
            for c in df.columns
        ]

        # APPLY FILTER
        df_clean = df[
            df[selected_column].notna() &
            (df[selected_column].astype(str).str.strip() != "")
        ]

        if excluded_values:
            df_filtered = df_clean[
                ~df_clean[selected_column].astype(str).isin(excluded_values)
            ]
        else:
            df_filtered = df_clean.copy()

        # ================= DROP KOLOM =================
        export_df = df_filtered.copy()
        drop_indexes = [0, 1, 3, 6, 7, 8, 9, 10, 11, 14, 15]
        drop_indexes = [i for i in drop_indexes if i < len(export_df.columns)]
        export_df = export_df.drop(export_df.columns[drop_indexes], axis=1)

        # ================= RENAME KOLOM =================
        export_df.columns = [
            "P/N",
            "S/N",
            "P/N Description",
            "Batch",
            *export_df.columns[4:]
        ][:len(export_df.columns)]

        # ================= FIX BATCH =================
        if export_df.shape[1] > 4:
            export_df["Batch"] = (
                export_df["Batch"]
                .replace(r"^\s*$", pd.NA, regex=True)
                .fillna(export_df.iloc[:, 4])
            )
            export_df = export_df.drop(export_df.columns[4], axis=1)

        # ================= AMBIL PN ASSY & SN ASSY (BENAR) =================
        pn_assy = ""
        sn_assy = ""

        if len(export_df) >= 2:
            pn_assy = export_df.loc[export_df.index[0], "P/N"]
            sn_assy = export_df.loc[export_df.index[0], "S/N"]

        # ================= INSERT KOLOM ASSY =================
        export_df.insert(0, "PN ASSY", pn_assy)
        export_df.insert(1, "SN ASSY", sn_assy)

        processed_dfs.append(export_df)

    # ================= GABUNG =================
    final_df = pd.concat(processed_dfs, ignore_index=True)

    # ================= HAPUS DUPLIKAT BATCH =================
    final_df = final_df.drop_duplicates(subset=["Batch"], keep="first")

    # ================= PREVIEW =================
    st.subheader("📄 Preview Data Final")
    st.dataframe(final_df, use_container_width=True)

    # ================= DOWNLOAD =================
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        "⬇️ Download hasil akhir",
        data=output,
        file_name="filtered_combined_with_assy.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

