🚗 BABmapper

Ein umfassendes Python-Desktop-Tool zur Visualisierung von Echtzeit-Verkehrsdaten der deutschen Autobahnen.
📖 Projektbeschreibung

BABmapper ist eine GUI-Anwendung, die Verkehrsdaten der Autobahn GmbH des Bundes abruft und auf einer interaktiven Karte darstellt.

Das Tool wurde entwickelt, um Pendlern, Logistikern oder Verkehrsinteressierten einen schnellen, gefilterten Überblick über die aktuelle Lage auf einer spezifischen Autobahn zu geben. Anders als Web-Apps setzt BABmapper auf eine native Desktop-Oberfläche mit lokalem Caching für maximale Performance und geringe API-Last.
✨ Features

    Interaktive Karte:

        Umschaltbar zwischen Topographisch (OpenStreetMap) und Satellit (Google Earth).

        Zoom- und Pan-Funktionen.

    Live-Daten Layer (Filterbar):

        🚧 Baustellen (Roadworks)

        ⚠️ Verkehrsmeldungen (Stau, Gefahren)

        ⛔ Sperrungen (Closures)

        ⚡ Ladestationen (E-Charging)

        🅿️ Rastplätze (Parking / LKW)

        📷 Webcams (Standorte & Metadaten)

    Live-Feed:

        Integrierter Newsticker für Warnungen und Sperrungen.

        Klick auf eine Meldung zoomt direkt zum Geschehen auf der Karte.

        Lokale Filterung des Feeds.

    Intelligentes Caching:

        Daten werden lokal zwischengespeichert, um API-Limits einzuhalten.

        Einstellbares Aktualisierungsintervall (Standard: 5 Min).

        Automatischer Refresh im Hintergrund.

    Detail-Ansicht:

        Seitenleiste mit detaillierten Informationen zu jedem Marker (Beschreibung, Start-/Endzeit, Ausstattungsmerkmale).

🛠️ Technologie & Pakete

Das Projekt ist in Python geschrieben und nutzt tkinter für die grafische Oberfläche.
Verwendete Bibliotheken

Folgende externe Pakete werden benötigt (siehe requirements.txt):

    tkintermapview: Für die Kartendarstellung (basiert auf OpenStreetMap Kacheln).

    requests: Für die Kommunikation mit der Autobahn-API.

    Pillow: Für Bildverarbeitung (Marker-Icons etc.).

🚀 Installation

    Repository klonen

bash
git clone https://github.com/dein-user/babmapper.git
cd babmapper

Abhängigkeiten installieren
Es wird empfohlen, eine virtuelle Umgebung (venv) zu nutzen.

bash
pip install -r requirements.txt

Anwendung starten

    bash
    python babmapper.py

🌍 Datenquellen & Credits

Dieses Projekt nutzt öffentliche Daten und Dienste:

    Verkehrsdaten: Bereitgestellt von der Die Autobahn GmbH des Bundes über deren öffentliche API.

    Kartenmaterial (Topo): © OpenStreetMap contributors. Open Data Commons Open Database License (ODbL).

    Kartenmaterial (Satellit): Google Maps Satellite Tiles.

⚙️ Konfiguration

Über den Einstellungen-Button (⚙️) in der App kann das Intervall für die automatische Aktualisierung angepasst werden, um Datenvolumen zu sparen oder die Aktualität zu erhöhen.
📄 Lizenz

Dieses Projekt ist unter der MIT Lizenz veröffentlicht. Siehe LICENSE für Details.

Dies ist ein inoffizielles Tool und steht in keiner direkten Verbindung zur Autobahn GmbH des Bundes.
