
import streamlit as st
import os
import sys
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.tools import Tool
from serpapi import GoogleSearch

# Ensure the directory containing secret_key.py is in the Python path
if '/content' not in sys.path:
    sys.path.insert(0, '/content')

# Load API keys
try:
    from secret_key import openapi_key, serpapi_key
    os.environ['OPENAI_API_KEY'] = openapi_key
    os.environ['SERPAPI_API_KEY'] = serpapi_key
    # print("API keys loaded successfully.") # For debugging, do not expose in final app
except ImportError:
    st.error("Error: Could not import 'secret_key.py'. Please ensure it exists in /content with 'openapi_key' and 'serpapi_key'.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred while loading API keys: {e}")
    st.stop()

# Streamlit page configuration
st.set_page_config(layout="wide", page_title="We the Chef Chatbot")

# 'We the Chef' logo suitable for mobile
st.image("https://www.wethechefs.in/wp-content/uploads/2020/07/We-The-Chefs-Logo.png", width="content") # Corrected deprecated parameter

st.title("We the Chef Chatbot")

st.write("Welcome to the We the Chef Chatbot! Ask me anything about recipes, ingredients, or chefs.")

# Initialize LLM and Memory (only once per session)
if "conversation" not in st.session_state:
    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    memory = ConversationBufferWindowMemory(k=4) # Store last 2 turns (human + AI response)
    st.session_state.conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
    st.session_state.messages = []

# Define SerpApi Google Search Tool (re-define if not in global scope or session state)
def serpapi_google_search(query: str) -> str:
    """Performs a Google Search using SerpApi and returns a relevant snippet."""
    params = {
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "no_cache": True # Ensure fresh results
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    if "answer_box" in results and "answer" in results["answer_box"]:
        return results["answer_box"]["answer"]
    elif "organic_results" in results and len(results["organic_results"]) > 0:
        return results["organic_results"][0]["snippet"]
    else:
        return "No relevant search results found."

# Create a Tool object for Google Search using the custom function
google_search_tool = Tool(
    name="Google Search",
    description="A wrapper around Google Search. Useful for when you need to answer questions about current events. Input should be a search query.",
    func=serpapi_google_search,
)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # Always perform a targeted Google search on wethechefs.in, then use LLM to process results
        search_query = f"site:wethechefs.in {prompt}"
        st.markdown("*(Thinking: Searching on We the Chef website...)*")
        search_result = google_search_tool.run(search_query) # Corrected typo: gogle_search_tool -> google_search_tool

        final_prompt = f"Given the user's question: '{prompt}' and the search result: '{search_result}', provide a concise answer."
        response = st.session_state.conversation.llm.invoke(final_prompt).content

        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})


# Instructions to run the Streamlit app from Colab
st.sidebar.markdown("### How to run this app")
st.sidebar.markdown("1. Run the Python file in your terminal: `streamlit run app.py`")
st.sidebar.markdown("2. If running in Colab, you'll need to use `!streamlit run app.py & npx localtunnel --port 8501` to expose the app.")
st.sidebar.markdown("3. Click the external URL provided by localtunnel.")
