#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<string.h>
#include<sys/socket.h>
#include<sys/types.h>
#include <sys/un.h>
#include<netinet/in.h>
#include <pthread.h>
#include <semaphore.h>
#include<cjson/cJSON.h>
#include "./CustomLibs/LinkedList.h"

sem_t MusicThreadSem;
struct LinkedList MusicLinkedList;

void* ControllerThreadFunc(void*)
{
    int server_fd;
    struct sockaddr_in address;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8080); 
    socklen_t addrlen = sizeof(address);

    bind(server_fd, (struct sockaddr*)&address, sizeof(address));

    listen(server_fd, 1);

    while(1)
    {
        int new_socket = accept(server_fd, (struct sockaddr*)&address, &addrlen);
        char data[1024] = {0};
        read(new_socket, data, 1024 - 1); 

        cJSON *parsed_json = cJSON_Parse(data);

        // send to music queue if the command is related to music operation
        if (strcmp(cJSON_GetObjectItemCaseSensitive(parsed_json, "service")->valuestring, "music") == 0)
        {
            push(&MusicLinkedList, data);
            sem_post(&MusicThreadSem);
        }
    }
}

void* MusicThreadFunc(void*)
{
    int server_fd;
    struct sockaddr_un address;
    
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
    
    while(1)
    {   
        sem_wait(&MusicThreadSem);

        struct Node* node = pop(&MusicLinkedList);
        if(node != NULL) {
            send(client_fd, node->data, strlen(node->data), 0);
            free(node);
        }
    }
}

int main()
{
    sem_init(&MusicThreadSem, 0, 0);
    ll_init(&MusicLinkedList);

    pthread_t musicThread;
    pthread_create(&musicThread, NULL, MusicThreadFunc, NULL);

    pthread_t controllerThread;
    pthread_create(&controllerThread, NULL, ControllerThreadFunc, NULL);


    pthread_join(musicThread, NULL);
    pthread_join(controllerThread, NULL);
    
    return 0;
}