#!/bin/bash

# Définir les chemins pour POSTGRES
POSTGRES_PATH="/path/to/your/postgres" # Remplacez par votre propre chemin
POSTGRES_HOST=$POSTGRES_PATH"/socket" # Remplacez par votre propre chemin
POSTGRES_DB="ldbcsnb"
POSTGRES_USER='postgres'
POSTGRES_PASSWORD='mysecretpassword'

echo "data_directory = '$POSTGRES_PATH'" >> postgresql.conf

# Initialiser la base de données
initdb -D $POSTGRES_PATH -U $POSTGRES_USER

# Créer le répertoire du socket
mkdir $POSTGRES_HOST
# Ajouter les configurations de socket au fichier postgresql.conf
echo "unix_socket_directories = '$POSTGRES_HOST'" >> postgresql.conf
echo "unix_socket_permissions = 0777" >> postgresql.conf

# Copier le fichier postgresql.conf vers le répertoire POSTGRES
cp postgresql.conf $POSTGRES_PATH/postgresql.conf

# Démarrer le serveur de base de données
pg_ctl -D $POSTGRES_PATH start

# Ajouter la ligne de confiance à pg_hba.conf
echo "host    all             all             0.0.0.0/0               trust" >> $POSTGRES_PATH/pg_hba.conf

# createdb and configure user
createdb -h $POSTGRES_HOST $POSTGRES_DB
psql -h $POSTGRES_HOST $POSTGRES_DB -c "CREATE POSTGRES_USER $POSTGRES_USER WITH password '$POSTGRES_PASSWORD';"
psql -h $POSTGRES_HOST $POSTGRES_DB -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER"

# initialise table and data
python3 -m venv postgresql-test
source postgresql-test/bin/activate
python3 -m pip install psycopg
