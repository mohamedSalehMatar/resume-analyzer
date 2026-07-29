import json
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx

try:
    from .services import analyze_resume
except ImportError:  # pragma: no cover - allows running as a script
    from services import analyze_resume

st.set_page_config(page_title="Resume Analyzer", page_icon="📄")
st.markdown("# Resume Analyzer")

if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = None
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown(
    """
    <style>
    .chat-container {max-width: 900px; margin: auto;}
    .message.user {background: #d6eaff; border-radius: 16px; padding: 12px 16px; margin: 8px 0; text-align: right;}
    .message.assistant {background: #f1f3f5; border-radius: 16px; padding: 12px 16px; margin: 8px 0; text-align: left;}
    .message .role {font-size: 0.85rem; color: #6b7280; margin-bottom: 6px;}
    .message pre {white-space: pre-wrap; word-wrap: break-word; margin: 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

tab_upload, tab_chat = st.tabs(["Upload PDF", "Chat"])

with tab_upload:
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Drag and drop a PDF file here or click to browse", type=["pdf"], accept_multiple_files=False)

    if uploaded_file is not None:
        if st.session_state.pdf_filename != uploaded_file.name:
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp_file.write(uploaded_file.getvalue())
            tmp_file.flush()
            tmp_file.close()
            st.session_state.pdf_path = tmp_file.name
            st.session_state.pdf_filename = uploaded_file.name
            st.session_state.pdf_uploaded = True
            st.session_state.chat_history = []

        st.success(f"Uploaded `{uploaded_file.name}` successfully.")
        st.write("PDF path:", st.session_state.pdf_path)

    if st.session_state.pdf_uploaded:
        st.info(f"Current uploaded file: **{st.session_state.pdf_filename}**")
        if st.button("Clear uploaded PDF"):
            st.session_state.pdf_path = None
            st.session_state.pdf_filename = None
            st.session_state.pdf_uploaded = False
            st.session_state.chat_history = []
    else:
        st.info("No PDF uploaded yet. Upload a file to enable the chat interface.")

with tab_chat:
    st.header("Chat about the uploaded PDF")
    if not st.session_state.pdf_uploaded:
        st.warning("Upload a PDF first in the Upload PDF tab.")
    else:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

        for message in st.session_state.chat_history:
            role = message["role"]
            text = message["text"]
            if role == "user":
                st.markdown(
                    f"<div class='message user'><div class='role'>You</div><pre>{text}</pre></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='message assistant'><div class='role'>Assistant</div><pre>{text}</pre></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

        user_question = st.text_area("Ask a question about the uploaded PDF", key="user_question", height=120)
        if st.button("Send", key="send_button"):
            if not user_question.strip():
                st.warning("Please type a question before sending.")
            else:
                st.session_state.chat_history.append({"role": "user", "text": user_question})
                with st.spinner("Getting answer from the notebook..."):
                    try:
                        answer = analyze_resume(pdf_path=st.session_state.pdf_path, user_input=user_question)
                        answer_text = json.dumps(answer.get("result", answer), indent=2)
                        st.session_state.chat_history.append({"role": "assistant", "text": answer_text})
                    except Exception as exc:
                        st.session_state.chat_history.append({"role": "assistant", "text": f"Error: {exc}"})
                        st.error(str(exc))

if __name__ == "__main__":
    if get_script_run_ctx() is None:
        script_path = Path(__file__).resolve()
        command = [sys.executable, "-m", "streamlit", "run", str(script_path), "--server.headless", "true"]
        raise SystemExit(subprocess.call(command))

