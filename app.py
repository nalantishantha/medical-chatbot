from flask import Flask, render_template, jsonify, request, session
import uuid
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
from src.prompt import *
import os
import glob
import json
import logging
from langchain_community.chat_message_histories import FileChatMessageHistory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Get the absolute path to the frontend folder
# In Docker: /app/app.py and /app/frontend/
# Locally: medical-chatbot/app.py and ../frontend/
base_dir = os.path.dirname(os.path.abspath(__file__))

# Try Docker path first
frontend_folder = os.path.join(base_dir, 'frontend')
if not os.path.exists(frontend_folder):
    # Try local development path
    frontend_folder = os.path.join(os.path.dirname(base_dir), 'frontend')

logging.info(f"Frontend folder: {frontend_folder}")
logging.info(f"Frontend exists: {os.path.exists(frontend_folder)}")
if os.path.exists(frontend_folder):
    logging.info(f"Frontend contents: {os.listdir(frontend_folder)}")

app = Flask(__name__, 
            template_folder=frontend_folder,
            static_folder=frontend_folder,
            static_url_path='')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))


load_dotenv()




embeddings = download_hugging_face_embeddings()

index_name = os.environ.get("PINECONE_INDEX_NAME", "medical-chatbot")
# Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)




retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})

chatModel = ChatOpenAI(model="gpt-4o")

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    chatModel, retriever, contextualize_q_prompt
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(chatModel, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

CHAT_DIR = os.path.join(base_dir, "chat_histories")
os.makedirs(CHAT_DIR, exist_ok=True)

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return FileChatMessageHistory(os.path.join(CHAT_DIR, f"{session_id}.json"))

conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)



@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template('chat.html')



@app.route("/get", methods=["GET", "POST"])
def chat():
    session_id = session.get("session_id", "default_session")
    msg = request.form["msg"]
    logging.info(f"User message: {msg}")
    response = conversational_rag_chain.invoke(
        {"input": msg},
        config={"configurable": {"session_id": session_id}}
    )
    logging.info(f"Response : {response['answer']}")
    return str(response["answer"])

@app.route("/clear", methods=["POST"])
def clear_chat():
    session_id = session.get("session_id")
    if session_id:
        get_session_history(session_id).clear()
    return jsonify({"status": "success"})


@app.route("/sessions", methods=["GET"])
def get_sessions():
    sessions = []
    for file_path in glob.glob(os.path.join(CHAT_DIR, "*.json")):
        session_id = os.path.basename(file_path).replace(".json", "")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = "New Chat"
                for msg in data:
                    if msg.get("type") == "human":
                        content = msg.get("data", {}).get("content", "New Chat")
                        title = (content[:30] + '...') if len(content) > 30 else content
                        break
                mtime = os.path.getmtime(file_path)
                sessions.append({"id": session_id, "title": title, "mtime": mtime})
        except Exception:
            pass
    sessions.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify(sessions)

@app.route("/session/new", methods=["POST"])
def new_session():
    session["session_id"] = str(uuid.uuid4())
    return jsonify({"status": "success", "session_id": session["session_id"]})

@app.route("/session/switch", methods=["POST"])
def switch_session():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400
    session_id = data.get("session_id")
    if session_id:
        session["session_id"] = session_id
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route("/history", methods=["GET"])
def get_history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify([])
    
    file_path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    return jsonify([])


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)