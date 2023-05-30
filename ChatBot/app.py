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
import smartcar


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

# Create a stop flag and lock for synchronization
lane_detection_stop_flag = threading.Event()
lane_detection_thread = None

def lane_detection():
    sc = smartcar.SmartCar()
    while not lane_detection_stop_flag.is_set():
        print("Self-driving is running...")
        sc.lane_detection_loop()
        sleep(1)

def download(download_id, file_type):
    address = base_address + "/getFile"
    data = {"file_id": download_id} 
    response = get(address, json=data) 
    dictionary = response.json() 
    link_ending = dictionary["result"]["file_path"] 
    file_link = "https://api.telegram.org/file/bot" + teleg_key + "/" + link_ending
    if file_type == "photo":
        file_destination = "/home/mendel/SmartMoves/AddOn/ChatBot/images/" + now_datetime() + ".jpg" 
        urlretrieve(file_link, str(file_destination))
    elif file_type == "voice":
        file_destination = "/home/mendel/SmartMoves/AddOn/ChatBot/audio/" + now_datetime() + ".wav"
        urlretrieve(file_link, str(file_destination))
        translate_audio(file_destination)


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
            '''
            The lane_detection_thread variable to keep track of the thread running the lane_detection() function. Initially, it is set to None. When the "start" text is received, we check if the lane_detection_thread is None or not alive. If it is None or not alive, indicating that the lane detection is not running, we start a new thread for the lane_detection() function. We also clear the lane_detection_stop_flag to ensure the function can execute.When the "stop" text is received, we set the lane_detection_stop_flag to stop the lane detection. Additionally, we check if the lane_detection_thread exists and is alive, and then call lane_detection_thread.join() to wait for the thread to complete before proceeding.
            '''
            if text == "start":
                if lane_detection_thread is None or not lane_detection_thread.is_alive():
                    # Start the lane detection thread
                    lane_detection_stop_flag.clear()
                    lane_detection_thread = threading.Thread(target=lane_detection)
                    lane_detection_thread.start()
            elif text == "stop":
                # Set the stop flag to stop the lane detection
                lane_detection_stop_flag.set()
                if lane_detection_thread is not None and lane_detection_thread.is_alive():
                    lane_detection_thread.join()
        elif "voice" in message:
            file_id = message["voice"]["file_id"]
            download(file_id, "voice")
        elif "photo" in message:
            photo_high_res = message["photo"][-1]
            file_id = photo_high_res["file_id"]
            download(file_id, "photo")
            
        next_update_id = result["update_id"] + 1