import os
from dotenv import load_dotenv
load_dotenv()
#LLM
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder

#Memory
from langchain.memory import ConversationBufferMemory

from langchain.chains import LLMChain

#Agents
from langchain.agents.conversational.base import ConversationalAgent #Uses GPT-3.5 Format
from langchain.agents.conversational_chat.base import ConversationalChatAgent #Uses ChatGPT Format
from langchain.agents import AgentExecutor

from agent.prompts import PREFIX, SUFFIX, FORMAT_INSTRUCTIONS
from langchain.prompts import PromptTemplate
from tools.library import Library


from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

OPENAI_API_KEY = os.getenv('OPENAI_APIKEY')

#Define o LLM
llm = OpenAI()
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

#Define os prefixos e configurações
ai_prefix = "Lex"
human_prefix = "Usuário"

#Ferramentas
#biblioteca = Library()
#library_dir = os.getenv("LIBRARY_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library')
#library_tools = biblioteca.generate_tools_for_library(library_dir)
#tools = []# + library_tools

#Memória
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a chatbot having a conversation with a human."), # The persistent system prompt
    MessagesPlaceholder(variable_name="chat_history"), # Where the memory will be stored.
    HumanMessagePromptTemplate.from_template("{human_input}"), # Where the human input will injected
])
    
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

llm = ChatOpenAI(streaming=True, callbacks=[StreamingStdOutCallbackHandler()])

chat_llm_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True,
    memory=memory,
)



from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    token = request.args.get('token')
    if token != 'senhasecreta':
        return "Acesso não autorizado", 403
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@socketio.on('message')
def handle_message(message):
    user_input = message.get('message')
    room = request.sid  # Obtém o ID da sessão atual
    
    if not user_input:
        socketio.emit('message', {'resposta': 'mensagem não fornecida'}, room=room)  # Envia para o room especificado
        return

    response = chat_llm_chain.predict(human_input=user_input)
    socketio.emit('start_message', room=room)  # Envia para o room especificado
    for chunk in response:
        socketio.emit('message', chunk, room=room)  # Envia para o room especificado
    socketio.emit('end_message', room=room)  # Envia para o room especificado

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)