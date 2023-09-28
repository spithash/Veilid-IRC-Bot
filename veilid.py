import socket
import ssl
import subprocess
import re
import time

# Define ANSI escape codes for colors
GREEN = '\033[32m'
PURPLE = '\033[95m'
BLUE = '\033[94m'
YELLOW = '\033[33m'
ENDC = '\033[0m'

# Define the allowed directory
allowed_directory = "/home/user/veilidbot"

def create_ssl_socket():
    irc_socket = socket.socket(socket.AF_INET)
    ssl_socket = ssl.create_default_context().wrap_socket(irc_socket, server_hostname="irc.libera.chat")
    return ssl_socket

def execute_veilid_dht_get(hash_value, subkey):
    command = f'/home/user/veilidbot/veilid-dht-get {hash_value}/{subkey}'
    try:
        print(f"{BLUE}Executing command: {command}{ENDC}")

        # Validate file path
        if not command.startswith(allowed_directory):
            return f"Error: Access denied."

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Command failed with exit code {process.returncode}")
            print(f"Error: {stderr.decode()}")
            return f"Error: {stderr.decode()}"
        else:
            print(f"Output: {stdout.decode()}")
            return stdout.decode()
    except Exception as e:
        print(f"Error executing command: {e}")
        return str(e)

def main():
    username = "username"
    password = "YourStongPassword"
    nickname = "VeilidRulez"
    channels = ["#veilid", "#test2"]  # List of channels

    irc_socket = create_ssl_socket()
    irc_socket.connect(("irc.libera.chat", 6697))

    irc_socket.sendall(f"PASS {password}\r\n".encode())
    irc_socket.sendall(f"NICK {nickname}\r\n".encode())
    irc_socket.sendall(f"USER {username} 0 * :{nickname}\r\n".encode())
    irc_socket.sendall(f"MODE {nickname} +RZiw\r\n".encode())

    # Join multiple channels
    for channel in channels:
        irc_socket.sendall(f"JOIN {channel}\r\n".encode())

    # Send the NickServ identify command
    irc_socket.sendall(f"PRIVMSG NickServ :IDENTIFY {nickname} {password}\r\n".encode())

    # Variable to track if a valid command has been executed
    valid_command_executed = False

    while True:
        try:
            message = irc_socket.recv(2048).decode().strip()
            print(f"{GREEN}Received message (length {len(message)}): {message}{ENDC}")

            if message.startswith("PING"):
                print(f"{YELLOW}Received PING, responding with PONG{ENDC}")
                irc_socket.sendall(f"PONG {message.split()[1]}\r\n".encode())
                continue
            if re.match(r"^:.*!.*@.* PRIVMSG #\w+ :!record get [A-Z0-9a-z_-]+ [0-9]+$", message):
                if valid_command_executed:
                    print(f"{PURPLE}Ignoring additional command{ENDC}")
                    continue

                valid_command_executed = True

                print(f"{PURPLE}Received !record get command{ENDC}")
                parts = message.split()
                hash_value = parts[-2]
                subkey = parts[-1]
                print(f"Hash Value: {hash_value}, Subkey: {subkey}")
                output = execute_veilid_dht_get(hash_value, subkey)
                print(f"Output from execute_veilid_dht_get: {output}")
                irc_socket.sendall(f"PRIVMSG {parts[2]} :{output}\r\n".encode())
                
                # Reset valid_command_executed
                valid_command_executed = False
        except socket.error as e:
            print(f"Socket error: {e}")
            print(f"Reconnecting in 10 seconds...")
            time.sleep(10)
            try:
                irc_socket = create_ssl_socket()
                irc_socket.connect(("irc.libera.chat", 6697))
                irc_socket.sendall(f"PASS {password}\r\n".encode())
                irc_socket.sendall(f"NICK {nickname}\r\n".encode())
                irc_socket.sendall(f"USER {username} 0 * :{nickname}\r\n".encode())
                irc_socket.sendall(f"MODE {nickname} +RZiw\r\n".encode())

                for channel in channels:
                    irc_socket.sendall(f"JOIN {channel}\r\n".encode())

                irc_socket.sendall(f"PRIVMSG NickServ :IDENTIFY {nickname} {password}\r\n".encode())

            except Exception as e:
                print(f"Reconnection failed: {e}")
                continue

if __name__ == "__main__":
    main()
