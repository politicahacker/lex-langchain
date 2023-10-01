# commands/agent_command.py

def run(args, session, ACTIVE_AGENTS, loaded_agents):
    if args:
        subcommand = args[0]
        if subcommand == "list":
            return f"Agente disponíveis: {', '.join(ACTIVE_AGENTS)}"
        elif subcommand == "set":
            new_agent = args[1] if len(args) > 1 else None
            if new_agent in loaded_agents.keys():
                session['current_agent'] = new_agent
                return f"Agente configurado para {new_agent}"
            else:
                return "Agente invalido."
    else:
        current_agent = session.get('current_agent', ACTIVE_AGENTS[0])
        return f"O agente atual é {current_agent}"
