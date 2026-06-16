#ifndef LINKEDLIST_H
#define LINKEDLIST_H

struct Node {
    char data[1024];
    struct Node* next;
};

struct LinkedList {
    struct Node* head;
    struct Node* tail;
};

void ll_init(struct LinkedList * ll);
void push(struct LinkedList * ll, char data[1024]); // push data at the end
struct Node * pop(struct LinkedList * ll); // pops data from the start

#endif