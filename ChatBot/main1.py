import smartcar
import time
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import cv2
import numpy as np
from play_music import * 
from bot import *
#from app import * 
        
# # Bot stuff
# import multiprocessing
# from time import sleep
# import json
# from urllib.request import urlretrieve

# CNN stuff
from PIL import Image, ImageFont, ImageDraw
from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
import numpy

# Needed for transferring the image to the Server
import socket
import base64

#HOST = '192.168.0.109'    # The remote host
HOST = 'localhost'    # The remote host
PORT = 50007              # The same port as used by the server

# Prepare the model
model = "red3_edgetpu.tflite"
CLASSES = ["red", "redyellow", "green", "yellow", "off", "Person"]
COLORS_BGR = [[0, 0, 255], [49,125,237], [80, 176, 0], [0, 192, 255], [0, 0, 0], [100, 100, 100]]
COLORS = ['red', 'orange', 'green', 'yellow', 'black', 'grey']
THRESHOLD = 0.25
# Prepare model outputs
interpreter = make_interpreter(model)
interpreter.allocate_tensors()


# Font
font = ImageFont.truetype(r'/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)

# ID of the traffic light
tl = "TL05"

mode = "standby"

# Phase of the traffic light
phasemqtt = "red"
phasecnn = "red"


current_speed = 0

def drive(velocity):
    global current_speed
    sc = smartcar.SmartCar(use_ultrasonic = True, use_local_window = False)
    sc.speed = velocity
    current_speed = velocity
    sc.lane_detection()
    sc.user_command()
    sc.handle_actuators()
    sc.handle_window()

def sendframe(frame):
    framestream = cv2.resize(frame, (320, 240))
    # Send the frame via TCP
    ret, buffer = cv2.imencode('.jpg', framestream)
    b64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(b64, 'utf-8'))

# MQTT receive callback
def on_message(client, userdata, message):
    global mode, phasemqtt, steer, speed, music
    steer = 0
    speed = 0
    music = ""
    topic_str = message.topic
    payload_str = message.payload.decode('ASCII')
    print(f"Received: topic={topic_str}  payload={payload_str}")
    if topic_str == "SMARTCAR_control/mode":
        if payload_str == "standby":
            mode = "standby"
        elif payload_str == "lanedetection":
            mode = "lanedetection"
        elif payload_str == "tlviamqtt":
            mode = "tlviamqtt"
        elif payload_str == "tlviacnn":
            mode = "tlviacnn"
    if topic_str == "SMARTCAR_control/turn":
            steer = payload_str
    if topic_str == "SMARTCAR_control/speed":
            speed = payload_str
    if topic_str == "SMARTCAR_control/music":
        if payload_str != "stop":
            music = payload_str
        elif payload_str == "stop":
            music = "stop"
    if topic_str == tl:
        phasemqtt = payload_str


# MQTT publishing of smartcar values
def publish_mqtt(client, mode, speed, steer, campan, camtilt, tlphase, song_name):
    client.publish("SMARTCAR_status/mode", mode)
    client.publish("SMARTCAR_status/speed", speed)
    client.publish("SMARTCAR_status/steer", steer)
    client.publish("SMARTCAR_status/campan", campan)
    client.publish("SMARTCAR_status/camtilt", camtilt)
    client.publish("SMARTCAR_status/tlphase", tlphase)
    client.publish("SMARTCAR_status/music", song_name)
    

def analyze_draw_objects(draw, objs):
    objects = []
    """Draws the bounding box and label for each object."""
    for obj in objs:
        if obj.id > len(CLASSES)-1:
            print("Unknown class id:", obj.id)
        else:
            bbox = obj.bbox
            draw.rectangle([(bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax)],
                           outline=COLORS[obj.id], width=2)
            draw.text((bbox.xmin, bbox.ymin),
                      '%s (%d)' % (CLASSES[obj.id], obj.score*100),
                      fill=COLORS[obj.id])
            objects.append(CLASSES[obj.id])
            #print(str(bbox.xmin) + " " + str(bbox.xmax) + " " + str(bbox.ymin) + " " + str(bbox.ymax) + " Area of rectangle is " + str((bbox.xmax-bbox.xmin)*(bbox.ymax-bbox.ymin)))
            #print('%d\n%s\n%.2f' % (obj.id, CLASSES[obj.id], obj.score))
    return objects

