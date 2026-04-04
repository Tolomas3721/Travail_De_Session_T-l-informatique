from socket import AF_INET, SOCK_DGRAM
from usocket import usocket

s = usocket(
    family=AF_INET,
    type=SOCK_DGRAM,
    fiabilite=0.85,
    taux_corruption=0.05,
)

s.connect(("127.0.0.1", 4242))
s.send(b"segment 1")
reponse = s.recv(1024)
