import os
from socket import AF_INET, SOCK_DGRAM
from usocket import usocket

from packet_helper import *



class Server:
    def __init__(self):
        self.sock = usocket(AF_INET, SOCK_DGRAM, fiabilite=FIABILITE, taux_corruption=TAUX_CORRUPTION)
        self.sock.bind(("127.0.0.1", SERVER_PORT))
        self.sock.settimeout(TIMEOUT)

        print(f"Le serveur écoute le port: {SERVER_PORT}")

        self.client_address = None
        self.expected_seq = 0
        self.received = {}


    def handshake(self):
        print("Attente de la connexion")

        while True:
            try:
                data, address = self.sock.recvfrom(65536)
            except TimeoutError:
                # fait juste attendre que le client se connecte
                continue
            packet = parse_packet(data)

            if packet and packet["type"] == TYPE_SYN:
                print("SYN reçu")

                self.client_address = address

                # SYN-ACK
                syn_ack = build_packet(TYPE_SYN_ACK, 0, packet["seq"])
                self.sock.sendto(syn_ack, address)

                # ACK
                try:
                    data, _ = self.sock.recvfrom(SERVER_MSS_PROPOSE + HEADER_SIZE)
                    ack_packet = parse_packet(data)

                    if ack_packet and ack_packet["type"] == TYPE_ACK:
                        print("Connexion établie")
                        return
                except TimeoutError:
                    print("Échec du handshake")

    def ls_command(self, packet):
        cmd = packet["data"].decode()

        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
            
        files = os.listdir(SAVE_DIR)
        response = '\n'.join(files).encode()
        res_packet = build_packet(TYPE_CMD, 0, 0, response)
        self.sock.sendto(res_packet, self.client_address)
        print("réponse envoyée")

    def receive_file(self, filename: str):
        print("Réception du fichier")

        self.expected_seq = 0
        self.received.update({filename: {}})
        
        reprises = 0

        while True:
            try:
                data, address = self.sock.recvfrom(SERVER_MSS_PROPOSE + HEADER_SIZE)
            except TimeoutError:
                print(f"Timeout ({reprises})")
                reprises += 1
                if reprises >= MAX_REPRISES:
                    print("Échec")
                    return
                continue
            
            packet = parse_packet(data)

            if not packet:
                continue

            if packet["type"] == TYPE_DATA:
                reprises = 0
                seq = packet["seq"]

                if seq in self.received[filename]:
                    continue

                self.received[filename][seq] = packet["data"]

                # reset the counter and recheck, just to be sure (im paranoid now, HELP)
                self.expected_seq = 0
                while self.expected_seq in self.received[filename]:
                    self.expected_seq += 1
                    
                ack_packet = build_packet(TYPE_ACK, 0, self.expected_seq)
                self.sock.sendto(ack_packet, address)

            elif packet["type"] == TYPE_FIN:
                print("Transfère complété")
                self.save_file(filename)
                self.received.pop(filename)
                return



    def save_file(self, filename: str):
        filename_dir = os.path.join(SAVE_DIR, filename)

        with open(filename_dir, "wb") as f:
            for i in sorted(self.received[filename]):
                f.write(self.received[filename][i])

        print(f"Fichier sauvergardé sous: {filename}")
        
        
    def resume(self, filename: str):
        if filename not in self.received.keys():
            return
        # we did find the file
        for i in range(MAX_REPRISES):
            try:
                ack_packet = build_packet(TYPE_ACK, 0, 0)
                self.sock.sendto(ack_packet, address)
            except TimeoutError:
                print(f"Timeout ({i + 1})")
        
        print("Réception du fichier")

        self.expected_seq = 0
        while self.expected_seq in self.received[filename]:
            self.expected_seq += 1
        
        reprises = 0

        while True:
            try:
                data, address = self.sock.recvfrom(SERVER_MSS_PROPOSE + HEADER_SIZE)
            except TimeoutError:
                print(f"Timeout ({reprises})")
                reprises += 1
                if reprises >= MAX_REPRISES:
                    print("Échec")
                    return
                continue
            
            packet = parse_packet(data)

            if not packet:
                continue

            if packet["type"] == TYPE_DATA:
                reprises = 0
                seq = packet["seq"]

                if seq in self.received[filename]:
                    continue

                self.received[filename][seq] = packet["data"]

                # reset the counter and recheck, just to be sure (im paranoid now, HELP)
                self.expected_seq = 0
                while self.expected_seq in self.received[filename]:
                    self.expected_seq += 1
                    
                ack_packet = build_packet(TYPE_ACK, 0, self.expected_seq)
                self.sock.sendto(ack_packet, address)

            elif packet["type"] == TYPE_FIN:
                print("Transfère complété")
                self.save_file(filename)
                self.received.pop(filename)
                print("HERE: ", self.received.keys())
                return
        
        

    def run(self):
        while True:
            self.handshake()

            while True:
                try:
                    data, address = self.sock.recvfrom(CLIENT_MSS_PROPOSE + HEADER_SIZE)
                except TimeoutError:
                    #print("waiting...")
                    continue
                
                packet = parse_packet(data)

                if not packet:
                    continue

                if packet["type"] == TYPE_CMD:
                    cmd = packet["data"].decode()

                    if cmd.startswith("put"):
                        cmd = cmd.split(' ')
                        if len(cmd) != 2:
                            print("La commande reçue contient le mauvais nombre de paramètres")
                            continue
                        self.receive_file(cmd[1])
                        
                    elif cmd.startswith("resume"):
                        cmd = cmd.split(' ')
                        if len(cmd) != 2:
                            print("La commande reçue contient le mauvais nombre de paramètres")
                            continue
                        print("WHAT THE FUCK")
                        self.resume(cmd[1])
                        
                        
                    elif cmd == "ls":
                        self.ls_command(packet)

                # fin ou nouvelle demande de connexion
                # au cas ou le client crash et il faut se reconnecter
                elif packet["type"] == TYPE_FIN or packet["type"] == TYPE_SYN:
                    print("Déconnexion")
                    break

                



if __name__ == "__main__":
    server = Server()
    server.run()