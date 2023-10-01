import os
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO
from importlib import import_module
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ACTIVE_AGENTS = ["lex_chatgpt", "lex_llama"]

loaded_agents = {}
for agent in ACTIVE_AGENTS:
    module = import_module(f"agent.{agent}")
    loaded_agents[agent] = module.chat_llm_chain

current_agent_name = os.getenv('DEFAULT_AGENT', loaded_agents[ACTIVE_AGENTS[0]])


# Carregando comandos
ACTIVE_COMMANDS = ["agent"]

loaded_commands = {}
for command in ACTIVE_COMMANDS:
    module = import_module(f"commands.{command}_command")
    loaded_commands[command] = module.run
    
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecret')  # Você precisa definir uma chave secreta para usar sessions
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=120)

@app.route('/')
def index():
    token = request.args.get('token')
    if token != 'senhasecreta':
        return "Acesso não autorizado", 403
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@socketio.on('connect')
def initialize_session():
    session['current_agent'] = current_agent_name  # Definindo o agente padrão

@socketio.on('select_agent')
def handle_agent_selection(agent_name):
    if agent_name in loaded_agents.keys():
        session['current_agent'] = agent_name

@socketio.on('message')
def handle_message(message):
    user_input = message.get('message')
    room = request.sid  # Obtém o ID da sessão atual
    current_agent_name = session.get('current_agent')
    current_agent = loaded_agents[current_agent_name]
        
    if not user_input:
        return None

    socketio.emit('start_message')  # Envia para o room especificado

    if user_input.startswith('!'):
        command, *args = user_input[1:].split()
        if command in loaded_commands:
            response = f"[{loaded_commands[command](args, session, ACTIVE_AGENTS, loaded_agents)}]"
            
        else:
            response = "Comando desconhecido. Por favor, tente novamente."
    else:
        response = current_agent.run(human_input=user_input)

    socketio.emit('message', response, room=room)  # Envia para o room especificado
    socketio.emit('end_message', room=room)  # Envia para o room especificado

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)