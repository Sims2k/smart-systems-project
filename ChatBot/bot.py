from dotenv import load_dotenv
from requests import get, post 
from time import sleep
from datetime import datetime
import os
from urllib.request import urlretrieve

load_dotenv()

#Chatbot Setup
teleg_key = os.getenv("TELEGRAM_KEY")
conversation_id = os.getenv("CONVERSATION_ID")
base_address = "https://api.telegram.org/bot" + teleg_key

def now_datetime():  
    now  = datetime.now() 
    now_string = now.strftime("%d-%m-%Y_%H.%M.%S")   
    return now_string

def unix_to_datetime(data):
    #data = json.load('json_file_with_telegram_message.json')
    messageTime = data['date'] # UNIX time
    messageTime = datetime.utcfromtimestamp(messageTime) # datetime format
    #messageTime = messageTime.strftime('%Y-%m-%d %H:%M:%S') # formatted datetime
    TimeStamp = messageTime
    return TimeStamp

def download(download_id, file_type):
    address = base_address + "/getFile"
    data = {"file_id": download_id} 
    response = get(address, json=data) 
    dictionary = response.json() 
    link_ending = dictionary["result"]["file_path"] 
    file_link = "https://api.telegram.org/file/bot" + teleg_key + "/" + link_ending
    if file_type == "photo":
        file_destination = "ChatBot/images/my_image_" + now_datetime() + ".jpg" 
        urlretrieve(file_link, str(file_destination))
    elif file_type == "voice":
        file_destination = "ChatBot/audio/my_audio_" + now_datetime() + ".wav"
        urlretrieve(file_link, str(file_destination))
        return file_destination
        

def send_message(message):
    address = base_address + "/sendMessage"
    data = {"chat_id": conversation_id, "text": message}
    response = post(address, json=data)