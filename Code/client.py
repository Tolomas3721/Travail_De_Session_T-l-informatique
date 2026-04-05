import socket 


# terminer la connexion
def bye_command():
    pass

# initie la connexion avec le port choisi
def open_command(port: str):
    pass

# retourne la liste des fichiers disponibles sur le serveur
def ls_command():
    pass

# téléverse le fichier choisi vers le serveur
def put_command(path: str):
    pass


def checksum_validation():
    pass



if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 4242))

    client.send('Hello from client'.encode())
    print(client.recv(1024))
    