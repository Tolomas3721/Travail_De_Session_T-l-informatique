import configparser
import struct
import zlib


config = configparser.ConfigParser()
config.read("Code/config.ini")

# TODO: mieux dutiliser getfloat ou getint, dumbass
TIMEOUT = float(config["RESEAU"]["timeout"])
WINDOW_SIZE = int(config["CONNEXION"]["n_propose"])

SERVER_PORT = 4242
FIABILITE = float(config["RESEAU"]["fiabilite"])
MAX_REPRISES = int(config["RESEAU"]["max_reprises"])
TAUX_CORRUPTION = float(config["RESEAU"]["taux_corruption"])

# pas sur ce qui est utile de load ici, donc je load tout lol
CLIENT_MSS_PROPOSE = int(config["CONNEXION"]["client_mss_propose"])
SERVER_MSS_PROPOSE = int(config["CONNEXION"]["serveur_mss_propose"])



SAVE_DIR = "./sauvegardes"

HEADER_FMT = "!BBIIHI"
HEADER_SIZE = struct.calcsize(HEADER_FMT)

VERSION = 1

TYPE_SYN = 1
TYPE_SYN_ACK = 2
TYPE_ACK = 3
TYPE_DATA = 4
TYPE_FIN = 5
TYPE_CMD = 6



def checksum(data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff


def build_packet(msg_type, seq, ack, data=b""):
    data_len = len(data)
    chk = checksum(data)
    header = struct.pack(HEADER_FMT, VERSION, msg_type, seq, ack, data_len, chk)
    return header + data


def parse_packet(packet: bytes):
    header = packet[:HEADER_SIZE]
    data = packet[HEADER_SIZE:]

    version, msg_type, seq, ack, data_len, chk = struct.unpack(HEADER_FMT, header)

    if checksum(data) != chk:
        return None  # TODO: corrompu

    return {
        "type": msg_type,
        "seq": seq,
        "ack": ack,
        "data": data
    }