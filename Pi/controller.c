#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<string.h>
#include<sys/socket.h>
#include<sys/types.h>
#include <sys/un.h>
#include<netinet/in.h>

void MusicSocket()
{
    int server_fd;
    struct sockaddr_un address;
    char buffer[1024] = {0};

    // setup server file descriptor
    server_fd = socket(AF_UNIX, SOCK_STREAM, 0);

    // remove the socket file if it already exists
    unlink("/tmp/music.sock");


    // bind the socket to the address "tmp/music.sock"
    memset(&address, 0, sizeof(address));
    address.sun_family = AF_UNIX;
    strcpy(address.sun_path, "/tmp/music.sock");

    bind(server_fd, (struct sockaddr*)&address, sizeof(address));

    // listen for incoming connections
    listen(server_fd, 1);
    
    // accept a connection from a client
    int client_fd = accept(server_fd, NULL, NULL);

    // send a message to the client
    char message[] = "{\"operation\": \"music\", \"user_input\": \"can you please play sahiba\"}";
    send(client_fd, message, strlen(message), 0);

    while(1)
    {
        sleep(500);
    }
}

int main()
{
    MusicSocket();

    return 0;
}