import client
import server


# main program loop that lets you choose between server or client to continue
# or exit the program
def main_loop():
    default_host = "127.0.0.1"
    default_port = 2222
    loop = True

    while loop:
        command = input("[MAIN MENU] Command (server/client/exit): ")
        host = ""
        port = ""

        if command == "server":
            host = input("[S] Choose your IP address (" + default_host + "): ")
            port = input("[S] Choose your port (" + str(default_port) + "): ")

        elif command == "client":
            host = input("[C] Choose the target's IP address (" + default_host + "): ")
            port = input("[C] Choose the target's port (" + str(default_port) + "): ")

        elif command == "exit":
            exit()

        else:
            continue

        if host == "":
            host = default_host
        if port == "":
            port = default_port

        if command == "server":
            server.Server(host, int(port))

        elif command == "client":
            client.Client(host, int(port))


# main starter
if __name__ == '__main__':
    main_loop()
