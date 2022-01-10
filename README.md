# esg-erreichbarkeit

Hallo Welt!
Danke für das Interesse, ich freue mich sehr über Feedback jeder Art. Natürlich beantworte ich auch gerne offen gebliebene Fragen!
mailto: manuel.fischer0309@web.de



## Intro:
Vorgestellt wird das Vorgehen zum Erstellen von Isochronen des ÖPNV. Das Tool verwendet dafür Daten im GTFS Format. Die erstellten Isochronen können durch einen GHSL Datensatz mit Einwohnerzahlen bereichert werden. Eine Analyse der Ergebnisse ist nicht enthalten.


## Stand:
- Es können Isochronen gezeichnet und mit Einwohnerdaten bereichert werden.
- Die Analyse ist NICHT vollautomatisiert.


## Verwendete Programme:
- Python3
- Qgis + ors plugin


## Kurzanleitung:
- Erstelle die Datei "osm_transfers.csv" mit dem QGIS Model "create_ors_transfers.model3".
- lasse analyst.py durchlaufen. Berechnung der Rohdaten dauert wenige Minuten. Erstellen der Isochronen dauert (siehe ORS API Restriktionen).
- Nachbereitung der Ergebnisse in QGIS [merge, dissolve, zonal statistiks]. Noch nicht in Graphical Modeller überführt.


## Benötigte Datensätze (schon in den Ordnern vorhaneden):
- gtfs Datensatz: (getestet für) https://www.vgn.de/opendata/GTFS.zip
- ghsl Datensatz: (getestet für) https://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_MT_GLOBE_R2019A/GHS_POP_E2015_GLOBE_R2019A_4326_9ss/V1-0/GHS_POP_E2015_GLOBE_R2019A_4326_9ss_V1_0.zip


## Schritt-für-Schritt Anleitung:

1) Vorbereitung in QGIS:
- QGIS: Händisches Erstellen eines Polygonlayer für das gewünschte Gewerbegebiet [Layer > Create "hiddenSpellError">new Layer > New Shapefile Layer...].
- QGIS: Erstellen eines konkreten Polygon, welches das Gewerbegebiet umreist [Toggle Editing > Add Polygon Feature > "erstellen des gewünschten Polygons" > Save Layer Edits > Toggle Editing].
- QGIS: Importiere stops.txt aus dem gtfs Datensatz in das Projekt [Layer > Add Layer > Add Delimited Text Layer...].
- QGIS: öffne den Graphical Modeller [Processing > Graphical Modeler...].
- QGIS/Graphical Modeler: open model "create_ors_transfers.model3". Das ORS-Plugin wird benötigt, den API Key kann man sich kostenlos holen. Entweder im Internet oder aus meinem Pythonmodul.
- QGIS/Graphical Modeler: run model (Plugin Version 1.4. benötigt).
- QGIS: speichere das Ergebnis des Matrix batch als "ors_transfers.csv". Speicherordner ist der Projektordner des Untersuchungsgebietes.

2) Berechnung der erreichbaren Haltestellen
- Python: öffne analyst.py
- Python: lege die Parameter fest:
	- filepath zu GTFS Datensatz
	- filepath zu Ordner mit dem Untersuchungsort. Dieser Ordner _muss die ors_transfers.txt enthalten.
	- Die Startzeiten der Untersuchung. Momentan werden acht Startzeiten mit 15 min Abstand berücksichtigt.
	- Untersuchungsdauer in Sekunden festlegen (=maximale Fahrtzeit).
	- Maximale Anzahl an Umstiegen festlegen.
- Python: Zurücklegen, entspannen und warten.

3) Nachbereitung:
- QGIS: fasse die einzelnen Isochronen zu einem Layer zusammen [Processing Toolbox > Vector general > Merge vector layer].
- QGIS/Merge vector layer: wähle alle single_iso Dateien mit demselben Präfix aus [inout layers > add file(s)...]
- QGIS: verschmelze die einzelnen Polygone des soeben erstellten Layer [Processing Toolbox > Vector geometry > Dissolve].
- QGIS: Bereichere das Ergebnispolygon mit Einwohnerdaten [Raster analysis > Zonal statistics].


## Beispiele zum Ausprobieren:
Im Ordner "Untersuchungsgebiete" findet ihr drei Projekte. Diese beinhalten verschiedene Zwischenstände der Analyse:
- Allersbegerstr.: Hier wurden schon Isochronen gezeichnet und QGIS Projekte angelegt.
- Nord-Ost-Park: ors_transfers.csv ist vorhanden. Es kann also direkt mit dem Python losgespielt werden.
- Panattoni-Park-Nuernberg: Das Gewerbegebietspolygon ist erstellt. Das Polygon und die stops.txt Datei sind in QGIS geladen. Es kann direkt das "create_ors_transfers.model3" ausprobiert werden. !!!Wichtig!!!: ors plugin version 1.5. ist defekt, wird aber im Lauf der Woche gefixed. Dazu: https://ask.openrouteservice.org/t/qgis-ors-tools-matrix-from-layers-keyerror/3461


## Offene Fragen uns sonstiges:
- Wochentage vs. Wochenende noch nicht berücksichtigt; Problem: Was passiert mit Trips, die nicht klar zuordenbar sind (z. B.: trips mit der service_id "T3+ro3" fahren nur dienstags und sonntags)?
- ghsl hat bei nicht vorhandenen daten den Standardwert -200; Problem: können diese Zellen das Untersuchungsergebnis verzerren?
- Es gibt startzeitbedingte Schwankungen bei den Einzugsgebietsgrößen und der damit assoziierten Einwohnerzahl. Problem: Die Erstellung eines Indexes ist von vielen "politischen" Entscheidungen geprägt (sollen Mittelwerte von mehreren Isochronen gebildet werden? Zu Stoßzeiten oder über den ganzen Tag? Welche zeitliche Auflösung soll ist angemessen? Etc.).


## Ausblick:
- Einzugsgebiete der Haltestellen sind abhängig von dem Verkehrsmittel und Urbanisierungsgrad an der Haltestelle. -> Berücksichtigen?
- Räumliche Eingrenzung von stop_times.txt. Besonders wichtig, sobald mit GTFS Datensätzen auf nationaler Ebene gearbeitet wird (beziehbar über GTFS.de oder NAP).
- ors via Docker und nicht via api verwenden.
- nicht nur isochronen vom Gewerbegebiet ausgehend, sondern auch mit Gewerbegebiet als Zielpunkt.

## Quickstart GTFS:
Intro in GTFS: https://www.youtube.com/watch?v=8OQKHhu1VgQ
Aufbau GTFS: https://developers.google.com/transit/gtfs/reference#routestxt

