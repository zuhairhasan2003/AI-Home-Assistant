#include "LinkedList.h"
#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include <pthread.h>

void ll_init(struct LinkedList * ll)
{
    ll->head = NULL;
    ll->tail = NULL;
    pthread_mutex_init(&ll->lock, NULL);
}

void push(struct LinkedList * ll, char data[1024]) // push data at the end
{
    struct Node * node = malloc(sizeof(struct Node));
    node->next = NULL;
    strncpy(node->data, data, sizeof(node->data) - 1);

    if(ll->head == NULL) // linkedlist is empty
    {
        ll->head = node;
        ll->tail = node;
    }
    else
    {
        ll->tail->next = node;
        ll->tail = node;
    }
}

struct Node * pop(struct LinkedList * ll) // pops data from the start
{
    if(ll->head == NULL)
        return NULL;

    struct Node * node = ll->head;
    ll->head = ll->head->next;

    if(ll->head == NULL)
        ll->tail = NULL;

    return node;
}