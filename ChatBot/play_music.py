import os
from smartcar_04_dashboardcontrol import publish_mqtt
import speech_recognition as sr
from pydub import AudioSegment
from time import sleep
from youtube_search import YoutubeSearch
from pytube import YouTube
from pytube.exceptions import RegexMatchError


# Define the functions
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

    # Check if the text contains the word "play" or "stop playing"
    lowercased_text = text.lower()

    if "stop playing" in lowercased_text:
        stop_playing()
    elif "play" in lowercased_text:
        play_song(lowercased_text)

def stop_playing():
    print("Music stopped.")

def play_song(text):
    # Extract the song name from the text (assuming the format "Play <song name>")
    song_name = text.lower().split("play", 1)[1].strip()

    # Search for the song on YouTube
    search_query = f"{song_name} audio"
    try:
        results = YoutubeSearch(search_query, max_results=5).to_dict()
        if len(results) > 0:
            print("Search Results:")
            for i, video in enumerate(results, start=1):
                print(f"{i}. {video['title']}")
            print()

            # Select the first result to play
            video_id = results[0]["id"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            audio_url = YouTube(youtube_url).streams.filter(only_audio=True).first().url
            song_name = results[0]['title']
            publish_mqtt(song_name) 
            print(f"Now playing: {results[0]['title']}")
            os.system(f"mpg123 -q {audio_url} > /dev/null 2>&1 &")
            sleep(2)
        else:
            print("No results found for the song.")
    except RegexMatchError:
        print("No results found for the song.")
