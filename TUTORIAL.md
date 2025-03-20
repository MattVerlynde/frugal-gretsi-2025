# Configuration pour le suivi de la consommation d'énergie

Cette page résume la procédure d'installation du pipeline de lecture, d'écriture, de stockage et de visualisation des données d'utilisation matérielle interne. Ce travail est basé sur le pipeline **Telegraf-InfluxDB-Grafana** (TIG). Il est largement inspiré du tutoriel disponible en ligne à l'adresse [https://domopi.eu/tig-le-trio-telegraf-influxdb-grafana-pour-surveiller-vos-equipements/](https://domopi.eu/tig-le-trio-telegraf-influxdb-grafana-pour-surveiller-vos-equipements/).
Ce guide présente également la procédure d'interrogation de la base de données **InfluxDB** après l'exécution d'un script Python à l'aide d'un script bash.

__*English version [here](https://github.com/MattVerlynde/performance-tracking/blob/main/config/README.md)*__

#### Table des matières

- [Présentation du pipeline](#pipeline)
- [Configuration TIG](#tig-config)
  - [Installation](#tig-install)
  - [Configuration de Grafana](#grafana-config)
  - [Interrogation de la base de données](#db-interro)
- [Suivi de la consommation d'énergie](#energy)
  - [Installation de la prise](#plug-install)
  - [Configuration vers InfluxDB](#influx-connect)
- [Erreurs possibles](#errors)

<!--more-->

## Présentation du pipeline <a name="pipeline"></a>

Le plugin Telegraf, produit par InfluxDB, permet la collecte en direct des données d'utilisation matérielle et leur formatage. Le plugin ZWave-JS UI collecte les données d'une prise connectée et les transfère à Telegraf à l'aide du plugin Mosquitto.
InfluxDB stocke les données au format de séries temporelles et forme la base de données interrogée dans le pipeline ; Grafana est un outil de visualisation et d'analyse des données utilisé avec la base de données InfluxDB.

![Pipeline final](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/pipeline.png)

## Configuration TIG <a name="tig-config"></a>

### Installation <a name="tig-install"></a>

> Ce tutoriel se concentre sur l'installation du pipeline à l'aide de Docker et dépend de son installation préalable.

Nous commençons par télécharger les images Docker des trois plugins du pipeline.

```shell
docker pull telegraf
docker pull influxdb
docker pull grafana/grafana-oss
```
Nous utiliserons la commande `docker compose` pour construire notre pipeline. Nous utilisons un fichier de construction `docker-compose.yml` après avoir choisi un port d'entrée pour Grafana. Pour cet exemple, nous choisissons le port `9090`.

```yaml
version: "3.8"
services:
  influxdb:
    image: influxdb
    container_name: influxdb
    restart: always
    ports:
      - 8086:8086
    hostname: influxdb
    environment:
      INFLUX_DB: $INFLUX_DB  # nom de la base de données
      INFLUXDB_USER: $INFLUXDB_USER  # nom d'utilisateur
      INFLUXDB_USER_PASSWORD: $INFLUXDB_USER_PASSWORD  # mot de passe utilisateur
      DOCKER_INFLUXDB_INIT_MODE: $DOCKER_INFLUXDB_INIT_MODE
      DOCKER_INFLUXDB_INIT_USERNAME: $DOCKER_INFLUXDB_INIT_USERNAME
      DOCKER_INFLUXDB_INIT_PASSWORD: $DOCKER_INFLUXDB_INIT_PASSWORD
      DOCKER_INFLUXDB_INIT_ORG: $DOCKER_INFLUXDB_INIT_ORG
      DOCKER_INFLUXDB_INIT_BUCKET: $DOCKER_INFLUXDB_INIT_BUCKET
      DOCKER_INFLUXDB_INIT_RETENTION: $DOCKER_INFLUXDB_INIT_RETENTION
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: $DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
    volumes:
      - ./influxdb:/var/lib/influxdb  # volume pour stocker la base de données InfluxDB

  telegraf:
    image: telegraf
    depends_on:
      - influxdb  # indique qu'influxdb est nécessaire
    container_name: telegraf
    restart: always
    links:
      - influxdb:influxdb
    tty: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # nécessaire pour récupérer les données du démon Docker
      - ./telegraf/telegraf.conf:/etc/telegraf/telegraf.conf  # fichier de configuration pour Telegraf
      - /:/host:ro # nécessaire pour récupérer les données de l'hôte (processus, threads...)

  grafana:
    image: grafana/grafana-oss
    depends_on:
      - influxdb  # indique qu'influxdb est nécessaire
    container_name: grafana
    restart: always
    ports:
      - 9090:3000  # port pour accéder à l'interface web de Grafana
    links:
      - influxdb:influxdb
    environment:
      GF_INSTALL_PLUGINS: "grafana-clock-panel,\
                          grafana-influxdb-08-datasource,\
                          grafana-kairosdb-datasource,\
                          grafana-piechart-panel,\
                          grafana-simple-json-datasource,\
                          grafana-worldmap-panel"
      GF_SECURITY_ADMIN_USER: $GF_SECURITY_ADMIN_USER  # nom d'utilisateur pour Grafana
      GF_SECURITY_ADMIN_PASSWORD: $GF_SECURITY_ADMIN_PASSWORD  # mot de passe utilisateur pour Grafana
    volumes:
      - ./grafana:/var/lib/grafana-oss
```

> Ce fichier est disponible à l'adresse : [tig/docker-compose.yml](https://github.com/MattVerlynde/performance-tracking/blob/main/config/tig/docker-compose.yml).

Ce fichier est construit avec un fichier dépendant contenant des variables d'environnement. Nous construisons ce fichier `.env` avec les valeurs des variables dans le même répertoire.

```yaml
INFLUX_DB=telegraf
INFLUXDB_USER=telegraf_user
INFLUXDB_USER_PASSWORD=telegraf_password
GF_SECURITY_ADMIN_USER=grafana_user
GF_SECURITY_ADMIN_PASSWORD=grafana_password
DOCKER_INFLUXDB_INIT_MODE=setup
DOCKER_INFLUXDB_INIT_USERNAME=telegraf_user
DOCKER_INFLUXDB_INIT_PASSWORD=telegraf_password
DOCKER_INFLUXDB_INIT_ORG=telegraf_org
DOCKER_INFLUXDB_INIT_BUCKET=telegraf_bucket
DOCKER_INFLUXDB_INIT_RETENTION=365d
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=telegraf_token
```

> Ce fichier est disponible à l'adresse : [tig/.env](https://github.com/MattVerlynde/performance-tracking/blob/main/config/tig/.env).

Nous configurons maintenant les paramètres pour Telegraf. Dans le shell bash, exécutez les lignes suivantes :

```shell
mkdir telegraf
docker run --rm telegraf telegraf config > telegraf/telegraf.conf
```

Cette commande a créé le fichier de configuration par défaut de Telegraf, que nous modifions pour notre projet.

```squidconf

# Configuration pour l'agent telegraf
[agent]

  [...]

  ## Remplacer le nom d'hôte par défaut, si vide utiliser os.Hostname()
  hostname = "telegraf"
  ## Si défini sur true, ne pas définir la balise "host" dans l'agent telegraf.
  omit_hostname = false

[...]

###############################################################################
#                            PLUGINS DE SORTIE                                   #
###############################################################################

# # Configuration pour l'envoi de métriques vers InfluxDB 2.0
[[outputs.influxdb_v2]]
#   ## Les URL des nœuds du cluster InfluxDB.
#   ##
#   ## Plusieurs URL peuvent être spécifiées pour un seul cluster, une seule des
#   ## urls sera écrite à chaque intervalle.
#   ##   ex: urls = ["https://us-west-2-1.aws.cloud2.influxdata.com"]
   urls = ["http://influxdb:8086"]
#
#   ## Jeton pour l'authentification.
   token = "telegraf_token"
#
#   ## Organisation est le nom de l'organisation dans laquelle vous souhaitez écrire.
   organization = "telegraf_org"
#
#   ## Bucket de destination pour écrire.
   bucket = "telegraf_bucket"

   [...]

[...]

[[outputs.influxdb]]
#   ## L'URL HTTP ou UDP complète pour votre instance InfluxDB.
#   ##
#   ## Plusieurs URL peuvent être spécifiées pour un seul cluster, une seule des
#   ## urls sera écrite à chaque intervalle.
#   # urls = ["unix:///var/run/influxdb.sock"]
#   # urls = ["udp://127.0.0.1:8089"]
#   # urls = ["http://127.0.0.1:8086"]
   urls = ["http://influxdb:8086"]

   [...]

#   ## Authentification HTTP de base
   username = "telegraf_user"
   password = "telegraf_password"

   [...]

[...]

[[inputs.docker]]
#   ## Point de terminaison Docker
#   ##   Pour utiliser TCP, définir endpoint = "tcp://[ip]:[port]"
#   ##   Pour utiliser les variables d'environnement (par exemple, docker-machine), définir endpoint = "ENV"
   endpoint = "unix:///var/run/docker.sock"

   [...]

[...]

# # Surveiller l'utilisation du CPU et de la mémoire des processus
[[inputs.procstat]]
   pattern = ".*"
   fieldpass = ["cpu_time_system", "cpu_time_user", "cpu_usage", "memory_*", "num_threads", "*pid"]
   pid_finder = "native"
   pid_tag = true

   [...]

[...]

# # Lire les métriques sur la température
[[inputs.temp]]

[...]

```
Appliquez ces modifications :
* Dans `[agent]`, la variable `hostname` avec la valeur de la variable d'environnement `INFLUX_DB`, ici `"telegraf"`

* Décommentez `[[outputs.influxdb_v2]]`, définissez `urls` avec `["http://influxdb:8086"]`, et définissez `token`, `organization` et `bucket` avec les variables d'environnement `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN`, `DOCKER_INFLUXDB_INIT_ORG` et `DOCKER_INFLUXDB_INIT_BUCKET`, ici `"telegraf_token"`, `"telegraf_org"` et `"telegraf_bucket"`.

* Commentez `[[outputs.file]]`. Nous n'avons pas besoin d'un fichier de sauvegarde dans Telegraf avec InfluxDB.

* Décommentez `[[outputs.influxdb]]`, définissez `urls` avec `["http://influxdb:8086"]`, et définissez `username` et `password` avec les variables d'environnement `DOCKER_INFLUXDB_INIT_USERNAME` et `DOCKER_INFLUXDB_INIT_PASSWORD`, ici `"telegraf_user"` et `"telegraf_password"`.

* Décommentez `[[inputs.docker]]`, définissez `endpoint` avec `"unix:///var/run/docker.sock"`.

* Décommentez `[[inputs.procstat]]`, définissez `pattern` avec `".*"` pour récupérer les données de chaque processus, définissez `fieldpass` avec nos variables d'intérêt, ici `["cpu_time_system", "cpu_time_user", "cpu_usage", "memory_*", "num_threads", "*pid"]`, définissez `pid_finder` avec `"native"` pour accéder aux données de l'hôte depuis l'extérieur du conteneur, et définissez `pid_tag` avec `true` pour conserver les identifiants des processus,

* Décommentez `[[inputs.temp]]` pour récupérer les données de température du CPU et du NVME.

> Ce fichier est disponible à l'adresse : [tig/telegraf/telegraf.conf](https://github.com/MattVerlynde/performance-tracking/blob/main/config/tig/telegraf/telegraf.conf).

Nous pouvons ensuite créer les conteneurs.

```shell
docker compose up -d
```

Vérifiez que les conteneurs ont été créés avec la commande suivante :

```shell
docker ps
```

Si les conteneurs ont été créés, nous pouvons accéder à l'interface Grafana sur le port choisi, ici à `http://localhost:9090`.

> Nous pouvons également accéder à l'interface InfluxDB sur le port choisi dans le fichier `docker-compose.yml`, ici à `http://localhost:8086`.

Nous pouvons ensuite configurer Grafana.

### Configuration de Grafana <a name="grafana-config"></a>

Sur la page d'accueil de Grafana, connectez-vous en utilisant le nom d'utilisateur et le mot de passe utilisés dans le fichier `.env`. Dans cet exemple, `grafana_user` et `grafana_password`.

![Page d'accueil de Grafana](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_welcome.png)

Configurez la source de données et choisissez InfluxDB comme type de source.

![Sélectionner la source de données (InfluxDB)](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_select_influx.png)

Configurez la source de données avec le port InfluxDB et sélectionnez `FLUX` comme langage d'interrogation de la base de données.

![Sélectionner le nom et le port](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_set_datasource1.png)

Ajoutez les identifiants de connexion à la base de données avec ceux de c.

![Ajout des identifiants](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_set_datasource2.png)

Importez un tableau de bord de visualisation compatible avec notre configuration. Nous pouvons en choisir un en ligne, mais celui avec l'identifiant `15650` est bien adapté pour cet exemple.

![Importation du tableau de bord](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_import_dashb1.png)

Choisissez la source configurée avant l'importation.

![Sélection de la source](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_import_dashb2.png)

Enfin, choisissez les paramètres du tableau de bord pour nos données, ici le nom du bucket que nous avons configuré dans le fichier `.env`.

![Sélection des paramètres](https://github.com/MattVerlynde/performance-tracking/blob/main/config/screenshots_config/grafana_import_dashb3.png)

Nous pouvons ensuite modifier notre tableau de bord selon nos préférences, en choisissant différents paramètres ou requêtes (en langage [FLUX](https://docs.influxdata.com/influxdb/cloud/query-data/get-started/query-influxdb/)).

Une autre possibilité consiste à importer le tableau de bord à partir d'un fichier `.json`. Le fichier configuré pour ce projet est disponible à l'adresse : [grafana_dashboard_template.json](https://github.com/MattVerlynde/performance-tracking/blob/main/config/grafana_dashboard_template.json).

### Interrogation de la base de données <a name="db-interro"></a>

Pour interroger la base de données **InfluxDB** précédemment créée, nous utilisons un script bash exécutant un script Python en argument. Nous interrogeons ensuite la base de données pour collecter les données insérées pendant le temps d'exécution du script Python.

> Ce fichier est disponible à l'adresse : [get_metrics.sh](https://github.com/MattVerlynde/performance-tracking/blob/main/config/get_metrics.sh).

Ce fichier est exécuté comme suit :

```bash
bash get_metrics.sh -f [python.file] (-p) (-P [pid])
```
* l'indicateur `-f` est requis et précède le nom du fichier Python à exécuter,
* l'indicateur `-P` est optionnel : s'il est utilisé, les données collectées sont celles associées au processus avec l'identifiant dans le fichier `python_process.pid` pendant le temps d'exécution du script Python,
* l'indicateur `-p` est optionnel : s'il est utilisé, les données collectées sont celles associées au processus avec l'identifiant suivant l'indicateur dans la commande,
* si les indicateurs `-p` et `-P` ne sont pas utilisés, les données de tous les processus sont collectées.

Les données collectées sont sauvegardées dans un fichier `metrics_output`.

Le fichier de collecte `get_metrics.sh` est organisé comme suit :

```bash
#!/bin/bash

# Collecte des arguments d'entrée
while getopts 'f:p:P:' OPTION; do
  case "$OPTION" in
    f)
      name_file="$OPTARG"
      ;;
    P)
      by_pid=true
      get_pid=true
      ;;
    p)
      by_pid=true
      get_pid=false
      npid="$OPTARG"
      ;;
    \?)
      echo "Option invalide : $OPTARG" 1>&2
      exit 1
      ;;
  esac
done
: ${name_file:?Missing -f}

# Heure de début d'exécution
t1=$(date -u +%Y-%m-%dT%T.%9NZ)
echo "*************************************************"
echo "Heure de début : $t1"
echo "*************************************************"
echo "Exécution du script Python : $name_file"
echo "*************************************************"

# Exécution du script Python choisi
python3 $name_file

# Heure de fin d'exécution
t2=$(date -u +%Y-%m-%dT%T.%9NZ)

echo "*************************************************"
echo "Heure de fin : $t2"
echo "*************************************************"

if [ "$by_pid" = true ]; then
  if [ "$get_pid" = true ]; then
    # Collecte de l'identifiant du processus s'il n'est pas dans les arguments d'entrée
    npid=$(cat python_process.pid)
  fi
  echo "Identifiant du processus : ${npid}"
  # Construction de la requête du processus
  query="data=from(bucket: \"telegraf_bucket\")
    |> range(start: ${t1}, stop: ${t2})
    |> filter(fn: (r) => r[\"_measurement\"] == \"procstat\")
    |> filter(fn: (r) => r[\"pid\"] == \"${npid}\")
    |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
    |> yield(name: \"mean\")"
else
  # Construction de la requête de toutes les données
  query="data=from(bucket: \"telegraf_bucket\")
    |> range(start: ${t1}, stop: ${t2})
    |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
    |> yield(name: \"mean\")"
fi

# Écriture de la requête
echo $query > query

# Copie de la requête dans le conteneur InfluxDB
sudo docker cp query influxdb:/query

# Exécution de la requête dans le conteneur et exportation de la sortie dans metrics_output
sudo docker exec -it influxdb sh -c 'influx query -f query -r' > metrics_output

echo "*************************************************"
echo "Fichier metrics_output créé"
echo "*************************************************"
head metrics_output
echo "*************************************************"
```

Format de la sortie dans `metrics_output` :

```text
#group,false,false,true,true,false,false,true,true,true,true,true,true

#datatype,string,long,dateTime:RFC3339,dateTime:RFC3339,dateTime:RFC3339,double,string,string,string,string,string,string

#default,mean,,,,,,,,,,,

,result,table,_start,_stop,_time,_value,_field,_measurement,host,pattern,pid,process_name

,,0,2024-03-27T16:15:21.073488201Z,2024-03-27T16:15:57.890192557Z,2024-03-27T16:15:31Z,6.46,cpu_time_system,procstat,telegraf,.*,1601463,python3

,,0,2024-03-27T16:15:21.073488201Z,2024-03-27T16:15:57.890192557Z,2024-03-27T16:15:41Z,6.87,cpu_time_system,procstat,telegraf,.*,1601463,python3

,,0,2024-03-27T16:15:21.073488201Z,2024-03-27T16:15:57.890192557Z,2024-03-27T16:15:51Z,7.46,cpu_time_system,procstat,telegraf,.*,1601463,python3

[...]
```

## Suivi de la consommation d'énergie <a name="energy"></a>

Une fois le pipeline TIG configuré, nous allons introduire la prise connectée pour collecter des informations sur la consommation d'énergie.

Prise Smart Switch 7 Aeotec &reg; | Contrôleur Z Stick 7 Aeotec &reg;
:-------------------------:|:-------------------------:
[<img src="smart-switch/smartswitch7.jpg" height="250"/>](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/smartswitch7.jpg)  |  [<img src="smart-switch/zstick7.jpg" height="250"/>](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/zstick7.jpg)

### Installation de la prise <a name="plug-install"></a>

Création du conteneur Docker pour l'application Home Assistant (tableau de bord spécifique optimisé pour Z-Wave) :

```bash
sudo docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Europe/Paris \
  -v ~/homeassistant:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

Création du répertoire avec les configurations Z-Wave :

```bash
cd homeassistant
mkdir docker
mkdir docker/zwave-js
```

Récupération du nom du réseau dans lequel Telegraf est installé :

```bash
sudo docker inspect telegraf -f '{{range $k, $v := .NetworkSettings.Networks}}{{printf "%s\n" $k}}{{end}}'
```

Récupération du nom du contrôleur USB :

```bash
dmesg | grep tty
```

Création du conteneur Docker pour l'application Z-Wave JS :

```bash
sudo docker run -d \
  --network [TELEGRAF_NETWORK] \
  --restart=always \
  -p 8091:8091 \
  -p 3002:3000 \
  --device=[USB_CONTROLLER] \
  --name="zwave-js" \
  -e "TZ=Europe/Paris" \
  -v ~/homeassistant/docker/zwave-js:/usr/src/app/store zwavejs/zwavejs2mqtt:latest
```

Configuration de Z-Wave JS sur le port choisi :

Pour configurer Z-Wave JS afin de collecter des données à partir de la prise connectée, nous accédons à son interface sur la page `Smart Start`, ici à `http://localhost:8091`.

![Smart Start](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/smart-start.png)

Ajoutez les informations du dispositif Smart Switch, en utilisant le bouton `Add`, et ajoutez le code DSK de la prise connectée (écrit sur l'emballage) et activez tous les systèmes de sécurité.

![Nouvelle entrée](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/new-entry.png)

Une fois la prise ajoutée, configurez les paramètres de l'application. Sur la page `Settings`, à `Z-Wave`, ajoutez le nom du contrôleur USB précédemment identifié.

Vérifiez que l'enregistrement des statistiques est activé.

![Activer les statistiques](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/enable-stats.png)

Enfin, dans `Home Assistant`, ajoutez l'adresse IP du conteneur Z-Wave en tant qu'hôte. Cette adresse peut être trouvée en utilisant la commande `docker sudo docker inspect --format '{{ .NetworkSettings.IPAddress }}' zwave-js` dans le shell. Nous pouvons également modifier le port selon nos préférences.

![Configurer Home Assistant](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/config-homeassist.png)

Maintenant que Z-Wave JS est configuré, nous accédons à l'interface Home Assistant, ici à `http://localhost:8123`. Commencez par créer un compte en suivant le guide affiché sur cette interface.
Une fois le compte créé, ajoutez le dispositif d'intérêt.

Sur la page `Settings`, allez dans `Devices & services`.
![Ajouter un appareil](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/add-device-ha.png)

Ajoutez une intégration Z-Wave en utilisant `Add integration` et en sélectionnant `Z-Wave`. Ajoutez l'adresse de la configuration Z-Wave JS au format `ws://[IP du conteneur zwave-js]:[port configuré]`.

Sélectionnez le dispositif Smart Switch 7, il est maintenant ajouté. Les premières acquisitions de la prise sont maintenant visibles, et nous pouvons créer un tableau de bord si nous le souhaitons.
![Obtenir les premières données](https://github.com/MattVerlynde/performance-tracking/blob/main/config/smart-switch/first-data.png)

### Connexion à InfluxDB <a name="influx-connect"></a>

```sh
pid_file /var/run/mosquitto.pid

persistence true
persistence_location /mosquitto/data/

log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

password_file /mosquitto/config/mosquitto.passwd
allow_anonymous false
```

```bash
sudo docker run -d \
  --network [TELEGRAF_NETWORK] \
  --restart=always \
  -p 1883:1883 \
  --name="mosquitto" \
  -v ~/homeassistant/docker/mqtt:/mosquitto eclipse-mosquitto:1.6.15
```

```bash
sudo docker exec -it mosquitto sh
```

```bash
mosquitto_passwd -c mosquitto/config/mosquitto.passwd [user]
[password]
```

```squidconf
# # Lire les métriques à partir du ou des sujets MQTT
[[inputs.mqtt_consumer]]
#   ## URL des serveurs pour le serveur ou le cluster MQTT. Pour se connecter à plusieurs
#   ## clusters ou serveurs autonomes, utilisez une instance de plugin distincte.
#   ##   exemple: servers = ["tcp://localhost:1883"]
#   ##            servers = ["ssl://localhost:1883"]
#   ##            servers = ["ws://localhost:1883"]
   servers = ["tcp://mosquitto:1883"]
#
#   ## Sujets qui seront abonnés.
   topics = [
     "zwave/Smart_switch_PC/50/0/value/65537",
     "zwave/Smart_switch_PC/50/0/value/66049",
     "zwave/Smart_switch_PC/50/0/value/66561",
     "zwave/Smart_switch_PC/50/0/value/66817",
   ]
#
#   ## Le sujet du message sera stocké dans une balise spécifiée par cette valeur. Si défini
#   ## sur une chaîne vide, aucune balise de sujet ne sera créée.
#   # topic_tag = "topic"
#
#   ## Politique QoS pour les messages
#   ##   0 = au plus une fois
#   ##   1 = au moins une fois
#   ##   2 = exactement une fois
#   ##
#   ## Lors de l'utilisation d'un QoS de 1 ou 2, vous devez activer persistent_session pour permettre
#   ## la reprise des messages non accusés de réception.
#   # qos = 0
#
#   ## Délai de connexion initiale en secondes
connection_timeout = "60s"
#
#   ## Messages non distribués maximum
#   ## Ce plugin utilise des métriques de suivi, qui garantissent que les messages sont lus vers
#   ## les sorties avant d'être accusés de réception au broker d'origine pour garantir que les données
#   ## ne sont pas perdues. Cette option définit le nombre maximum de messages à lire à partir du
#   ## broker qui n'ont pas été écrits par une sortie.
#   ##
#   ## Cette valeur doit être choisie en tenant compte de la valeur metric_batch_size de l'agent.
#   ## Définir un nombre maximum de messages non distribués trop élevé peut entraîner un flux constant
#   ## de lots de données vers la sortie. Tandis que le définir trop bas peut ne jamais vider les messages du broker.
#   # max_undelivered_messages = 1000
#
#   ## Session persistante désactive la suppression de la session client à la connexion.
#   ## Pour que cette option fonctionne, vous devez également définir client_id pour identifier
#   ## le client. Pour recevoir des messages arrivés pendant que le client est hors ligne,
#   ## définissez également l'option qos sur 1 ou 2 et n'oubliez pas de définir également le QoS lors
#   ## de la publication. Enfin, l'utilisation d'une session persistante utilisera les sujets de connexion initiaux et
#   ## ne s'abonnera à aucun nouveau sujet même après reconnexion ou redémarrage sans changement d'identifiant client.
#   # persistent_session = false
#
#   ## Si non défini, un identifiant client aléatoire sera généré.
client_id = "telegraf"
#
#   ## Nom d'utilisateur et mot de passe pour se connecter au serveur MQTT.
username="********"
password="********"
#
#   ## Configuration TLS facultative
#   # tls_ca = "/etc/telegraf/ca.pem"
#   # tls_cert = "/etc/telegraf/cert.pem"
#   # tls_key = "/etc/telegraf/key.pem"
#   ## Utiliser TLS mais ignorer la vérification de la chaîne et de l'hôte
#   # insecure_skip_verify = false
#
#   ## Messages de trace du client
#   ## Lorsqu'il est défini sur true, et que le mode debug est activé dans les paramètres de l'agent, les messages du
#   ## client MQTT sont inclus dans les journaux de Telegraf. Ces messages sont très bruités, mais essentiels pour le débogage des problèmes.
client_trace = true
#
#   ## Format de données à consommer.
#   ## Chaque format de données a son propre ensemble d'options de configuration uniques, lisez
#   ## plus à leur sujet ici :
#   ## https://github.com/influxdata/telegraf/blob/master/docs/DATA_FORMATS_INPUT.md
   data_format = "json"
   interval = "60s"
#
#   ## Activer l'extraction des valeurs de balise à partir des sujets MQTT
#   ## _ indique une entrée ignorée dans le chemin du sujet
#   # [[inputs.mqtt_consumer.topic_parsing]]
#   #   topic = ""
#   #   measurement = ""
#   #   tags = ""
#   #   fields = ""
#   ## Valeur prise en charge : int, float, unit
#   #   [[inputs.mqtt_consumer.topic.types]]
#   #      key = type
```

## Erreurs possibles <a name="errors"></a>

Lorsqu'il y a un arrêt complet du serveur, les adresses IP des conteneurs Docker peuvent changer. Cela ne devrait pas poser de problème pour le pipeline, sauf pour Home Assistant.
Pour reconnecter HomeAssistant :

  * Récupérez l'adresse IP du conteneur de l'interface utilisateur ZWave-JS en utilisant la commande : ```sudo docker inspect --format '{{ .NetworkSettings.Networks.tig_default.IPAddress }}' zwave-js```

  * Reconnectez HomeAssistant au pipeline avec cette adresse IP en suivant les étapes précédentes.

Lorsqu'il y a un arrêt de la prise connectée, la fréquence de collecte des données peut changer. Pour choisir la fréquence :

  * Allez sur l'interface ZWave-JS UI (ici `http://localhost:8091/`) sur le `Control panel`,

  * Sur le nœud associé à la prise, dans `Values`, allez dans `Configuration v1`,

  * Définissez l'`Automatic Reporting Interval` selon vos préférences (**Attention**, la valeur minimale est de 30 secondes).