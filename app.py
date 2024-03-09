import config
from utils import authenticate, upload_to_drive
import streamlit as st
from streamlit_extras.switch_page_button import switch_page


def main():
    # set page config
    st.set_page_config(page_title="SpeakingDoc", layout="wide", initial_sidebar_state="collapsed")
    st.title("SpeakingDoc")
    st.subheader("Chat with any document")

    # collapse side menu bar
    st.markdown(
    f"""<style>
        [data-testid="collapsedControl"] {{display:none}}
    </style>""",
    unsafe_allow_html=True,
    )

    # upload button
    upload_container = st.container()
    upload_container.markdown(
        """
        <style>
        div[data-testid="stFileUploader"] div:first-child {
            max-width: 300px;
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Upload PDF file
    uploaded_file = upload_container.file_uploader("Upload a PDF file", type=["pdf", "docx", "txt"])

    if uploaded_file:
        # Authenticate and upload to drive
        st.session_state['file_name'] = uploaded_file.name
        st.session_state['folder_id'] = config.FOLDER_ID
        st.session_state['file_id'] = None

        drive_service = authenticate()

        if drive_service:
            st.session_state['file_id'] = upload_to_drive(drive_service, 
                                                              uploaded_file.name, 
                                                              uploaded_file.getvalue(), 
                                                              config.FOLDER_ID) 
        else:
            st.write("Storage service authentication failed !!")

    if uploaded_file and st.session_state['file_id'] and st.button("Chat"):
        # Switch to chat.py page
        switch_page("chat")


if __name__ == "__main__":
    main()
