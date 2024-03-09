import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.mistralai import MistralAI
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.core import Document
import config
from utils import fetch_from_drive, authenticate, string_to_generator, delete_file_from_drive


@st.cache_resource
def get_tokenizer_model():
    """
    Loads Mistral LLM and embedding model
    """
    system_prompt = """You are a helpful, respectful and honest assistant. Please ensure that your \
                responses are socially unbiased and positive in nature.
                If a question does not make any sense, explain why instead of answering something \
                not correct. If you don't know the answerto a question, please don't share false \
                information. Use the information and context from the document to answer the question.\
                Word limit of your response is 700 words."""

    # Define LLM
    Settings.llm = MistralAI(model=config.MISTRAL_MODEL_NAME, 
                             api_key=config.MISTRAL_API_KEY,
                             max_tokens= 1024, # 512 by default 
                             system_prompt=system_prompt)
    # Define embedding model
    Settings.embed_model = MistralAIEmbedding(model_name='mistral-embed', 
                                              api_key=config.MISTRAL_API_KEY)


# @st.cache_resource
def store_doc():
    """
    Fetch the document from drive, store and index it
    """
    # Authenticate and fetch from drive
    service = authenticate()
    if service:
        content = fetch_from_drive(service, st.session_state['file_id'])
    else:
        st.write("Storage service authentication failed !!")
        content = None
      
    if content:
        # Create a document from the fetched content and 
        document = Document(text=content) 
        # store it as vectorDB
        index = VectorStoreIndex.from_documents([document])
        return index
    else:
        return None


def run_query(user_input):
    """
    Run query on indexed document, return response
    """
    index = store_doc()
    if index:    
        query_engine = index.as_query_engine(similarity_top_k=2, streaming=True)
        response = query_engine.query(user_input)
        return response.response_gen
    else:
        return string_to_generator("Query did not run due to an error !!")


def main():
    # st.set_page_config(page_title="Chat with PDF", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
    f"""<style>
        [data-testid="collapsedControl"] {{display:none}}
    </style>""",
    unsafe_allow_html=True,
    )

    st.header(':green[Ask any doc related question]')

    # user prompt
    user_input = st.text_input("Type here:")
    
    # define button layout
    cols = st.columns([2, 3, 10, 1])
    with cols[0]:
        send = st.button("Send")
             
    with cols[1]:
        home = st.button("Back to home")

    # run query & stream response on pressing send
    if send:
        st.write("You:\n", user_input)
        st.write("Assistant:\n")
        st.write_stream(run_query(user_input))
    
    # delete current doc from drive and return to home page
    if home:
        if 'file_id' in st.session_state:
            delete_file_from_drive(st.session_state['file_id'])
        switch_page('app')



if __name__ == "__main__":
    st.set_page_config(page_title="Chat with PDF", layout="wide", initial_sidebar_state="collapsed")
    get_tokenizer_model()
    main()
