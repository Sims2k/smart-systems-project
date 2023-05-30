from dotenv import load_dotenv
import os
import speech_recognition as sr
from pydub import AudioSegment
import webbrowser
import requests

load_dotenv()

# Setup YouTube API
# You need to enable the YouTube Data API v3 and get an API key
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

def convert_audio(input_file, output_file, output_format):
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format=output_format)

def translate_audio(file_path):
    convert_audio(file_path, file_path, "wav")
    
    # Load the audio file and preprocess it if needed
    audio = AudioSegment.from_file(file_path)
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
    text = recognizer.recognize_google(audio_data)
    print(text)

    # Check if the text contains the word "play"
    if "play" in text.lower():
        # Extract the song name from the text (assuming the format "Play <song name>")
        song_name = text.lower().split("play", 1)[1].strip()

        # Search for the song on YouTube
        query = f"{song_name} audio"
        search_url = f"https://www.googleapis.com/youtube/v3/search?key={youtube_api_key}&part=snippet&q={query}&type=video&maxResults=1"
        response = requests.get(search_url)
        json_data = response.json()
        if json_data["items"]:
            video_id = json_data["items"][0]["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"Now playing: {song_name}")

            # Open the YouTube video in the same tab
            webbrowser.open(video_url, new=0)
        else:
            print(f"No results found for: {song_name}")
