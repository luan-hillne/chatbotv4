import os, re
import json
from pathlib import Path
import pandas as pd
import random
from config_app.config import get_config
from langchain.schema import messages_to_dict
import requests
from rag_architecture.retrieval import search_db
from rag_architecture.few_shot_sentence import classify_intent, find_closest_match, correct_spelling_input
from rag_architecture.generate import initialize_chat_conversation
from config_app.enum import Variable
from typing import Dict, Any 
import logging, time, datetime

random_number = random.randint(0, 4)
config_app = get_config()
enum = Variable()
rasa_host = config_app['parameter']['rasa_url']
data_private = config_app['parameter']['data_private']
df = pd.read_excel(data_private)
current_time = datetime.datetime.now() # current time

USER_STORAGE_DIR = 'logs/user_storage/'
os.makedirs(USER_STORAGE_DIR, exist_ok=True)

def load_user_data(user_id: str) -> dict:
    user_dir = os.path.join(USER_STORAGE_DIR, f'{user_id}')
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, 'session.json')
    data = {}
    if not os.path.exists(file_path):
        data['save_outtext'] = ''

    if os.path.exists(file_path):
        with open(file_path,'r', encoding='utf-8') as file:

            data = json.load(file)

    return  data['save_outtext']

def set_save_outtext(user_id: str, new_value: str) -> None:
    user_dir = os.path.join(USER_STORAGE_DIR, f'{user_id}')
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, 'session.json')
    data = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    data['save_outtext'] = new_value

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def handle_conversation(ok, query_text, response_elastic, session_id):
    print('query text in chat', query_text)
    if ok == 0:
        logging.info("==Conversation2==")
        print('= =  Conversation2  = =')
        initialize_func = initialize_chat_conversation
    else:
        logging.info("==Conversation==")
        print('= =  Conversation  = =')
        initialize_func = initialize_chat_conversation
    result = initialize_func(query_text, response_elastic, session_id)
    return result

