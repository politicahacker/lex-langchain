import os
from dotenv import load_dotenv
load_dotenv()
#LLM
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI

#Memory
from langchain.memory import ConversationBufferMemory

#Agents
from langchain.agents.conversational.base import ConversationalAgent #Uses GPT-3.5 Format
from langchain.agents.conversational_chat.base import ConversationalChatAgent #Uses ChatGPT Format
from langchain.agents import AgentExecutor

from agent.prompts import PREFIX, SUFFIX, FORMAT_INSTRUCTIONS
from tools.library import Library

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

#Define o LLM
llm = OpenAI()

#Define os prefixos e configurações
ai_prefix = "Lex"
human_prefix = "Usuário"

#Ferramentas
biblioteca = Library()
library_dir = os.getenv("LIBRARY_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library')
library_tools = biblioteca.generate_tools_for_library(library_dir)
tools = [] + library_tools

#Memória
memory = ConversationBufferMemory(ai_prefix=ai_prefix, human_prefix=human_prefix, memory_key="chat_history")

#Agente
agent_chain = AgentExecutor.from_agent_and_tools(
        agent=ConversationalAgent.from_llm_and_tools(llm=llm, tools=tools, prefix=PREFIX, format_instructions=FORMAT_INSTRUCTIONS, suffix=SUFFIX,
                                                     ai_prefix=ai_prefix, human_prefix=human_prefix),
        tools=library_tools,
        memory=memory,
        verbose=True,
        tags=['conversational-react-description']
    )

def main():
    while True:
        user_input = input("Usuário: ")
        if user_input.lower() == "exit":
            print("Encerrando o programa.")
            break

        response = agent_chain.run(user_input)
        print("Lex:", response)

if __name__ == "__main__":
    main()