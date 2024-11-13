import socket
import os
import asyncio
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def async_send_file(client_socket, file_path, start_position, byes_buff_size):
    try:
        # Open the file and send data asynchronously from the start position
        if not byes_buff_size:
            byes_buff_size = 1024 * 1024
        with open(file_path, "rb") as file:
            file.seek(start_position)
            while True:
                send_unit = file.read(byes_buff_size)
                if not send_unit:
                    break
                await asyncio.get_running_loop().sock_sendall(client_socket, send_unit)
        logging.info("File transfer complete.")
    except (socket.error, OSError) as e:
        logging.error(f"Network error or client disconnect: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        client_socket.close()
        logging.info("Connection closed with client.")


def handle_client(client_socket):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Receive file path
        file_path = client_socket.recv(256).decode('utf-8').strip()
        print(f"Request to transfer file: {file_path}")
        if not os.path.exists(file_path):
            logging.error(f"{file_path} does not exist!")
            client_socket.sendall(b"ERROR: File not found!".ljust(25))
            return
        # Send the file size to the client
        file_size = os.path.getsize(file_path)
        client_socket.sendall(str(file_size).encode('utf-8').ljust(20))
        # Receive the client end byes_buff_size
        byes_buff_size = client_socket.recv(10).decode('utf-8').strip()
        byes_buff_size = 1024 * 1024 if byes_buff_size == 'None' else int(byes_buff_size)
        print(f"byes_buff_size is: {byes_buff_size}")
        # Receive the start position
        start_position = int(client_socket.recv(20).decode('utf-8').strip())
        logging.info(f"Starting file transfer from byte {start_position} for {file_path}")

        # Run asynchronous send file task
        loop.run_until_complete(async_send_file(client_socket, file_path, start_position, byes_buff_size))
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        loop.close()


def start_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        logging.info(f"File copy server listening on {host}:{port}")

        # Initialize ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as executor:
            try:
                while True:
                    # Accept incoming client connections
                    client_socket, client_address = server_socket.accept()
                    logging.info(f"Connection established with {client_address}")

                    # Submit the client handler to the thread pool
                    executor.submit(handle_client, client_socket)
            except KeyboardInterrupt:
                logging.info("Shutting down server...")
            except Exception as e:
                logging.error(f"An unexpected error occurred in server: {e}")
            finally:
                logging.info("Server shut down successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='File transfer client.')
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0', help='The server hostname or IP address.')
    parser.add_argument('-p', '--port', type=int, default=58089, help='The server port number.')

    args = parser.parse_args()
    start_server(args.host, args.port)


