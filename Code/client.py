import os
from socket import AF_INET, SOCK_DGRAM
from usocket import usocket

from packet_helper import *



class Client:
    def __init__(self):
        self.sock = usocket(AF_INET, SOCK_DGRAM, fiabilite=FIABILITE, taux_corruption=TAUX_CORRUPTION)
        self.sock.settimeout(TIMEOUT)
        self.server_address = None
        self.seq = 0

    def open(self, ip):
        self.server_address = (ip, SERVER_PORT)

        print("Connexion")

        # SYN
        for i in range(MAX_REPRISES):
            packet = build_packet(TYPE_SYN, self.seq, 0)
            self.sock.sendto(packet, self.server_address)

            # SYN-ACK
            try:
                data, _ = self.sock.recvfrom(CLIENT_MSS_PROPOSE + HEADER_SIZE)
            except Exception:
                print("Échec de la connexion (Timeout)")
                continue
            
            res = parse_packet(data)
            if res and res["type"] != TYPE_SYN_ACK:
                continue
            print("SYN-ACK")

            # ACK
            self.seq += 1
            ack_packet = build_packet(TYPE_ACK, self.seq, res["seq"])
            self.sock.sendto(ack_packet, self.server_address)

            print("Connected!")
            return True
        return False
            
    def wait_for_file(self):
        try:
            data, _ = self.sock.recvfrom(CLIENT_MSS_PROPOSE + HEADER_SIZE)
        except Exception:
            print("Échec de la connexion (Timeout)")
            return
        data = parse_packet(data)
        return data["data"].decode()

    def send_command(self, cmd: str):
        packet = build_packet(TYPE_CMD, self.seq, 0, cmd.encode())
        self.sock.sendto(packet, self.server_address)
        print("commande envoyée")
        return self.wait_for_file()

    def send_file(self, path: str):
        if not os.path.exists(path):
            print("File not found")
            return
        
        _, filename = os.path.split(path)
        
        packet = build_packet(TYPE_CMD, self.seq, 0, f"put {filename}".encode())
        self.sock.sendto(packet, self.server_address)

        print(f"Sending {filename}")

        with open(path, "rb") as file:
            data = file.read()

        chunks = [data[i:(i + SERVER_MSS_PROPOSE)] for i in range(0, len(data), SERVER_MSS_PROPOSE)]
        print(f"sending {len(chunks)} chunks")

        base = 0
        retries = 0
        
        while base < len(chunks):
            window = chunks[base:base + WINDOW_SIZE]

            # envoi
            for i, chunk in enumerate(window):
                packet = build_packet(TYPE_DATA, base + i, 0, chunk)
                self.sock.sendto(packet, self.server_address)

            # attendre ack
            try:
                data, _ = self.sock.recvfrom(CLIENT_MSS_PROPOSE + HEADER_SIZE)
            except TimeoutError:
                retries += 1
                print(f"Timeout ({retries})")

                if retries >= MAX_REPRISES:
                    print("Transfère raté")
                    # TODO: demander de coninuer tranfère
                    return
                continue
            
            res = parse_packet(data)

            if res and res["type"] == TYPE_ACK:
                ack = res["ack"]
                base = ack + 1
                retries = 0

        fin_packet = build_packet(TYPE_FIN, self.seq, 0)
        self.sock.sendto(fin_packet, self.server_address)

        print("Fichier envoyé")

    def close(self):
        if self.sock:
            self.sock.close()
        print("Déconnexion")



def main():
    client = Client()

    is_connected = False
    while True:
        cmd = input(">> ").strip()

        # dumb, but make sure to have the space at the end so
        # stuff like "putter" arent actually counted as commands
        # only put it when the command has params
        if cmd.startswith("open "):
            _, ip = cmd.split()
            if client.open(ip):
                is_connected = True

        elif cmd.startswith("put "):
            if is_connected:
                _, filename = cmd.split(' ')
                client.send_file(filename)
            else:
                print("Vous n'êtes pas connecté au serveur!")

        elif cmd == "ls":
            if is_connected:
                print(client.send_command("ls"))
            else:
                print("Vous n'êtes pas connecté au serveur!")

        elif cmd == "bye":
            client.close()
            break

        else:
            print("commande inconnue")


if __name__ == "__main__":
    main()