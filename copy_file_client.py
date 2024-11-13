import socket
import os
import argparse
import sys
from tqdm import tqdm


def pre_file_copy(host, port, file_path, byes_speed, file_save_location):
    local_file_path = os.path.join(file_save_location, os.path.basename(file_path))

    try:

        with socket.create_connection((host, port)) as server_socket:
            server_socket.sendall(file_path.encode('utf-8').ljust(256))
            remote_file_info = server_socket.recv(25).decode('utf-8').strip()
            if remote_file_info == "ERROR: File not found":
                print("Remote File not found!")
                sys.exit(1)
            file_size = int(remote_file_info)
            print(f"file_size is: {file_size}")
            byes_buff_size = 1024 * 1024 if byes_speed is None else byes_speed
            server_socket.sendall(str(byes_buff_size).encode('utf-8').ljust(10))
            print(f"byes_buff_size is: {byes_buff_size}")
            if os.path.exists(local_file_path):
                print(f"Resuming file transfer for {local_file_path}")
                file_copy_a(local_file_path, server_socket, byes_buff_size, file_size)
            else:
                print(f"Starting new file transfer for {local_file_path}")
                file_copy_w(local_file_path, server_socket, byes_buff_size, file_size)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"Process for {local_file_path} is complete or interrupted.")


def file_copy_w(local_file_path, server_socket, byes_buff_size, file_size):
    try:
        server_socket.sendall("0".encode('utf-8').ljust(20))
        print(f"File size: {file_size} bytes. Starting download...")

        with open(local_file_path, "wb") as save_file, \
                tqdm(desc="Receiving file", total=file_size, unit="B", unit_scale=True) as pbar:
            while True:
                file_content = server_socket.recv(byes_buff_size)
                if not file_content:
                    break
                save_file.write(file_content)
                pbar.update(len(file_content))

    except Exception as e:
        print(f"An error occurred during file write: {e}")
    finally:
        print("File copy complete or interrupted!")


def file_copy_a(local_file_path, server_socket, byes_buff_size, file_size):
    try:

        start_length = os.path.getsize(local_file_path)
        server_socket.sendall(str(start_length).encode('utf-8').ljust(20))

        print(f"File size: {file_size} bytes. Resuming download from {start_length} bytes...")

        with open(local_file_path, "ab") as save_file, \
                tqdm(desc="Appending file", total=file_size, unit="B", unit_scale=True, initial=start_length) as pbar:
            while True:
                file_content = server_socket.recv(byes_buff_size)
                if not file_content:
                    break
                save_file.write(file_content)
                pbar.update(len(file_content))

    except Exception as e:
        print(f"An error occurred during file append: {e}")
    finally:
        print("File copy complete or interrupted!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='File transfer client.')
    parser.add_argument('-H', '--host', required=True, type=str, help='The server hostname or IP address.')
    parser.add_argument('-p', '--port', required=True, type=int, help='The server port number.')
    parser.add_argument('-f', '--file', required=True, type=str, help='The absolute path of the target file.')
    parser.add_argument('-s', '--speed', type=int, help='The bytes buff size for socket.recv().')
    parser.add_argument('-o', '--output', type=str, default='./', help='The location to save the file')

    args = parser.parse_args()

    pre_file_copy(args.host, args.port, args.file, args.speed, args.output)

