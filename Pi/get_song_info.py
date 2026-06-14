import sys
import socket
from google import genai
import json
import asyncio

async def gemeni_api_req():
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
	Input: """ + sys.argv[1]

	response = await asyncio.to_thread(
	        client.models.generate_content,
		model="gemini-3.5-flash",
		contents=prompt)

	return response


async def kill_other_music():
	await asyncio.sleep(1)

async def main():

	gemeni_task = asyncio.create_task(gemeni_api_req())
	kill_task = asyncio.create_task(kill_other_music())

	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	sock.connect("/tmp/music.sock")

	response, _ = await asyncio.gather(gemeni_task, kill_task)

	# response = '{"song_name": "Safar", "singer_name": "Bayan", "confidence": 0.84}'

	json_response = json.loads(response.text)
	if(float(json_response['confidence']) >= 0.85):
		print("Song detected!")
		sock.send(json.dumps(json_response).encode())
	else:
		print("Song not found!!!")


asyncio.run(main())
