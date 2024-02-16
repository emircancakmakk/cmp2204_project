import math
import threading
import os
import time
import json
import socket

# Max size of chunks in bytes
MAX_CHUNK_SIZE = 4096
CHUNK_NUM = 5  # Number of chunks per file
ANNOUNCE_PERIOD = 60  # Time between announcements in seconds
broadcast_address = '192.168.0.255'
content_dict = {}


def file_splitter(content_name):
    filename = content_name + '.png'
    c = os.path.getsize(filename)
    print('file size ', c, ' bytes\n')
    chunk_size = math.ceil(math.ceil(c) / CHUNK_NUM)
    print('chunk size ', chunk_size, ' bytes\n')

    index = 1
    with open(filename, 'rb') as infile:
        chunk = infile.read(int(chunk_size))
        while chunk:
            chunkname = content_name + '_' + str(index)
            print("chunk name is: " + chunkname)
            with open(chunkname, 'wb+') as chunk_file:
                chunk_file.write(chunk)
            index += 1
            chunk = infile.read(int(chunk_size))
    chunk_file.close()


def chunk_announcer(content_name):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((socket.gethostname(), 5001))

    # Ask the user for the initial file
    file_splitter(content_name)

    # Start announcing chunks
    while True:

        # Read the names of the chunk files
        chunk_files = []
        for f in os.listdir():
            if "_" in f and "." not in f:
                chunk_files.append(f)

        # Create the announcement message
        message = json.dumps({"chunks": chunk_files}).encode('utf-8')

        sock.sendto(message, (broadcast_address, 5001))
        # print(f'Broadcasting complete waiting for {ANNOUNCE_PERIOD} seconds...')
        time.sleep(ANNOUNCE_PERIOD)


def content_discovery():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    sock.bind(('0.0.0.0', 5001))
    # Initialize the content dictionary

    while True:
        # Receive a message
        data, addr = sock.recvfrom(2048)
        # Parse the message
        message = json.loads(data.decode('utf-8'))

        # Explanation is provided with ChatGpt incredible work!!!!!!!!!!!!!!!!
        # The 'for' loop iterates over every key-value pair in the 'content_dict' dictionary.
        # 'chunk' is the key and represents the name of the chunk.
        # 'ips' is the value and represents a list of IP addresses associated with that chunk.
        for chunk, ips in content_dict.items():

            # 'addr' is a tuple containing the IP address and port number of the sender of the current message.
            # 'addr[0]' is the IP address of the sender.
            # Here, we check if the sender's IP address is in the list of IPs for the current chunk.
            if addr[0] in ips:
                # If the sender's IP address is in the list, we remove it.
                # This is because the sender has just sent us a new list of chunks that they have,
                # and we are updating our 'content_dict' to match that new list.
                # If a chunk is not in the new list but the sender's IP is associated with it in our 'content_dict',
                # we remove that association as the sender no longer has that chunk.
                ips.remove(addr[0])

        # Update the content dictionary
        for chunk in message['chunks']:
            if chunk not in content_dict:
                content_dict[chunk] = [addr[0]]
            else:
                if addr[0] not in content_dict[chunk]:
                    # Note addr[0] is the ip adress addr[1] is port ;)
                    content_dict[chunk].append(addr[0])

        # Print the detected user and their hosted content
        print(f'{addr[0]} : {", ".join(message["chunks"])}')


def chunk_downloader(content_name):
    chunk_names = []
    # Go through each chunk
    for i in range(1, 6):
        chunk_name = f"{content_name}_{i}"
        chunk_names.append(chunk_name)

        # If the chunk is not in the content dictionary, print a warning and continue to the next chunk
        if chunk_name not in content_dict or not content_dict[chunk_name]:
            print(f"NO KNOWN ONLINE PEER THAT ANNOUNCED {chunk_name}, CANNOT MERGE {content_name} ABORTING...")
            return

        # Try downloading the chunk from each peer until it is successfully downloaded
        for ip in content_dict[chunk_name]:

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # Set timeout to 5 seconds

            try:
                # Establish a TCP connection and request a chunk from a peer
                sock.connect((ip, 5000))  # Connect to the peer
                request = json.dumps({"requested_content": chunk_name}).encode('utf-8')
                sock.send(request)  # Send the request

                # Receive the chunk, While True part is a band-aid solution sent files were decreasing in size
                chunk_data = b""
                while True:
                    data = sock.recv(MAX_CHUNK_SIZE)
                    if not data:
                        break
                    chunk_data += data

                if len(chunk_data) == 0:
                    raise Exception(
                        f'DOWNLOAD ERROR: TRIED DOWNLOADING FROM {ip} CHUNK SIZE IS 0, TRYING OTHER SOURCE...')

                # Save the chunk to a file, To remember: 'wb' is for Write Binary
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)

                # Log the download, To remember: 'a' is for Append
                with open('download_log.txt', 'a') as log_file:
                    log_file.write(f"{time.ctime()} - {chunk_name} downloaded from {ip}\n")
                print(f'Successfully downloaded {chunk_name} from {ip} at {time.ctime()}')

            except Exception as e:
                print(f"Failed to download {chunk_name} from {ip}: {e}, REMOVING IP FROM CHUNK LIST...")
                # Remove the IP from the list associated with the chunk
                content_dict[chunk_name].remove(ip)
            finally:
                # Close the connection
                sock.close()

    with open(content_name + '.png', 'wb') as outfile:
        for chunk in chunk_names:
            with open(chunk, 'rb') as infile:
                outfile.write(infile.read())
            infile.close()