def predict_rasa_llm(input_text, session_id, namebot, user_id, type=enum.TYPE_RASA):
    user_id = str(user_id)
    session_id = str(session_id)
    # current_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    print("----------------NEW_SESSION--------------")
    print("user_id  = ", user_id)
    print("input_text  = ", input_text) 
    print("sesstion id  = ", session_id) 

    query_text = input_text
    results = {'terms': [], 'out_text': '', 'inventory_status': False, 'products': [], 'similarity_status': False, 'total_tokens': ''}
    
    if type == enum.TYPE_RASA:
        logging.info("=====rasa=====")
        print('======rasa======')
        # conversation = initialize_chat_conversation(conversation_messages_conv, conversation_messages_snippets, "")
        response = requests.post(rasa_host, json={"sender": "test", "message": query_text})
        print('response.json():',response.json())
        if len(response.json()) == 0:
            results['out_text'] = 'LLM_predict'
        elif response.json()[0].get("buttons"):
            results['terms'] = response.json()[0]["buttons"]
            results['out_text'] = response.json()[0]["text"]
        elif 'nhập mã' in response.json()[0]["text"]:
            results['inventory_status'] = True
            results['out_text'] = response.json()[0]["text"]
        elif "tìm sản phẩm tương tự" in response.json()[0]["text"]:
            results['similarity_status'] = True
            results['out_text'] = response.json()[0]["text"]
        else:
            results['out_text'] = response.json()[0]["text"]
        
        logging.info(f"+rasa out+:\n{results['out_text']}")
        print('+rasa out+:\n',results['out_text'])
        logging.info("====rasa done!====")
        print('====rasa done!====')
    
    if results['out_text'] == enum.TYPE_LLM:
        logging.info("=====LLM=====")
        print('======LLM======')
        # Initialize variables     
        demands = {'object': {}}
        products = []
    
        list_product = df["group_name"].unique()
        check_match_product = find_closest_match(query_text, list_product)
        if check_match_product[1] < 43:
            ok = 0
            # response_elastic = "Không có sản phẩm mà anh/chị cần!"
            print("=====Not product found=====")
        else:
            demands = classify_intent(query_text)
            print("= = = = result few short = = = =:", demands)
            if len(demands['object']) >= 1:
                response_elastic, products, ok = search_db(demands)
                print('===response_elastic===', response_elastic)
                if len(response_elastic) > 0:
                    set_save_outtext(user_id, response_elastic)
            else: 
                ok = 0
                # response_elastic = "Không có sản phẩm mà anh/chị cần!"
        t1 = time.time()
        result, memory, total_tokens = handle_conversation(ok, query_text, load_user_data(user_id), session_id)
        # conversation_messages_conv = memory.chat_memory.messages
        # messages_conv = messages_to_dict(conversation_messages_conv)
        # Save to DB
        # try:
        #     db_handler = DatabaseHandler()
        #     db_handler.insert_chat_message(user_id, session_id, current_time, messages_conv)
        # except Exception as e:
        #     print(f"An error occurred: {e}")
            
        # print("====memory===", messages_conv)
        # Predict handle conversation function
        try:
            results['out_text'] = result.replace("AI: ", "").replace("Assistant: ", "").replace("Support Staff: ", "").replace("*", "")
        except Exception as e:
            results['out_text'] = result
            
        results['products'] = products
        results['total_tokens'] = total_tokens
        if len(demands['object']) >= 1:
            results['terms'] = [
            {
                "payload": "similarity_status_true",
                "title": "Bạn muốn tìm kiếm sản phẩm tương tự?"
            },
            {
                "payload": "inventory_status_true",
                "title": "Bạn muốn tra cứu hàng tồn kho?"
            }
            ]
        logging.info(f"+LLM out+:\n{results['out_text']}")
        print('+LLM out+:\n',results['out_text'])
        logging.info("=====LLM done!=====")
        print('======LLM done!======')
    
    results['out_text'] = re.sub(r'\([^)]*\)', '', results['out_text'])
    return results


def predict_rasa_llm_for_image(objects, session_id, NameBot, user_id, type = enum.TYPE_IMAGE):
    # global user_storage
    # # Kiểm tra nếu user_id đã có trong storage
    # if session_id not in user_storage:
    #     user_storage[session_id] = {'save_outtext': ''}
        
    query_text = 'tôi cần tìm sản phẩm '
    for ob in objects:
        query_text += ob + ','

    logging.info("---SEARCH_IMAGE---")
    logging.info(f"inputText: {query_text}")

    results = {'terms':[],'out_text':'', 'inventory_status' : False, 'products': [], 'similarity_status': False, 'total_tokens':''}
    
    demands = {'object':objects}
    response_elastic, products, ok = search_db(demands)
    # user_storage[session_id]['save_outtext'] = response_elastic
    
    result, memory, total_tokens = handle_conversation(ok, query_text, response_elastic , session_id)
    conversation_messages_conv = memory.chat_memory.messages
    messages_conv = messages_to_dict(conversation_messages_conv)
    
    # Save to DB
    # try:
    #     db_handler = DatabaseHandler()
    #     db_handler.insert_chat_message(user_id, session_id, current_time, messages_conv)
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    
    # print("time predict conver: ", time.time() - t1)
    results['out_text'] = result
    results['products'] = products
    if len(objects) >= 1:
        results['terms'].append({
            "payload": "similarity_status_true",
            "title": "Bạn muốn tìm kiếm sản phẩm tương tự với nhu cầu"
            })
        # except:
        #     results['out_text'] = config_app['parameter']['can_not_res'][random_number]
    logging.info(f"Vcc_bot:\n{results['out_text']}")
    results['total_tokens'] = total_tokens
    results['out_text'] = results['out_text'].replace("AI: ", "").replace("Assistant: ", "").replace("Support Staff: ","").replace("*","")
    print('results in chat', results)
    return results



