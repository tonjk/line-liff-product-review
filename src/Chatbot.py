from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
load_dotenv()
from langfuse.callback import CallbackHandler
from .RedisHistory.redis_chat_manager import ChatHistoryManager

langfuse_handler = CallbackHandler(public_key="pk-lf-7825de89-a8c6-4c24-9cbc-8954a1a438e7",
                                   secret_key="sk-lf-a9a2178b-9323-4ca1-947a-124968872130",
                                   host="https://us.cloud.langfuse.com")
# langfuse_handler = CallbackHandler(public_key=os.environ.get('LANGFUSE_PUBLIC_KEY'),
#                                    secret_key=os.environ.get('LANGFUSE_SECRET_KEY'),
#                                    host=os.environ.get('LANGFUSE_HOST'))

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=1, max_tokens=1024)

system_prompt = "You are helpful assistant that can chat with user in Thai. You love to talk with user about everything. Use 'ครับ' to respon politely. Respond in short and do not use BOLD text format."
prompt = ChatPromptTemplate.from_messages([("system", system_prompt),
                                           MessagesPlaceholder(variable_name="history"),
                                           ("human", "{input}")])
chain = prompt | llm | StrOutputParser()

# init chat manager
chat_history_manager = ChatHistoryManager()

def chat(session_id:str, user_name:str, user_input:str):
    user_input = user_input.strip()
    cnt_chat = chat_history_manager.cnt_chat_history(session_id)
    if user_input.lower() == '#reset' or cnt_chat > 40:
        # cnt_chat = chat_history_manager.cnt_chat_history(session_id)
        # print(cnt_chat)
        chat_history_manager.clear_chat_history(session_id)
        if cnt_chat > 20:
            response = "เมื่อสักครู่เราคุยกันเยอะเหมือนกันนะครับเนี่ย แต่เราจะเริ่มแชทกันใหม่นะครับ"
        else:
            response = "Let's start a new chat kub. ^_^"
        return response
    else:
        chat_history_manager.save_message(user_id=session_id, role='user', message=user_input)
        response = chain.invoke({"input": user_input,
                                "history": chat_history_manager.get_recent_chat_history(session_id)},
                                config={"callbacks": [langfuse_handler],
                                        "configurable": {"session_id": session_id,
                                                         "langfuse_session_id": session_id,
                                                         "langfuse_user_id": user_name,}})
        chat_history_manager.save_message(user_id=session_id, role='assistant', message=response)

        return response

if __name__=="__main__":
    # print(chat(session_id='123', user_input='hello'))
    while True:
        user_input = input("User: ")
        if user_input == 'exit':
            break
        print(chat(session_id='123', user_name='BotTest', user_input=user_input))