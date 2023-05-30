from dotenv import load_dotenv
from requests import get, post
import threading
from time import sleep
from datetime import datetime
import os
import json
from subprocess import Popen
from urllib.request import urlretrieve
from play_music import *
import ChatBot.smartcar as smartcar 

load_dotenv()

#Setup Spotify API
# https://www.youtube.com/watch?v=WAmEZBEeNmg
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

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

def lane_detection(is_running):
    sc = smartcar.SmartCar()
    is_running = True
    while is_running:
        sc.lane_detection_loop()

def download(download_id, file_type):
    address = base_address + "/getFile"
    data = {"file_id": download_id} 
    response = get(address, json=data) 
    dictionary = response.json() 
    link_ending = dictionary["result"]["file_path"] 
    file_link = "https://api.telegram.org/file/bot" + teleg_key + "/" + link_ending
    if file_type == "photo":
        file_destination = "/home/mendel/SmartMoves/AddOn/ChatBot/audio/" + now_datetime() + ".jpg" 
        urlretrieve(file_link, str(file_destination))
    elif file_type == "voice":
        file_destination = "/home/mendel/SmartMoves/AddOn/ChatBot/audio/" + now_datetime() + ".wav"
        urlretrieve(file_link, str(file_destination))


address = base_address + "/sendMessage"
data = {"chat_id": conversation_id, "text": "Hello how can I help you?"}
response = post(address, json=data)

next_update_id = 0
active_bot = True

while active_bot:
    address = base_address + "/getUpdates"
    data = {"offset": next_update_id}
    response = get(address, json=data)
    dictionary_of_response = response.json()
    data = response.json()
    json_formatted_str = json.dumps(dictionary_of_response["result"], indent=2)
    print(json_formatted_str)
    for result in dictionary_of_response["result"]:
        message = result["message"]
        file_datetime = unix_to_datetime(message)
        print("file time:" + str(file_datetime))
        if "text" in message:
            text = message["text"]
            print(text)
            if text == "start":
                lane_detection(True)
                #threading.Thread(target = sc.lane_detection_loop).start()
            elif text == "stop":
                lane_detection(False)
        elif "voice" in message:
            file_id = message["voice"]["file_id"]
            download(file_id, "voice")
            #threading.Thread(target = download, args = (file_id, "voice",)).start()
        elif "photo" in message:
            photo_high_res = message["photo"][-1]
            file_id = photo_high_res["file_id"]
            download(file_id, "photo")
            #threading.Thread(target = download, args = (file_id, "photo",)).start()
        next_update_id = result["update_id"] + 1
