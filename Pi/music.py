import sys
import socket
from google import genai
from googleapiclient.discovery import build
import vlc
import yt_dlp
import json
import time
import os

def gemeni_api_req(raw_json):
	client = genai.Client()

	prompt = """ Identify the most likely real song from the input. The input may contain transcription errors, misheard lyrics, partial lyrics, or incorrect song/artist names.
	Return ONLY valid JSON:
	{"song_name":string|null,"singer_name":string|null,"confidence":number}
	Rules:
	* ONLY PLAIN TEXT, NOTHING EXTRA, JUST JSON
	* Return the official song title and artist name.
	* Do NOT simply repeat names from the input; correct them if needed.
	* Use lyrics, title fragments, phonetic similarity, and context to identify the song.
	* If no reliable match exists, return null for song_name and singer_name.
	* confidence must be 0-1 and reflect confidence in the match.
	* No explanations or extra text.
	Input: """ + raw_json['user_input']

	response = client.models.generate_content(
		model="gemini-3.5-flash",
		contents=prompt)

	try:
		json_response = json.loads(response.text)
	except json.JSONDecodeError:
		return None

	if(float(json_response['confidence']) >= 0.85):
		return json_response

	return None


while not os.path.exists("/tmp/music.sock"):
    time.sleep(1)
    print("MUSIC PLAYER - Waiting for server...")

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/music.sock")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
current_song_player = None

while True:
	raw_json = sock.recv(1024)

	if(current_song_player != None):
		current_song_player.stop()

	json_obj = gemeni_api_req(json.loads(raw_json.decode()))

	if(json_obj == None):
		continue

	song_name = f"{json_obj['song_name']} - {json_obj['singer_name']}" if json_obj.get("singer_name") else json_obj["song_name"]

	request = youtube.search().list(
		q=song_name,
		part='snippet',
		maxResults=1
		)

	response = request.execute()

	if not response['items']:
		continue

	url = f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"

	ydl_opts = { 'format': 'best', 'quiet': True, }

	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(url, download=False)
		video_url = info['url']
		title = info['title']

	instance = vlc.Instance(
		"--intf", "dummy",
    		"--no-video",
    		"--quiet",
    		"--no-osd",
    		"--verbose", "0")

	player = instance.media_player_new()
	player.set_mrl(video_url)
	player.play()
	current_song_player = player