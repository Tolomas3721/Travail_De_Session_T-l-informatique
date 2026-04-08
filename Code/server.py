import os
from socket import AF_INET, SOCK_DGRAM
from usocket import usocket

from packet_helper import *



class Server:
    def __init__(self):
        self.sock = usocket()
        self.sock.bind(("127.0.0.1", SERVER_PORT))
        self.sock.settimeout(TIMEOUT)

        print(f"Le serveur écoute le port: {SERVER_PORT}")

        self.client_addr = None
        self.expected_seq = 0
        self.received = {}


    def handshake(self):
        print("Attente de la connexion")

        while True:
            data, addr = self.sock.recvfrom(2048)
            packet = parse_packet(data)

            if packet and packet["type"] == TYPE_SYN:
                print("SYN reçu")

                self.client_addr = addr

                # SYN-ACK
                syn_ack = build_packet(TYPE_SYN_ACK, 0, packet["seq"])
                self.sock.sendto(syn_ack, addr)

                # ACK
                try:
                    data, _ = self.sock.recvfrom(2048)
                    ack_packet = parse_packet(data)

                    if ack_packet and ack_packet["type"] == TYPE_ACK:
                        print("Connexion établie")
                        return
                except:
                    print("Échec du handshake")

    def ls_command(self, packet):
        cmd = packet["data"].decode()

        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
            
        files = os.listdir(SAVE_DIR)
        response = '\n'.join(files).encode()
        res_packet = build_packet(TYPE_CMD, 0, 0, response)
        self.sock.sendto(res_packet, self.client_addr)

    def receive_file(self):
        print("Réception du fichier")

        self.expected_seq = 0
        self.received = {}

        while True:
            try:
                data, addr = self.sock.recvfrom(65536)
            except Exception:
                # TODO: timeout
                continue
            
            packet = parse_packet(data)

            if not packet:
                continue  # TODO: corrompu

            if packet["type"] == TYPE_DATA:
                seq = packet["seq"]

                if seq in self.received:
                    continue

                self.received[seq] = packet["data"]

                while self.expected_seq in self.received:
                    self.expected_seq += 1

                if seq % WINDOW_SIZE == 0:
                    ack_packet = build_packet(TYPE_ACK, 0, self.expected_seq - 1)
                    self.sock.sendto(ack_packet, addr)

            elif packet["type"] == TYPE_FIN:
                print("Transfère complété")
                self.save_file()
                return

            elif packet["type"] == TYPE_CMD:
                self.handle_command(packet)


    def save_file(self):
        filename = os.path.join(SAVE_DIR, "received_file")

        with open(filename, "wb") as f:
            for i in sorted(self.received):
                f.write(self.received[i])

        print(f"Fichier sauvergardé sous: {filename}")

    def run(self):
        while True:
            self.handshake()

            while True:
                try:
                    data, addr = self.sock.recvfrom(1024)
                except TimeoutError:
                    continue
                
                packet = parse_packet(data)

                if not packet:
                    continue

                if packet["type"] == TYPE_CMD:
                    cmd = packet["data"].decode()

                    if cmd.startswith("put"):
                        self.receive_file()

                    elif cmd == "ls":
                        self.ls_command(packet)

                elif packet["type"] == TYPE_FIN:
                    print("Déconnexion")
                    break

                



if __name__ == "__main__":
    server = Server()
    server.run()