# Travail_De_Session_T-l-informatique


comment lancer le serveur:
1. ouvrez un terminal de commande (cmd)
2. lancez server.py avec la commande "./server.py" (sans les guiellemets)


comment lancer le client:
1. ouvrez un second terminal de commande (cmd)
2. lancez client.py avec la commande "./client.py" (sans les guillemets)

comment exécuter un transfert:
1. connectez vous au serveur avec la commande client "open 127.0.0.1" (sans les guillemets)
    le serveur écoute automatiquement le port 4242 à l'adresse locale 127.0.0.1
2. utilisez la commande "put"  
    "put dir/to/file/nom_de_fichier" (sans les guillemets)
3. attendre le transfère
4. en cas d'erreur, il est possible de réessayer le transfère à partir de là où l'erreure est survenue avec la commande
    "resume" qui prend en argument le nom du fichier a transférer de la même façon que "put"
    "resume dir/to/file/nom_de_fichier" (sans les guillemets)
5. reprendre à partir de 3 jusqu'à un transfère complété

comment vérifier l’intégrité finale du fichier:
1. les fichiers transférés sont mis dans le dossier "sauvegardes"