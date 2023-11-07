# <img src="Steuerung_Versuchsstand/Raspberry/matchminimal.png" height=20>&nbsp; Masterlabor: Maschinelles Lernen in der Produktionstechnik

![MLL Coverfoto](Steuerung_Versuchsstand/Raspberry/mllcover.png)

Sammlung aller Skripte und Komponenten, welche für das [Masterlabor: Maschinelles Lernern in der Produktionstechnik](https://www.match.uni-hannover.de/de/studium/lehrveranstaltungen/masterlabor-maschinelles-lernen-in-der-produktionstechnik) am [Insitut für Montagetechnik (match)](https://www.match.uni-hannover.de/) der [Universtität Hannover (LUH)](https://www.uni-hannover.de/) genutzt werden.

## Tutorial

<center><a target="_blank" href="https://colab.research.google.com/github/match-Education/match-MLL/Programmierung/Tutorial_Skript_Programmierung_NN.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a></center>

Zur Vorbereitung auf das Labor, soll zunächst das Tutorial [Tutorial_Skript_Programmierung_NN](/Programmierung/Tutorial_Skript_Programmierung_NN.ipynb) berarbeitet werden. Dies kann auch direkt auf Google Colab geöffnet werden.

Alle weiteren Informationen können dem Skript für die Veranstaltung entnommen werden.

## Programmierung

<center><a target="_blank" href="https://colab.research.google.com/github/match-Education/match-MLL/Programmierung/Vorlage_Programmierung_NN_COLAB.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a></center>

Zur weiteren Vorbereitung auf den Versuch, ist es ebenso möglich, die Vorlage für Prorammierung bereits in Colab oder auf dem lokalen System zu nutzen.


### Verwendung von Keras Applications

Zum Vergleich verschiedener State of the Art Modelle, können [Keras Appliacations](https://keras.io/api/applications/) verwendet werden. Die ermöglichen es, eine Vielzahl unterschiedlicher Machine Learning Modelle schnell und einfach zu nutzen.

Die Verwendung ist in der Keras Dokumentation beschrieben. Es Gilt zu beachten, dass die Modelle eine jeweils spezifische Eingabegröße erwarten. Somit ist es gegenfalls notwendig, die Bilder des Datensatzes entsprechend zu resizen. Die gewünschten Dimensionne können mit Hilfe der `model.summary()` ermittelt werden:

```
Model: "resnet101v2"
__________________________________________________________________________________________________
 Layer (type)                Output Shape                 Param #   Connected to                  
==================================================================================================
 input_1 (InputLayer)        [(None, 224, 224, 3)]        0         []                            
```
Beispiel: Die Output Shape der Input Layer von ResNet101v2 entspricht den Datendimensionen, welche das Modell erwartet. Also 224x224 Pixel bei 3 Farbkanälen. Im Falle von Graustufen Bildern, ist es also dennoch notwendig, drei gleiche Kanäle an das Modell zu übergeben.

## Versuchsstand

Die folgende Dokumenation richtet sich primär an die Betreur*innen des Labors. Sie kann jedoch auch für die persönliche Verwendung genutzt werden, etwa bei der vertiefenden wissenschaftlichen Arbeit mit künstlichen neuronalen Netzen.

Der systematische Aufbau des Versuchsstandes ist in der der folgenden Abbildung dargestellt:

![Alt text](Steuerung_Versuchsstand/Raspberry/mllarchitecture.png)

### Remote Serving

Es existieren viele untetrschiedliche Möglichkeiten um fertig trainierte Modelle im produktiven Betrieb zu nutzen. Häufig werden hierzu Services wie etwa [Amazon SakeMaker](https://aws.amazon.com/de/sagemaker/) genutzt.

[TensorFlow Serving](https://github.com/tensorflow/serving) bietet eine weitere Möglichkeit Machine Learning Modelle mit relativ geringem Aufwand auf einer Vielzahl unterschiedlichster System zu deployen. Im Rahmen des MLL wird TensorFlow Serving verwendet um die trainierten Netze auf einem leistungsstarken Computer zur Verfügung zu stellen. Mit Hilfe der bereitgestellten [RestAPI](https://www.tensorflow.org/tfx/serving/api_rest) können Anfragen für die Objekterkennung vom Raspberry Pi aus gemacht werden.

#### Anlegen der .credentials Datei
In order to use the [mountshare.sh](/Steuerung_Versuchsstand/Serving/mountshare.sh), [runserving.sh](/Steuerung_Versuchsstand/Serving/runserving.sh) and [mllapi.py](/Steuerung_Versuchsstand/Serving/mllapi.py) script, a file named ".credentials" must exist in the same folder. As this file contains secrets, is must be manually edited from the [.credentials_template](/Steuerung_Versuchsstand/Serving/.credentials_template):

```bash
# .credentials - CIFS Mount Configuration

# CIFS server address or IP
server="server_address_or_ip"

# Name of the CIFS share
share="share_name"

# Local mount point directory
mount_point="/mnt/cifs"

# CIFS username for authentication
username="your_username"

# CIFS password for authentication
password="your_password"
```

Edit the template file and save it as '.credentials'. For example `mv .credentials_template .credentials` and then `nano .credentials` and edit the variables.

#### Install Flask

In order to use the [mllapi.py](/Steuerung_Versuchsstand/Serving/mllapi.py) Flask must be installed in the desired python environment:

```bash
pip install Flask
```

#### Install Docker

To run the TensorFlow Serving Container, the Docker Engine must be installed as per the [Docker Engine install instructions](https://docs.docker.com/engine/install/). Once installed, further [Post-installation Steps](https://docs.docker.com/engine/install/linux-postinstall/) should be done to ensure docker works as intended.

To verify, that the docker installation was successfull, run the following commands, to launch a TensorFlow Serving Container:

```bash
# Download the TensorFlow Serving Docker image and repo
docker pull tensorflow/serving

git clone https://github.com/tensorflow/serving
# Location of demo models
TESTDATA="$(pwd)/serving/tensorflow_serving/servables/tensorflow/testdata"

# Start TensorFlow Serving container and open the REST API port
docker run -t --rm -p 8501:8501 \
    -v "$TESTDATA/saved_model_half_plus_two_cpu:/models/half_plus_two" \
    -e MODEL_NAME=half_plus_two \
    tensorflow/serving &

# Query the model using the predict API
curl -d '{"instances": [1.0, 2.0, 5.0]}' \
    -X POST http://localhost:8501/v1/models/half_plus_two:predict

# Returns => { "predictions": [2.5, 3.0, 4.5] }
```

### mllapi.py

Die [mllapi.py](/Steuerung_Versuchsstand/Serving/mllapi.py) stetllt einen Flask-Webserver zur Verfügung, welcher die folgenden Dienste anbietet:

- GET ***/create_config***: Erstellt, basierend auf den Inhalten des Netze Ordners, eine Konfigurationsdatei. Diese wird verwendet um den TensorFlow Serving Docker Container zu starten. Dieser Dienste sollte einmal ausgeführt werden, bevor der TensorFlow Serving Container gestartet wird, bei dem Hinzufügen weitere Netze, ist dies erneut notwendig.
  
- GET ***/get_models***: Gibt eine Liste der Modelle aus, welche der TensorFlow Serving Docker Container bereitstellt. Findet Verwendung in dem Tkinter GUI für die Sortierung.

Es ist möglich die Dienste auch manuell zu nutzen, etwa in einem Browser oder mit Hilfe von curl:

```bash
curl http://HOSTNAME/get_models
```

### Raspberry GUIs

#### Installtion notweniger Python Pakete mit PIP

In den entsprechen Order wechseln und anschließend alle Pakete aus der [`requirements.txt`](/Steuerung_Versuchsstand/Raspberry/requirements.txt) installieren:

```bash
# chance directory
cd Steuerung_Versuchsstand/Raspberry/

# use pip to install from file
pip install -r requirements.txt
```


Anschließend sollte [`sortierung.py`](/Steuerung_Versuchsstand/Raspberry/sortierung.py) und [`datensatzaufnahme.py`](/Steuerung_Versuchsstand/Raspberry/datensatzaufnahme.py) verwendet werden können. Eventuell müssen diese jedoch noch mit `chmod` ausführbar gemacht werden (`chmod +x sortierung.py`) und gestartet werden können (`./sortierung.py`). Alterantiv können diese wie gewohnt mit dem `python` Befehl gestartet werden (`python sortierung.py`). Zur schnellen Verwendung, sind weiterhin zwei Shortcuts zur Verfügung gestellt, welche ggf. leicht angepasst werden müssen.


## Roadmap
- [x] TensorFlow Serving implementieren
- [ ] Übergabe von korrekten Labels bei Verwendung von Remote Serving
- [ ] Alternative Implementierung PyTorch
## License

[MIT](https://choosealicense.com/licenses/mit/)