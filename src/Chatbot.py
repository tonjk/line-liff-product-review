from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
# import time, json, redis, os
from dotenv import load_dotenv
load_dotenv()

from src.RedisHistory.redis_chat_manager import ChatHistoryManager

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1, max_tokens=1024)

system_prompt = "You are helpful assistant that can chat with user in Thai. You love to talk with user about everything. Use 'ครับ' to respon politely."
prompt = ChatPromptTemplate.from_messages([("system", system_prompt),
                                           MessagesPlaceholder(variable_name="history"),
                                           ("human", "{input}")])
chain = prompt | llm | StrOutputParser()

# init chat manager
chat_history_manager = ChatHistoryManager()

def chat(session_id:str, user_input:str):
    user_input = user_input.strip()
    chat_history_manager.save_message(user_id=session_id, role='user', message=user_input)
    response = chain.invoke({"input": user_input,
                             "history": chat_history_manager.get_recent_chat_history(session_id)},
                            config={"configurable": {"session_id": session_id}})
    chat_history_manager.save_message(user_id=session_id, role='assistant', message=response)

    return response

if __name__=="__main__":
    print(chat(session_id='123', user_input='hello'))