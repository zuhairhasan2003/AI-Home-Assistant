import sys
import socket
from google import genai

client = genai.Client()

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/music.sock")


while(1):
	response = client.models.generate_content(
		model="gemini-3.5-flash",
    		contents=sys.argv[1])

	sock.send(response.text.encode())
