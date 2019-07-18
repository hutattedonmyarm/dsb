Ein kleines Tool, welches den DSBMobile Vertretungsplan nach dem eingegebenen Klassennamen filtert und die Ergebnisse auflistet.

**Vorraussetzungen**
* python >= 3.7.0
* requests => `pip install requests`
* bs4 => `pip install beautifulsoup4`

**Einrichtung**
1. Benötigte Module installieren
2. `config.py.sample` in `config.py` umbenennen
3. Login-Daten, Klasse, und Aushang in Config eintragen
4. `dsb.py` ausführen

Bei einigen Schulen gibt es mehrere Aushänge, z.B. in Berufsschulzentren. Diese heißen dann "Foyer (aktuell)", "WG (zukünftig)", etc. Dafür gibt es den Eintrag `notice` in der Config. Setze diesen einfach auf "Foyer" oder "TG", etc. Damit werden dann alle Aushänge gefunden, die "Foyer" beinhalten. Falls alle Aushänge mit einbezogen werden sollen den Eintrag einfach auf `None` setzen.

**dsb.sh**
Die `dsb.sh` hatte ich ursprünglich für Testzwecke angelegt. Sie liefert nur die URLs zu den aktuellen Aushängen (aktuell und zukünftig) zurück.