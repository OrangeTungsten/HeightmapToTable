import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import io

# ─────────────────────────────────────────────
#  LANGUAGE PACK
# ─────────────────────────────────────────────
LANG = {
    "en": {
        "page_title":       "Heightmap to XYZ",
        "title":            "🗺️ Heightmap to XYZ Table",
        "description":      "Upload a grayscale image to generate 3D coordinates.",
        "file_uploader":    "Choose an image (PNG, JPG)",
        "grid_x":           "Number of points X",
        "grid_y":           "Number of points Y",
        "z_min":            "Z minimum",
        "z_max":            "Z maximum",
        "z_warning":        "⚠️ Warning: Z minimum must be less than Z maximum!",
        "caption":          "Original Heightmap",
        "btn_generate":     "Generate table",
        "spinner":          "Processing data...",
        "success":          "✅ Table generated with {total:,} rows ({gx} × {gy}).",
        "preview_info":     "Showing first {limit:,} of {total:,} rows.",
        "btn_csv":          "⬇️ Download CSV",
        "btn_excel":        "⬇️ Download Excel",
        "excel_warning":    "⚠️ Excel export unavailable. Install xlsxwriter: `pip install xlsxwriter`",
        "lang_button":      "🇷🇸 🌐",
        "start_from_zero":  "Start X and Y from 0",
    },

    "sr": {
        "page_title":       "Heightmap u XYZ",
        "title":            "🗺️ Heightmap u XYZ Tabelu",
        "description":      "Uploaduj crno-belu sliku da bi generisao 3D koordinate.",
        "file_uploader":    "Izaberi sliku (PNG, JPG)",
        "grid_x":           "Broj tačaka po X",
        "grid_y":           "Broj tačaka po Y",
        "z_min":            "Z minimalno",
        "z_max":            "Z maksimalno",
        "z_warning":        "⚠️ Upozorenje: Z minimalno mora biti manje od Z maksimalnog!",
        "caption":          "Originalni Heightmap",
        "btn_generate":     "Generiši tabelu",
        "spinner":          "Obrađujem podatke...",
        "success":          "✅ Generisana tabela sa {total:,} redova ({gx} × {gy}).",
        "preview_info":     "Prikazano prvih {limit:,} od {total:,} redova.",
        "btn_csv":          "⬇️ Preuzmi CSV tabelu",
        "btn_excel":        "⬇️ Preuzmi Excel tabelu",
        "excel_warning":    "⚠️ Excel export nije dostupan. Instalirajte xlsxwriter: `pip install xlsxwriter`",
        "lang_button":      "🇬🇧 🌐",
        "start_from_zero":  "Počni X i Y od 0",
    },
}

# ─────────────────────────────────────────────
#  SESSION STATE – default is englesh
# ─────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(key, **kwargs):
    # """Vraća string za trenutni jezik, sa opcionim format parametrima."""
    text = LANG[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text

# ─────────────────────────────────────────────
#  CORE
# ─────────────────────────────────────────────
def process_heightmap(image_file, grid_x, grid_y, z_min, z_max, z_decimals=4, start_from_zero=True):
    img = Image.open(image_file).convert('L')
    img = img.resize((grid_x, grid_y), resample=Image.Resampling.LANCZOS)

    z_values = np.array(img).astype(float)
    z_mapped = z_min + (z_values / 255.0) * (z_max - z_min)

    x_coords = np.arange(grid_x)
    y_coords = np.arange(grid_y)
    xv, yv = np.meshgrid(x_coords, y_coords, indexing='ij')

    if start_from_zero == True:
        offset = 0 
    else:
        offset = 1

    z_final = np.round(z_mapped.T.flatten(order='C'), z_decimals)
    x_final = xv.flatten(order='C') + offset
    y_final = yv.flatten(order='C') + offset

    return pd.DataFrame({'X': x_final, 'Y': y_final, 'Z': z_final})


# ─────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────
st.set_page_config(page_title=t("page_title"), layout="centered")

# Language
col_title, col_lang = st.columns([5, 1])
with col_title:
    st.title(t("title"))
with col_lang:
    st.write("")  # vertikalni razmak
    if st.button(t("lang_button"), use_container_width=True):
        st.session_state.lang = "sr" if st.session_state.lang == "en" else "en"
        st.rerun()

st.write(t("description"))

uploaded_file = st.file_uploader(t("file_uploader"), type=["png", "jpg", "jpeg"])

col1, col2 = st.columns(2)
with col1:
    grid_x = st.number_input(t("grid_x"), min_value=2, value=10)
    z_min  = st.number_input(t("z_min"), value=0.0)
with col2:
    grid_y = st.number_input(t("grid_y"), min_value=2, value=10)
    z_max  = st.number_input(t("z_max"), value=10.0)

if z_min >= z_max:
    st.warning(t("z_warning"))
    
start_from_zero = st.checkbox(t("start_from_zero"), value=True)

if uploaded_file is not None:

    if st.button(t("btn_generate"), disabled=(z_min >= z_max)):
        with st.spinner(t("spinner")):
            uploaded_file.seek(0)
            df_result = process_heightmap(uploaded_file, grid_x, grid_y, z_min, z_max, start_from_zero=start_from_zero)

            total_rows = len(df_result)
            st.success(t("success", total=total_rows, gx=grid_x, gy=grid_y))

            PREVIEW_LIMIT = 500
            if total_rows > PREVIEW_LIMIT:
                st.info(t("preview_info", limit=PREVIEW_LIMIT, total=total_rows))
                st.dataframe(df_result.head(PREVIEW_LIMIT))
            else:
                st.dataframe(df_result)

            csv = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=t("btn_csv"),
                data=csv,
                file_name="heightmap_coords.csv",
                mime="text/csv",
            )

            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_result.to_excel(writer, index=False, sheet_name='Coordinates')
                st.download_button(
                    label=t("btn_excel"),
                    data=output.getvalue(),
                    file_name="heightmap_coords.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except ImportError:
                st.warning(t("excel_warning"))
    
    uploaded_file.seek(0)
    st.image(uploaded_file, caption=t("caption"), use_container_width=True)