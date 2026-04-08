import os
from socket import AF_INET, SOCK_DGRAM
from usocket import usocket

from packet_helper import *



class Client:
    def __init__(self):
        self.sock = None
        self.server_addr = None
        self.seq = 0

    def open(self, ip):
        self.sock = usocket()
        self.sock.settimeout(TIMEOUT)
        self.server_addr = (ip, SERVER_PORT)

        print("Connexion")

        # SYN
        pkt = build_packet(TYPE_SYN, self.seq, 0)
        self.sock.sendto(pkt, self.server_addr)

        # SYN-ACK
        try:
            data, _ = self.sock.recvfrom(2048)
        except Exception:
            print("Connection failed")
            return
        
        res = parse_packet(data)
        if res and res["type"] == TYPE_SYN_ACK:
            print("SYN-ACK")

            # ACK
            self.seq += 1
            ack_pkt = build_packet(TYPE_ACK, self.seq, res["seq"])
            self.sock.sendto(ack_pkt, self.server_addr)

            print("Connected!")

    def send_command(self, cmd: str):
        pkt = build_packet(TYPE_CMD, self.seq, 0, cmd.encode())
        self.sock.sendto(pkt, self.server_addr)

    def send_file(self, filename):
        if not os.path.exists(filename):
            print("File not found")
            return

        print(f"Sending {filename}")

        with open(filename, "rb") as f:
            data = f.read()

        chunks = [data[i:(i + CLIENT_MSS_PROPOSE)] for i in range(0, len(data), CLIENT_MSS_PROPOSE)]

        base = 0
        retries = 0

        while base < len(chunks):
            window = chunks[base:base + WINDOW_SIZE]

            # envoi
            for i, chunk in enumerate(window):
                pkt = build_packet(TYPE_DATA, base + i, 0, chunk)
                self.sock.sendto(pkt, self.server_addr)

            # attendre ack
            try:
                self.sock.settimeout(TIMEOUT)
                data, _ = self.sock.recvfrom(2048)
            except Exception:
                retries += 1
                print(f"Timeout ({retries})")

                if retries >= MAX_REPRISES:
                    print("Transfère raté")
                    return
                continue
            
            res = parse_packet(data)

            if res and res["type"] == TYPE_ACK:
                ack = res["ack"]
                base = ack + 1
                retries = 0

            

        fin_pkt = build_packet(TYPE_FIN, self.seq, 0)
        self.sock.sendto(fin_pkt, self.server_addr)

        print("Fichier envoyé")

    def close(self):
        if self.sock:
            self.sock.close()
        print("Déconnexion")



def main():
    client = Client()

    while True:
        cmd = input(">> ").strip()

        # dumb, but make sure to have the space at the end so
        # stuff like "putter" arent actually counted as commands
        # only put it when the command has params
        if cmd.startswith("open "):
            _, ip = cmd.split()
            client.open(ip)

        elif cmd.startswith("put "):
            _, filename = cmd.split()
            client.send_file(filename)

        elif cmd == "ls":
            client.send_command("ls")

        elif cmd == "bye":
            client.close()
            break

        else:
            print("commande inconnue")


if __name__ == "__main__":
    main()