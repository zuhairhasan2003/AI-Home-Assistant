#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <sys/un.h>
#include <cjson/cJSON.h>
#include <gpiod.h>

int main()
{
    int client_fd = socket(AF_UNIX, SOCK_STREAM, 0);

    struct sockaddr_un server_addr;
    server_addr.sun_family = AF_UNIX;
    const char * sock_file = "/tmp/lights.sock";
    strncpy(server_addr.sun_path, sock_file, sizeof(server_addr.sun_path)-1);

    connect(client_fd, (struct sockaddr *)&server_addr, sizeof(server_addr));

    printf("Connected to the server!!!\n");

    const char * chip_name = "gpiochip0";
    struct gpiod_chip * chip = gpiod_chip_open_by_name(chip_name);
    unsigned int pin_offset = 5;
    struct gpiod_line * line = gpiod_chip_get_line(chip, pin_offset);
    gpiod_line_request_output(line, "led", 0);

    while(1)
    {
        char data[1024] = { 0 };
        read(client_fd, data, 1024-1);

        printf("%s\n", data);

        cJSON *parsed_json = cJSON_Parse(data);
        printf("\nDATA RECV :\n");
        printf("%s\n", cJSON_GetObjectItemCaseSensitive(parsed_json, "service")->valuestring);
        printf("%s\n", cJSON_GetObjectItemCaseSensitive(parsed_json, "operation")->valuestring);
        printf("%s\n", cJSON_GetObjectItemCaseSensitive(parsed_json, "user_input")->valuestring);

        if(cJSON_GetObjectItemCaseSensitive(parsed_json, "operation")->valuestring == "turn_on")
        {
            gpiod_line_set_value(line, 1);
        }
        else if(cJSON_GetObjectItemCaseSensitive(parsed_json, "operation")->valuestring == "turn_off")
        {
            gpiod_line_set_value(line, 0);
        }
    }

    return 0;
}