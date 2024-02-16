# Peer-to-Peer File Sharing System in Python
This Python script implements a simple peer-to-peer (P2P) file sharing system. It uses TCP and UDP sockets for communication between peers, and JSON for data serialization and deserialization.

## Features
Split a file into chunks and announce the availability of these chunks to all peers in the network.
Discover available chunks from other peers.
Download chunks from other peers.
Download a specific chunk from a specific peer.
Combine downloaded chunks back into the original file.
Console command interface to interact with the system.
## How it works
The **file_splitter** function splits a file into chunks.
The **chunk_announcer** function periodically broadcasts the availability of the chunks to all peers.
The **content_discovery** function listens for chunk announcements from other peers and updates a content dictionary that maps chunk names to the IP addresses of the peers that have those chunks.
The **chunk_downloader** function downloads chunks from other peers based on the content dictionary.
The **get_chunk_from_ip** function downloads a specific chunk from a specific peer.
The **chunk_uploader** function listens for chunk download requests from other peers and sends the requested chunks.
The **console_sniffer** function provides a command line interface for the user to interact with the system, such as to download a file, download a specific chunk from a specific peer, or print the current content dictionary.
## Usage
Run the script: python p2p_file_sharing.py
When prompted, enter the name of the file to host (without the extension).
Use the following commands to interact with the system:
* d/<requested_file_name>: Download the requested file.
* pd/: Print the current content dictionary.
* s/<file_name>: Split the specified file into chunks.
* g/<_ip_>/<chunk_name>: Download a specific chunk from a specific peer.
## Requirements
This script requires Python 3.7 or higher. No external libraries are needed.
