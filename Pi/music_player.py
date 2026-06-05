import socket
import os

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Remove old socket file if it exists
if os.path.exists("/tmp/music.sock"):
    os.remove("/tmp/music.sock")

sock.bind("/tmp/music.sock")
sock.listen(1)

while True:
	conn, _ = sock.accept()

	data = conn.recv(4096)
	print(data.decode())
