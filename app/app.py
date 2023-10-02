import os, sys
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO
from importlib import import_module
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import whisper
from utils import MODEL_DIRECTORY

transcriber = whisper.load_model("medium", download_root=MODEL_DIRECTORY)

ACTIVE_AGENTS = ["lex_chatgpt"]#, "lex_llama"]
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

loaded_agents = {}
for agent in ACTIVE_AGENTS:
    module = import_module(f"agent.{agent}")
    loaded_agents[agent] = module.chat_llm_chain

current_agent_name = os.getenv('DEFAULT_AGENT', ACTIVE_AGENTS[0])


# Carregando comandos
ACTIVE_COMMANDS = ["agent"]

loaded_commands = {}
for command in ACTIVE_COMMANDS:
    module = import_module(f"commands.{command}_command")
    loaded_commands[command] = module.run
    
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecret')  # Você precisa definir uma chave secreta para usar sessions
socketio = SocketIO(app,
                    cors_allowed_origins="*", 
                    ping_timeout=120)

@app.route('/')
def index():
    token = request.args.get('token')
    session['current_agent'] = current_agent_name  # Definindo o agente padrão
    if token != 'senhasecreta':
        return "Acesso não autorizado", 403
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@socketio.on('connect')
def initialize_session():
    pass

@socketio.on('select_agent')
def handle_agent_selection(agent_name):
    if agent_name in loaded_agents.keys():
        session['current_agent'] = agent_name

@socketio.on('message')
def handle_message(message):
    user_input = message.get('message')
    room = request.sid  # Obtém o ID da sessão atual
    current_agent_name = session.get('current_agent')
    socketio.emit('start_message', room=room)  # Envia para o room especificado
    current_agent = loaded_agents[current_agent_name]
        
    if not user_input:
        return None
    if user_input.startswith('!'):
        command, *args = user_input[1:].split()
        if command in loaded_commands:
            response = f"[{loaded_commands[command](args, session, ACTIVE_AGENTS, loaded_agents)}]"
            socketio.emit('message', {'result' : response}, room=room)  # Envia para o room especificado
            socketio.emit('end_message', room=room)  # Envia para o room especificado
            
        else:
            response = "Comando desconhecido. Por favor, tente novamente."
            socketio.emit('message', {'result' : response}, room=room)  # Envia para o room especificado
            socketio.emit('end_message', room=room)  # Envia para o room especificado
    else:
        socketio.start_background_task(message_task, current_agent_name, user_input, room)


@socketio.on('audioMessage')
def handle_audioMessage(audio_blob):
    room=request.sid
    socketio.start_background_task(audio_task, audio_blob, room)

def audio_task(audio_blob, room):    # Carregar modelo e transcrever o áudio
    # Salvar o blob de áudio como um arquivo temporário
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_blob)
    result = transcriber.transcribe("temp_audio.wav", verbose=True)
    socketio.emit('transcription', {'result': result['text']}, room=room)

def message_task(current_agent, user_input, room):    
    response = current_agent.run(human_input=user_input)
    socketio.emit('message', {'result' : response}, room=room)  # Envia para o room especificado
    socketio.emit('end_message', room=room)  # Envia para o room especificado

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)