def main():
    global phasecnn
    # MQTT connection
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    client.on_message = on_message
    client.subscribe("SMARTCAR_control/mode")
    client.subscribe("SMARTCAR_control/turn")
    client.subscribe("SMARTCAR_control/speed")
    client.subscribe("SMARTCAR_control/music")
    client.subscribe(tl)
    client.loop_start()
    # SmartCar object without using the local camera and control window
    sc = smartcar.SmartCar(use_ultrasonic = True, use_local_window = False)
    try:
        while not sc.quit:

            global current_speed

            # # check for new updates
            # address = base_address + "/getUpdates"    
            # data = {"offset": next_update_id}
            # response = get(address, json=data)
            # dictionary_of_response = response.json()
            # data = response.json()
            # json_formatted_str = json.dumps(dictionary_of_response["result"], indent=2)
            # print(json_formatted_str)
            
            phase2send = "off"
            # receive camera image and ultrasonic distance 
            sc.handle_sensors()
            # mode lanedetection
            if mode == "lanedetection":
                if sc.speed < 40:
                    sc.speed += 1
                # Call routines for driving the car
                drive(sc.speed)
                sc.lane_detection()
                sc.user_command()
                sc.handle_actuators()
                sc.handle_window()
                sendframe(sc.frame)
            # mode tlviamqtt
            elif mode == "tlviamqtt":
                # Set speed according traffic light phase
                if phasemqtt == "red":
                    sc.speed = 0
                elif phasemqtt == "redyellow":
                    sc.speed = 0
                elif phasemqtt == "yellow":
                    sc.speed = 30
                elif phasemqtt == "green":
                    sc.speed = 40
                # Call routines for driving the car
                sc.lane_detection()
                sc.user_command()
                sc.handle_actuators()
                sc.handle_window()
                sendframe(sc.frame)
                phase2send = phasemqtt
            # mode tlviacnn
            elif mode == "tlviacnn":
                # Convert to RGB color space
                image = Image.fromarray(cv2.cvtColor(sc.frame, cv2.COLOR_BGR2RGB))
                # Create a Draw object for drawing rectangle around the detected objects
                draw = ImageDraw.Draw(image)
                # Detect objects
                _, scale = common.set_resized_input(
                    interpreter, image.size, lambda size: image.resize(size, Image.ANTIALIAS))
                interpreter.invoke()
                objs = detect.get_objects(interpreter, THRESHOLD, scale)
                # Draw image and additional info
                if objs != None:
                    objects = analyze_draw_objects(draw, objs)
                frameout = numpy.array(image)
                sc.frame = cv2.cvtColor(frameout, cv2.COLOR_RGB2BGR)
                # Define the TL state with a certain priority for safety reasons
                phasecnn = "off"
                sc.speed = 40
                if "red" in objects:
                    phasecnn = "red"
                    sc.speed = 0
                elif "redyellow" in objects:
                    phasecnn = "redyellow"
                    sc.speed = 0
                elif "yellow" in objects:
                    phasecnn = "yellow"
                    sc.speed = 30
                elif "green" in objects:
                    phasecnn = "green"
                    sc.speed = 40
                # Call routines for driving the car
                sc.lane_detection()
                sc.user_command()
                sc.handle_actuators()
                sc.handle_window()
                sendframe(sc.frame)
                phase2send = phasecnn
            
            
            if music != "stop":
                play_song(music)
                print("music_start")
                continue
              
            elif music == "stop":
                stop_playing()
                print("music_stop")
                continue 
              
          
            if int(speed) == 10:
                drive(20)
                sendframe(sc.frame)
                continue
                
            elif int(speed) > 0:
                drive(int(speed))  
                sendframe(sc.frame)
                continue
                                
            elif int(speed) < 0: 
                drive(int(speed))
                sendframe(sc.frame)
                continue
                
            elif int(speed) == 0:
                drive(int(speed))
                sendframe(sc.frame)
                continue 
 
            
            if int(steer) > 0:
                sc.speed = current_speed
                sc.steer = int(steer)
                sc.lane_detection()
                sc.user_command()
                sc.handle_actuators()
                sc.handle_window()
                sendframe(sc.frame)
                continue 
                

            # mode standby
            else:
                sc.speed = 0
                sc.p_part = 0
                sc.i_part = 0
                sc.d_part = 0
                sc.handle_actuators()
                sc.handle_window()
                sendframe(sc.frame)
            # Publish the current values of the SmartCar
            publish_mqtt(client, mode, sc.speed, sc.steer, sc.campan, sc.camtilt, phase2send, music)
            
    finally:
        # Clean up the SmartCar object
        sc = None
        # Disconnect MQTT
        client.loop_stop()
        client.unsubscribe(tl)
        client.unsubscribe("SMARTCAR_control/mode")
        client.unsubscribe("SMARTCAR_control/turn")
        client.unsubscribe("SMARTCAR_control/speed")
        client.unsubscribe("SMARTCAR_control/music")
        client.disconnect()

if __name__ == "__main__":
    main()