def chunk_uploader():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # For the server to listen on all available IP addresses, use ''
    server_socket.bind(('', 5000))
    server_socket.listen()

    while True:
        # Accept a new client connection
        conn, addr = server_socket.accept()
        requested_chunk_name = 'Unknown chunk'

        try:
            # Receive the JSON request
            request = json.loads(conn.recv(2048).decode('utf-8'))
            # Get the chunk name from the request
            requested_chunk_name = request["requested_content"]

            # Open the requested chunk file and send it back to the client
            if os.path.exists(requested_chunk_name):
                with open(requested_chunk_name, 'rb') as chunk_file:
                    chunk_data = chunk_file.read()
                    conn.send(chunk_data)
            else:
                raise Exception(f' REQUESTED FILE NOT FOUND...')

            # Log the file info after sending the chunk
            with open('upload_log.txt', 'a') as log_file:
                log_file.write(f"{time.ctime()} - {requested_chunk_name} sent to {addr[0]}\n")
            print(f'Successfully uploaded {requested_chunk_name} to {addr[0]} at {time.ctime()}')

        except Exception as e:
            print(f"Failed to send {requested_chunk_name} to {addr[0]}: {e}")
        finally:
            # Close the connection
            conn.close()


def get_chunk_from_ip(ip, chunk_name):

    # Establish a TCP connection and request the chunk from the IP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Set timeout to 5 seconds
    try:
        sock.connect((ip, 5000))  # Connect to the IP
        request = json.dumps({"requested_content": chunk_name}).encode('utf-8')
        sock.send(request)  # Send the request

        # Receive the chunk, While True part is a band-aid solution since files were decreasing in size
        chunk_data = b""
        while True:
            data = sock.recv(MAX_CHUNK_SIZE)
            if not data:
                break
            chunk_data += data

        if len(chunk_data) == 0:
            raise Exception(f'DOWNLOAD ERROR: TRIED DOWNLOADING {chunk_name} FROM {ip} BUT CHUNK SIZE IS 0')

        # Save the chunk to a file, To remember: 'wb' is for Write Binary
        with open(chunk_name, 'wb') as chunk_file:
            chunk_file.write(chunk_data)

        # Log the download, To remember: 'a' is for Append
        with open('download_log.txt', 'a') as log_file:
            log_file.write(f"{time.ctime()} - {chunk_name} downloaded from {ip}\n")
        print(f'Successfully downloaded {chunk_name} from {ip} at {time.ctime()}')

    except Exception as e:
        print(f"Failed to download {chunk_name} from {ip}: {e}")

    finally:
        # Close the connection
        sock.close()


def console_sniffer():
    print("\nUsable commands (While entering omit the ' char):\n"
          "Download requested file: 'd/<requested_file_name>'\n"
          "Print the current content dictionary: 'pd/'\n"
          "Split specified file in directory s/<file_name>\n"
          "Get specified chunk from an IP: 'g/<ip>/<chunk_name>")
    while True:
        command = input()

        if command.startswith("d/"):
            file_name = command.split('/')[1]
            # Start a new thread to download the file
            download_thread = threading.Thread(target=chunk_downloader, args=(file_name,))
            download_thread.start()
        elif command.startswith("pd/"):
            print(content_dict)
        elif command.startswith("s/"):
            file_name = command.split('/')[1]
            file_splitter(file_name)
        elif command.startswith("g/"):
            parts = command.split('/')
            if len(parts) != 3:
                print('Invalid command for getting a chunk. Use the format g/<ip>/<chunk_name>')
            else:
                ip = parts[1]
                chunk_name = parts[2]
                # Start a new thread to get the chunk from the specified IP
                get_thread = threading.Thread(target=get_chunk_from_ip, args=(ip, chunk_name))
                get_thread.start()
        else:
            print('Unknown command')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    content_name = input("Enter the name of the file to host (without extension): \n")

    # Running Chunk Announcer
    chunk_announcer_thread = threading.Thread(target=chunk_announcer, args=(content_name,))
    chunk_announcer_thread.start()

    # Running Content Discovery
    content_discovery_thread = threading.Thread(target=content_discovery)
    content_discovery_thread.start()

    # Running Chunk Uploader
    chunk_uploader_thread = threading.Thread(target=chunk_uploader)
    chunk_uploader_thread.start()

    console_sniffer_thread = threading.Thread(target=console_sniffer)
    time.sleep(2)
    console_sniffer_thread.start()

    # ... you can add other threads here ...

    # Wait for all threads to complete
    chunk_announcer_thread.join()
    content_discovery_thread.join()
    chunk_uploader_thread.join()
    console_sniffer_thread.join()
