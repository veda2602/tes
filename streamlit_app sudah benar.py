import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(layout="wide")
st.title("📊 Excel Filter (XLS XML + XLSX Safe)")

uploaded_files = st.file_uploader(
    "Upload Excel (.xlsx atau .xls XML)",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

processed_outputs = []

if uploaded_files:

    for file in uploaded_files:

        # ===================== XML XLS =====================
        if file.name.endswith(".xls"):
            xml = file.read().decode("utf-8", errors="ignore")

            df = xml_xls_to_df(xml)

            df.columns = [
                unicodedata.normalize("NFKD", str(c))
                .encode("ascii", "ignore")
                .decode("utf-8")
                for c in df.columns
            ]

            # === FILTER P/N TIDAK KOSONG ===
            df = df[df["P/N"].notna() & (df["P/N"].astype(str).str.strip() != "")]

            # === AMBIL ASSY ===
            pn_assy = df.iloc[0]["P/N"]
            sn_assy = df.iloc[0]["S/N"]

            df.insert(0, "PN ASSY", pn_assy)
            df.insert(1, "SN ASSY", sn_assy)

            # === KEMBALIKAN XML DENGAN LAYOUT ===
            final_xml = filter_xml_rows(xml)

            processed_outputs.append(
                ("xls", file.name.replace(".xls", "_filtered.xls"), final_xml.encode())
            )

        # ===================== XLSX =====================
        else:
            df = pd.read_excel(file)

            df.columns = [
                unicodedata.normalize("NFKD", str(c))
                .encode("ascii", "ignore")
                .decode("utf-8")
                for c in df.columns
            ]

            df = df[df["P/N"].notna() & (df["P/N"].astype(str).str.strip() != "")]

            pn_assy = df.iloc[0]["P/N"]
            sn_assy = df.iloc[0]["S/N"]

            df.insert(0, "PN ASSY", pn_assy)
            df.insert(1, "SN ASSY", sn_assy)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)

            processed_outputs.append(
                ("xlsx", file.name.replace(".xlsx", "_filtered.xlsx"), output.getvalue())
            )

    st.success("Semua file berhasil diproses ✅")

    for ftype, fname, data in processed_outputs:
        mime = (
            "application/vnd.ms-excel"
            if ftype == "xls"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            f"⬇️ Download {fname}",
            data,
            file_name=fname,
            mime=mime
        )
