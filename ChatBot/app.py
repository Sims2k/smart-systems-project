from requests import get
import threading
from time import sleep
import json
from urllib.request import urlretrieve
from bot import *
from play_music import *

# Create a stop flag and lock for synchronization
lane_detection_stop_flag = threading.Event() 
lane_detection_thread = None

def lane_detection():
    #sc = smartcar.SmartCar()
    while not lane_detection_stop_flag.is_set():
        print("Self-driving is running...")
        #sc.lane_detection_loop()
        sleep(1)

def start_car():
    global lane_detection_thread
    if lane_detection_thread is None or not lane_detection_thread.is_alive():
        # Start the lane detection thread
        lane_detection_stop_flag.clear()
        lane_detection_thread = threading.Thread(target=lane_detection)
        lane_detection_thread.start()
        send_message("Self-driving is running...")

def stop_car():
    global lane_detection_thread
    # Set the stop flag to stop the lane detection
    lane_detection_stop_flag.set()
    if lane_detection_thread is not None and lane_detection_thread.is_alive():
        lane_detection_thread.join()
        send_message("Self-driving has stopped")

send_message("Hello, how can I help you")

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
            text = message["text"].lower()
            if text == "start":
                start_car()
            elif text == "stop":
                stop_car()
        elif "voice" in message:
            file_id = message["voice"]["file_id"]
            audio_file = download(file_id, "voice")
            translate_audio(audio_file)
        elif "photo" in message:
            photo_high_res = message["photo"][-1]
            file_id = photo_high_res["file_id"]
            download(file_id, "photo")
            
        next_update_id = result["update_id"] + 1