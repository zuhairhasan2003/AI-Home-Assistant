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

	IF the user asks you to pick a song, then please SUGGEST them the song

	Input: """ + raw_json['user_input']

	response = client.models.generate_content(
		model="gemini-3.5-flash-lite",
		contents=prompt)

	try:
		json_response = json.loads(response.text)
	except json.JSONDecodeError:
		return None

	if(float(json_response['confidence']) >= 0.85):
		return json_response

	return None

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
current_song_player = None

print("MUSIC PLAYER - starting...", flush=True)

while True:

	while True:
		try:
			sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			sock.connect("/tmp/music.sock")
			print("MUSIC PLAYER - connected to controller...", flush=True)
			break
		except (FileNotFoundError, ConnectionRefusedError):
			print("MUSIC PLAYER - waiting for controller...", flush=True)
			time.sleep(1)
	
	while True:
		raw_json = sock.recv(1024)

		if not raw_json:
			break

		print(raw_json, flush=True)

		if(current_song_player != None):
			current_song_player.stop()

		if(json.loads(raw_json.decode())['operation'] == 'play'):

			json_obj = gemeni_api_req(json.loads(raw_json.decode()))

			print(json_obj, flush=True)
			
			if(json_obj is None):
				continue

			if json_obj.get("singer_name"):
				song_name = f"{json_obj['song_name']} - {json_obj['singer_name']}"
			else:
				song_name = json_obj["song_name"]

			request = youtube.search().list(
				q=song_name,
				part='snippet',
				maxResults=1
				)

			response = request.execute()

			if not response['items']:
				continue

			url = f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"

			ydl_opts = {
				'format': 'bestaudio/best',
				'noplaylist': True,
				'js_runtimes': {
					'node': {}
				},
				'extractor_args': {
					'youtube': {
						'player_client': ['default', 'web_embedded', '-android_vr']
					}
				},
			}

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

		elif(json.loads(raw_json.decode())['operation'] == 'stop'):
			player.stop()

	sock.close()