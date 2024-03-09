import config
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io
import PyPDF2
import zipfile
import streamlit as st
import re


def authenticate():
    """
    Authenticate using service account credentials.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            config.SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)
    except:
        return None
     

def upload_to_drive(drive_service, file_name, file_content, folder_id):
    """
    Upload the file to drive using service account
    """
    try:
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        docType = file_name.split(".")[-1]

        mime_type = {'pdf': 'application/pdf', 'txt': 'text/plain', 
                        'docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}

        if docType not in mime_type:
            raise st.write(f"""Document of type "{docType}" is not supported!""")

        media = MediaIoBaseUpload(io.BytesIO(file_content), 
                                mimetype= mime_type[docType], 
                                resumable=True)

        file = drive_service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        st.write(f"""Your file "{file_name}" is uploaded successfully!""")
        return file.get('id')
    except:
        st.write("Failed to upload document to cloud !!")
        return None


def fetch_from_drive(drive_service, file_id):
    """
    Fetch document as pdf, extract text and return as string
    """
    # Fetch the PDF file metadata
    try:
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        func_switcher = {'application/pdf': extract_text_from_pdf,
                         'text/plain': extract_text_from_txtfile,
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document': extract_text_from_docx}
        
        if file_metadata['mimeType'] not in func_switcher:
            raise st.write(f"""File of the type {file_metadata['mimeType']} is not supported""")
        
        content = drive_service.files().get_media(fileId=file_id).execute()
        text_content = func_switcher[file_metadata['mimeType']](content)
        
        return text_content
    except:
        st.write("Failed to fetch the file !!")
        return None


def extract_text_from_pdf(pdf_content):
    """
    Converts pdf to string 
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = PyPDF2.PdfReader(pdf_file)

        text_content = ""
        for page_num in range(len(reader.pages)):
            text_content += reader.pages[page_num].extract_text()

        return text_content
    except:
        st.write("Error file extracting text from document !!")
        return None


def extract_text_from_txtfile(content):
    """
    Converts txt to string
    """
    return content.decode('utf-8')


def extract_text_from_docx(content):
    """
    Converts docx to string
    """
    content_bytes = io.BytesIO(content)
    docx_text = ""
    with zipfile.ZipFile(content_bytes) as docx_zip:
        with docx_zip.open('word/document.xml') as docx_xml:
            docx_text = docx_xml.read().decode()
    
    cleaned_text = re.sub(r'<.*?>', '', docx_text)
    return cleaned_text


def delete_file_from_drive(file_id):
    """
    Delete file from drive, given file ID
    """
    drive_service = authenticate()
    if drive_service:
        drive_service.files().delete(fileId=file_id).execute()
    else:
        st.write("Failed to delete file from server")


def string_to_generator(input_string):
    """
    Convert string to generator/iterable for streaming text
    """
    for char in input_string:
        yield char
