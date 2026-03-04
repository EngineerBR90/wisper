import streamlit as st
import whisper
import os
import datetime
import tempfile

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Transcritor de WhatsApp", page_icon="🎙️")

st.title("🎙️ Transcritor de Áudio (.opus)")
st.write("Suba seus arquivos e extraia o texto com a data automática.")

# ---------------------------------------------------------------------------
# Instalação e aviso sobre FFmpeg
# ---------------------------------------------------------------------------
with st.expander("⚙️ Pré-requisitos — leia antes de usar"):
    st.markdown("""
    **1. FFmpeg (obrigatório no sistema operacional)**

    O `ffmpeg-python` instalado via pip é apenas um wrapper Python.
    O binário do FFmpeg precisa estar instalado separadamente:

    - **Windows:** `winget install ffmpeg` (ou baixe em https://ffmpeg.org/download.html)
    - **Linux:** `sudo apt install ffmpeg`
    - **macOS:** `brew install ffmpeg`

    Sem isso, a transcrição vai falhar.

    **2. Dependências Python**
    ```
    pip install streamlit openai-whisper ffmpeg-python
    ```
    """)

# ---------------------------------------------------------------------------
# Modelo Whisper
# ---------------------------------------------------------------------------
MODEL_OPTIONS = {
    "base  — rápido, qualidade baixa": "base",
    "small — equilibrado (recomendado)": "small",
    "medium — melhor qualidade, mais lento": "medium",
}

model_label = st.selectbox(
    "Escolha o modelo Whisper:",
    options=list(MODEL_OPTIONS.keys()),
    index=1,  # small como padrão
)
model_name = MODEL_OPTIONS[model_label]

@st.cache_resource
def load_model(name: str):
    return whisper.load_model(name)

model = load_model(model_name)

# ---------------------------------------------------------------------------
# Extração de data a partir do nome do arquivo
# Suporta prefixos comuns do WhatsApp: PTT-, IMG-, AUD-, VID-, etc.
# Padrão esperado: PREFIXO-AAAAMMDD-WAxxx.opus
# ---------------------------------------------------------------------------
def extrair_data(filename: str) -> str:
    try:
        partes = filename.split("-")
        # A parte da data é sempre o segundo segmento (índice 1)
        date_str = partes[1]
        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
        return date_obj.strftime("%d/%m/%Y")
    except Exception:
        return "Data desconhecida"

# ---------------------------------------------------------------------------
# Upload de múltiplos arquivos
# ---------------------------------------------------------------------------
uploaded_files = st.file_uploader(
    "Escolha os arquivos .opus",
    type=["opus"],
    accept_multiple_files=True,
)

if uploaded_files:
    # Ordena pelos nomes para garantir sequência WA001, WA002, etc.
    uploaded_files = sorted(uploaded_files, key=lambda f: f.name)

    if st.button("▶️ Iniciar Transcrição"):
        transcricoes = []

        for uploaded_file in uploaded_files:
            with st.spinner(f"Transcrevendo {uploaded_file.name}..."):
                # Salva em arquivo temporário (Whisper exige caminho real)
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".opus"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    # Transcrição com idioma forçado para português
                    result = model.transcribe(tmp_path, language="pt")
                    texto = result["text"].strip()

                except Exception as e:
                    st.error(f"Erro ao transcrever {uploaded_file.name}: {e}")
                    texto = "[erro na transcrição]"

                finally:
                    # Garante remoção do temporário mesmo em caso de exceção
                    if tmp_path and os.path.exists(tmp_path):
                        os.remove(tmp_path)

            data_envio = extrair_data(uploaded_file.name)

            # Bloco de texto com cabeçalho
            bloco = f"[{data_envio}] {uploaded_file.name}\n{texto}"
            transcricoes.append(bloco)

            # Exibição na tela
            st.markdown(f"### 📄 {uploaded_file.name}")
            st.info(f"**Data extraída:** {data_envio}")
            st.write(texto)
            st.divider()

        # -----------------------------------------------------------------------
        # Exportar todas as transcrições em um único .txt
        # -----------------------------------------------------------------------
        if transcricoes:
            texto_completo = "\n\n" + ("—" * 60) + "\n\n".join(transcricoes)
            st.download_button(
                label="⬇️ Baixar todas as transcrições (.txt)",
                data=texto_completo.encode("utf-8"),
                file_name="transcricoes.txt",
                mime="text/plain",
            )

        st.success("✅ Tudo pronto!")