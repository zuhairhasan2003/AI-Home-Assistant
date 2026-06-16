#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int main()
{
    int sock;
    struct sockaddr_in server_addr;
    char json_message[1024];

    // Create socket
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        perror("socket");
        return 1;
    }

    // Setup server address
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    // Connect to server
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1) {
        perror("connect");
        return 1;
    }

    printf("Connected to server!\n");

    // Send demo data
    snprintf(json_message, sizeof(json_message),
        "{\"operation\": \"music\", \"user_input\": \"play birds of feather by billie eilish please\", \"parameter\": \"volume_50\"}");
    
    printf("Sending: %s\n", json_message);
    send(sock, json_message, strlen(json_message), 0);

    close(sock);
    printf("Message sent!\n");

    return 0;
}