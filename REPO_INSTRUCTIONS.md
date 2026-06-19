# Standardanweisung – hoas_kitchen_helper

> Diese Datei ist die verbindliche Arbeitsanweisung für KI-Assistenten und Entwickler beim Arbeiten mit diesem Repository.
> Sie wird bei jeder neuen Sitzung konsultiert, bevor Code-Änderungen vorgenommen werden.

---

## 📋 Pflichtschritte bei JEDER neuen Version

Bei jeder Versionserhöhung sind **alle** der folgenden Schritte verpflichtend:

### 1. CHANGELOG.md aktualisieren
**Datei:** `addons/kitchen_helper/CHANGELOG.md`

- Neuen Eintrag ganz **oben** einfügen (neueste Version zuerst).
- Format: `## [X.Y.Z] – YYYY-MM-DD`
- Abschnitte verwenden: `### Neu`, `### Geändert`, `### Behoben`, `### Optimiert`, `### Entfernt`
- Jeder Eintrag muss auf Deutsch und für Endanwender verständlich sein.
- **Warum**: Home Assistant liest diese Datei aus und zeigt sie beim Addon-Update im Store an.

### 2. README.md aktualisieren
**Datei:** `README.md`

- Neue Funktionen in den entsprechenden Abschnitt eintragen.
- Bei neuen Konfigurationsoptionen die Tabelle im Installations-Abschnitt ergänzen.
- Badge-Links und externe Verlinkungen aktuell halten.

### 3. DOCS.md aktualisieren
**Datei:** `addons/kitchen_helper/DOCS.md`

- Neue Funktionen im Abschnitt „Funktionen im Überblick" beschreiben.
- Schritte in „Erste Schritte" anpassen, wenn sich der Installationsablauf ändert.
- **Warum**: Diese Datei wird in Home Assistant als Dokumentations-Tab des Addons angezeigt.

### 4. Versionsnummern synchronisieren
Alle drei Dateien müssen immer die **gleiche** Versionsnummer tragen:

| Datei | Schlüssel |
|---|---|
| `addons/kitchen_helper/config.json` | `"version": "X.Y.Z"` |
| `kitchen_helper/config.yaml` | `version: "X.Y.Z"` |

### 5. Git-Commit & Tag
```bash
git add .
git commit -m "feat/fix/chore: kurze Beschreibung (vX.Y.Z)"
git tag -a vX.Y.Z -m "vX.Y.Z: Kurzbeschreibung der wichtigsten Änderung"
git push origin main
git push origin vX.Y.Z
```

**Commit-Konventionen:**
- `feat:` – neue Funktion
- `fix:` – Fehlerbehebung
- `perf:` – Performance-Optimierung
- `docs:` – nur Dokumentation geändert
- `chore:` – Build, Konfiguration, Abhängigkeiten

---

## 🔢 Versionsstrategie (Semantic Versioning)

| Änderung | Version | Beispiel |
|---|---|---|
| Neue Hauptfunktion oder Breaking Change | **Major** X.0.0 | Neue Datenbank-Struktur |
| Neue Funktion, abwärtskompatibel | **Minor** 1.Y.0 | Neuer KI-Provider |
| Bugfix, Performance, Docs | **Patch** 1.1.Z | Absturzfix, Speicher-Tuning |

---

## 📁 Projektstruktur

```
hoas_kitchen_helper/
├── kitchen-helper-card.js       # Lovelace Custom Card (HACS)
├── README.md                    # GitHub README
├── CHANGELOG.md                 # Root-Changelog (optional, Mirror)
├── repository.json              # HACS Repository-Metadaten
├── hacs.json                    # HACS Konfiguration
│
├── addons/kitchen_helper/       # Home Assistant Addon-Paket
│   ├── config.json              # Addon-Metadaten & Version ← SYNC!
│   ├── CHANGELOG.md             # HA-sichtbarer Changelog ← IMMER UPDATEN
│   ├── DOCS.md                  # HA Dokumentations-Tab ← IMMER UPDATEN
│   ├── Dockerfile
│   ├── run.sh
│   └── app/                     # Gespiegelt von kitchen_helper/app/
│
└── kitchen_helper/              # Entwicklungsquelle
    ├── config.yaml              # Addon-Metadaten & Version ← SYNC!
    └── app/
        ├── main.py              # FastAPI Backend
        ├── database.py          # SQLite Datenbanklogik
        ├── static/
        │   ├── app.js           # Frontend-Logik
        │   └── index.html       # Frontend-UI
        └── ...
```

### ⚠️ Wichtig: App-Verzeichnis ist doppelt vorhanden!
`kitchen_helper/app/` ist die Entwicklungsquelle.  
`addons/kitchen_helper/app/` ist die HA-Addon-Version.  
**Bei jeder Änderung an Python/JS-Dateien: beide Verzeichnisse synchron halten!**

---

## 🏗 Architektur-Überblick

- **Backend**: FastAPI (Python), läuft auf Port 8000 via Uvicorn
- **Frontend**: Vanilla HTML/CSS/JS (Single-Page-App), serviert als StaticFiles
- **Datenbank**: SQLite (`/data/recipes.db` auf dem HA-Host)
- **KI-Anbindung**: OpenAI / Anthropic / Gemini / OpenAI-kompatibel (via `llm_provider` Config)
- **HA-Integration**: Supervisor API für Kalender, To-Do-Listen und Addon-Optionen
- **Lovelace-Karte**: `kitchen-helper-card.js` – Custom Element mit visuellem Editor

---

## 🧠 Bekannte Einschränkungen & Hinweise

- **RAM auf Raspberry Pi**: Python's Speicher-Allocator gibt Speicher nicht immer ans OS zurück. `gc.collect()` + `malloc_trim` Middleware ist bewusst aktiv – nicht entfernen.
- **Thread-Pool**: AnyIO-Pool ist auf 4 begrenzt, um den Pi nicht zu überlasten.
- **SQLite Cache**: `cache_size` ist auf 200 KB begrenzt – für kleine Datenmengen ausreichend.
- **Bildkomprimierung**: Bilder werden clientseitig vor dem Upload komprimiert (Canvas API), um Übertragung + Speicher zu schonen.
- **Dual-Directory**: Änderungen immer in BEIDEN App-Verzeichnissen vornehmen (oder ein Sync-Skript nutzen).

---

## 🔧 Lokale Entwicklung

```bash
# Virtuelle Umgebung aktivieren
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r kitchen_helper/requirements.txt

# Server starten (ohne HA-Supervisor-Token)
cd kitchen_helper
uvicorn app.main:app --reload --port 8000
```

---

## ☕ Maintainer

**Yannick Holz** – [@ChertiGER](https://github.com/ChertiGER)  
Support via PayPal: [paypal.me/YHolz](https://paypal.me/YHolz)
