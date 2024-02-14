import os
from flask import session


#LLM
from langchain_community.llms import OpenAI
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder

#Memory
from langchain_community.chat_message_histories.firestore import (
    FirestoreChatMessageHistory,
)
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

#CallBack
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

#Prompts
from .prompts import SYS_PROMPT
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

#Define o LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYS_PROMPT), # The persistent system prompt
    MessagesPlaceholder(variable_name="history"), # Where the memory will be stored.
    HumanMessagePromptTemplate.from_template("{human_input}"), # Where the human input will injected
])


# TODO: use different memory_key for each session

import firebase_admin
from firebase_admin import credentials, firestore
script_dir = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(f"{script_dir}/../keys/politicalai-lex.json")
app = firebase_admin.initialize_app(cred)
client = firestore.client(app=app)

message_history = FirestoreChatMessageHistory(
    collection_name="lex-history",
    session_id="default",
    user_id="no-user-defined",
    firestore_client=client,
)



# memory = ConversationBufferMemory(memory_key=f"chat_history", chat_memory=message_history, return_messages=True)
memory = ConversationBufferMemory(chat_memory=message_history, return_messages=True)

print(f"MESSAGES: {memory}")
## memory = ConversationBufferMemory(memory_key=f"chat_history", return_messages=True)



llm = ChatOpenAI(streaming=True, callbacks=[StreamingStdOutCallbackHandler()])

chat_llm_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True,
    memory=memory,
)