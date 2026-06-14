import socket
import os
from googleapiclient.discovery import build
import vlc
import yt_dlp
import json
import time
import os

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

if os.path.exists("/tmp/music.sock"):
    os.remove("/tmp/music.sock")

sock.bind("/tmp/music.sock")
sock.listen(1)

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

current_song_player = None

while True:
	conn, _ = sock.accept()

	data = conn.recv(4096)

	if(current_song_player != None):
		current_song_player.stop()

	json_obj = json.loads(data.decode())

	song_name = f"{json_obj['song_name']} - {json_obj['singer_name']}" if json_obj.get("singer_name") else json_obj["song_name"]

	request = youtube.search().list(
		q=song_name,
		part='snippet',
		maxResults=1
		)

	response = request.execute()

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

	# time.sleep(info['duration'])
