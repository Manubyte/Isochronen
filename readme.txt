In den readme wird erklärt:
    1) Wie das Skript laufen gelassen werden kann und Parameter eingestellt werden können.
    2) Wie Startpunkte erstellt werden können.
    3) Wie die Ergebnisisochronen zusammengefasst werden können.


1) --- Laufenlassen des Skriptes und ändern der Parameter ---

Um ein Durchlaufen des Skriptes zu garantieren, wurde in dem Ordner ein requirements.txt File hinterlegt. In dieser Datei sind alle benötigten Pakete inklusive Version dokumentiert. Sollte es Probleme beim Durchlaufen lassen des Pythonskript geben, so kann es innerhalb eines  sogenannten "virtual environment" laufen gelassen werden. Um dieses Aufzusetzen müssen folgende Befehle in der Konsole aufgerufen werden. Dazu muss zuerst in diesen Ordner navigiert werden:

(i) Erstellen eines virtual environments namens "env"

	python3 -m venv env

(ii) Aktivieren des virtual environments namens "env"
Windows:

	env\Scripts\activate.bat

Unix oder MacOS:

	source env/bin/activate

(iii) Installieren der benötigten Pakete innerhalb des virtual environments

	pip3 install -r requirements.txt

Gratulation, die benötigten Pakete wurden innerhalb des virtual environments namens env installiert! Sollte es Probleme bei diesen Schritten geben, so findet sich eine ausführliche Anleitung in der Python Dokumentation (https://docs.python.org/3/tutorial/venv.html).



Als Nächstes kann das Skript laufen gelassen werden. Dazu wird folgende Zeile benötigt:

	python3 createIsochrone.py

Es startet eine Untersuchung für das Gewerbegebiet Adlershof am 14.03.2022 (analysisDate). Untersuchungsbeginn ist 17:35:00 (analysisStartTime) für eine Untersuchungsdauer von 1800 Sekunden (analysisDuration), die maximale Anzahl an Umstiegen ist 4 (analysisMaxTransfers). Maximale Einzugsbereiche von Bushaltestellen sind 300 Sekunden (analysisCatchementStreet) Laufdauer und von Zughaltestellen 600 (analysisCatchmentTrain). Der zugrundeliegende GTFS Datensatz ist der des VBB in dem Ordner "gtfs/vbb/" (analysisGtfsPath), während der Startpunkt durch die Datei ors_transfers.csv in dem Ordner "untersuchungsgebiete/Adlershof/" ('untersuchungsgebiete/Adlershof/') gegeben ist. 

Sollten andere Parameter für die Untersuchung gewünscht sein, so können diese in der __main__ Funktion der createIsochrone.py Datei eingestellt werden. 

Für jede erreichte Haltestelle wird eine Isochrone über den OpenRoutingService angefragt und ausgedruckt, für das Programm ist zwingend eine Internetverbindung notwendig! Informationen zu der Isochrone werden im Terminal ausgegeben.


2) --- Erstellen neuer Startpunkte ---
Das Erstellen neuer Startpunkte geschieht in QGIS unter der Verwendung des OpenRoutingService PlugIn. Über "Erweiterungen > Erweiterungen verwalten und installierten…" öffnet sich das Erweiterungen-Dialogfenster, in diesem kann ORS Tools gesucht und heruntergeladen werden. Zurück in der Hauptbedienoberfläche muss unter "Web > ORS Tools > Provider Settings" der ORS API Schlüssel eingegeben werden. Dieser kann auf der Seite "https://openrouteservice.org/dev" erzeugt werden (alternativ kann der Schlüssel 5b3ce3597851110001cf624842a188fa1398429c8964718870a35b5f genutzt werden).

Bevor ein neuer Untersuchungsort festgelegt werden kann, muss einen Polygonlayer mit dem Umriss des Gewerbegebiets und einen Punktlayer mit den Haltestellen aus der stops.txt Datei in das Projekt geladen werden. Der Polygonlayer kann über „Layer > Layer erstellen > neuer Shapedatei-Layer…“ erstellt oder aus einer anderen Quelle in das Projekt geladen werden. Die Haltestellen werden über „Layer > Layer hinzufügen > Getrennte Textdatei als Layer hinzufügen…“ in das Projekt geladen. In der Eingabemaske die sich öffnet, ist die stops.txt Datei aus einem entsprechenden GTFS Datensatz auszuwählen. Die vorausgefüllten Einstellen müssen geprüft werden. Als Dateiformat sollte CSV ausgewählt sein. Unter dem Reiter Geometriedefinition sollte angegeben sein, dass es sich um Punktkoordinaten im Koordinatenbezugssystem EPSG:4326 handelt. Nachdem beide Layer in QGIS geladen wurden, kann über „Verarbeitung > Graphische Modellierung… > Modell öffnen“ die legeUntersuchungsortFest.modell3 Datei geöffnet werden. Eine graphische Darstellung des Modells erscheint in dem Dialogfenster. Der grüne dreieckige „Modell ausführen“ Knopf öffnet eine Eingabemaske. Die zuvor erstellten Layer sind auszuwählen. Zusätzlich kann an dieser Stelle noch festgelegt werden, wie groß das Umfeld um das Gewerbegebiet ist, in dem Haltestellen als erreichbar gelten. Das Modell gibt unter anderem eine Tabelle mit Gehzeiten und -distanzen von dem Mittelpunkt des Polygonlayers zu allen nahegelegenen Haltestellen aus. In dem „Layer Bedienfeld“ taucht „ors_transfers“ als temporärer Layer auf. Das Erstellen dieser Datei war Ziel des Teilprozesses, mit "Rechtsklick > Exportieren > Objekt speichern als…" kann sie gespeichert werden. In dem Dialogfenster welches sich öffnet, ist als Format CSV zu wählen. Name der Datei muss ors_transfers.csv sein.


3) --- Zusammenfassen der Ergebnisisochronen --- 
Das Model namens fasseIsochronenZusammen.modell3 kann analog zu dem Model für das Erstellen eines Startpunktes geoffnet werden. Die Isochronen, die zusammengefasst werden sollen, können direkt aus der Ordnerstruktur ausgewählt werden. 



