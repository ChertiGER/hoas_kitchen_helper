# Changelog – Küchenhelfer Addon

## [1.8.2] – 2026-06-22

### Behoben
- **Auswahl-Bug in Safari/WebViews**: Klick-Handling für Unverträglichkeiten-Checkboxen optimiert, um doppelt auslösende Klick-Ereignisse (Double-Toggle) unter Safari auf macOS und iOS zu verhindern. Die Allergene lassen sich nun reibungslos auswählen.

---

## [1.8.1] – 2026-06-22

### Behoben
- **Cache-Control im Ingress-Iframe**: Es werden nun spezifische Cache-Control-Header für statische HTML-, JS- und CSS-Dateien mitgesendet. Dies verhindert, dass der Browser bei zukünftigen Addon-Updates veraltete Stände aus dem Cache lädt.

---

## [1.8.0] – 2026-06-22

### Neu
- **Küchenpräferenzen**: Neue Konfigurationssektion im Einstellungs-Tab zur KI-Zubereitungsoptimierung basierend auf der vorhandenen Küchenausstattung und Unverträglichkeiten.
- **Detaillierte Küchengeräte-Auswahl**: Auswahl aus 23 typischen Küchengeräten (unterteilt in Grundausstattung, Kaffeezubereitung, Mixer & Küchenmaschinen, Spezialgeräte).
  - **Marken & Modelle**: Optionales Eingabefeld pro ausgewähltem Gerät (z.B. „Vorwerk TM6" bei Thermomix, oder „Ninja DoubleStack" bei Airfryer), um Anweisungen optimal auf das Modell anzupassen.
  - **Gerätespezifische KI-Modi**: Automatisierte Optimierung (z.B. TM-spezifische Varoma/Messerstufen im TM-Modus, Temperatur-/Zeitangaben im Airfryer-Modus).
- **Multi-Select Dropdown für Unverträglichkeiten**: Komfortable Auswahl der 14 EU-Hauptallergene und weiterer Unverträglichkeiten mit übersichtlichen roten Pill-Tags (einzeln per Klick entfernbar).
- **Weitere persönliche Präferenzen**: Freitextfeld für sonstige Hinweise (z.B. „Low-Carb", „saisonal").
- Die Präferenzen fließen automatisch in **alle** KI-Generierungen ein (KI-Chefkoch, Rezept-Scraper, Foto-Import, visuelle Resteverwertung).

---

## [1.7.2] – 2026-06-20

### Geändert
- kleinere Bugfixes

---

## [1.7.1] – 2026-06-20

### Behoben
- Kalender-Datum im Rezept-Einplan-Dialog zeigte immer das Datum des letzten Seitenladevorgangs anstelle des heutigen Datums.
- Langer Rezepttitel auf der Lovelace-Karte wurde abgeschnitten statt umgebrochen.

---

## [1.7.0] – 2026-06-20

### Neu
- **Visuelle Lovelace-Kartenkonfiguration**: Die `kitchen-helper-card` erscheint jetzt direkt im „Karte hinzufügen"-Dialog von Home Assistant – kein manuelles YAML mehr nötig.
- **GUI-Karteneditor**: Beim Bearbeiten der Karte öffnet sich ein vollständiger visueller Editor mit Entity-Dropdown, Farbpicker, Abschnitt-Toggles und Höhensteuerung.
- **Akzentfarbe**: Alle Kartenfarben (Header, Icons, Markierungen) sind jetzt über die Konfiguration anpassbar.
- **`window.customCards`-Registrierung**: Karte ist jetzt korrekt im Lovelace-Picker sichtbar.

### Geändert
- `DOCS.md` und `README.md` auf v1.7.0 aktualisiert (Lovelace-Sektion überarbeitet).

---

## [1.6.3] – 2026-06-19

### Neu
- **Dokumentationsseite** (`DOCS.md`) im Addon für den HA-Dokumentations-Tab.
- **PayPal-Spendenlink** in README, App-Footer und Addon-Beschreibung integriert.
- **Repo-Kurzname** (`ChertiGER/hoas_kitchen_helper`) in der Addon-Übersicht sichtbar.

### Behoben
- `python-multipart` als fehlende Abhängigkeit ergänzt (verhinderte Datei-Uploads).

### Optimiert
- Clientseitige Bildkomprimierung vor dem Upload (reduziert Übertragungsgröße deutlich).
- Garbage Collection Middleware in FastAPI zur aktiven Speicherfreigabe auf dem Raspberry Pi.
- AnyIO Thread-Pool auf 4 Threads begrenzt.
- SQLite `cache_size` auf 200 KB reduziert.

---

## [1.6.0] – 2026-06-19

### Neu
- **Rezept-Scraper**: URL einer Kochwebseite eingeben, Rezept wird automatisch digitalisiert.
- **Foto-Import**: Bild eines gedruckten Rezepts hochladen, KI erstellt einen Entwurf.
- **Visuelle Resteverwertung**: Kühlschrank fotografieren, KI schlägt passende Rezepte vor.
- **Rezept-Tags**: Benutzerdefinierte Tags analog zu den KI-Chefkoch-Dropdowns.
- **Tag-Filter** in der Rezeptsammlung.
- **HACS Dashboard-Karte** (`kitchen-helper-card.js`): Zeigt das heutige Rezept im Lovelace-Dashboard an.

---

## [1.0.0] – 2026-06-01

### Neu
- Lokale Rezeptdatenbank (SQLite).
- KI-Chefkoch: Rezepte generieren mit OpenAI, Anthropic, Gemini oder OpenAI-kompatiblen Providern.
- Wochenplaner mit HA-Kalender-Integration.
- Smarte Einkaufsliste mit direktem Export in HA-To-Do-Listen.
- Intelligente Portionierung (automatische Mengenanpassung).
- Standardvorrat (Pantry) zur automatischen Markierung vorhandener Zutaten.
