import os
import sys
import unicodedata
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
                title = video['title']
                sanitized_title = sanitize_string(title)
                try:
                    print(f"{i}. {sanitized_title}")
                except UnicodeEncodeError:
                    print(f"{i}. {sanitized_title.encode(sys.stdout.encoding, errors='replace').decode()}")

            # Select the first result to play
            video_id = results[0]["id"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            audio_file = download_audio(youtube_url)
            if audio_file:
                song_name = results[0]['title']
                #publish_mqtt(song_name)
                print(f"Now playing: {results[0]['title']}")
                #print("COMMAND: " + r"C:\PATH_Programs\mpg123-1.31.3-x86-64\mpg123.exe -q " + audio_file + " > NUL 2>&1")
                os.system(r"C:\PATH_Programs\mpg123-1.31.3-x86-64\mpg123.exe -q " + audio_file + " > NUL 2>&1")
                sleep(2)
            else:
                print("Failed to download the audio.")
        else:
            print("No results found for the song.")
    except RegexMatchError:
        print("No results found for the song.")

def sanitize_string(text):
    sanitized_text = "".join(
        char if unicodedata.category(char) != "Cc" else f"[Unsupported Character: U+{ord(char):04X}]"
        for char in text
    )
    return sanitized_text

def download_audio(url):
    try:
        video = YouTube(url)
        audio_stream = video.streams.filter(only_audio=True).first()
        if audio_stream:
            # Set the output path to the "songs" folder
            output_path = os.path.join(os.getcwd(), "ChatBot\songs")
            os.makedirs(output_path, exist_ok=True)  # Create the folder if it doesn't exist
            pre_audio_file = audio_stream.download(output_path=output_path, filename_prefix="audio_")
            # Replace spaces with underscores in the file name
            audio_file = pre_audio_file.replace(" ", "_")
            os.rename(pre_audio_file, audio_file)
            return audio_file
        else:
            print("No audio stream available for the video.")
            return None
    except RegexMatchError:
        print("Invalid URL or no matching video found.")
        return None

