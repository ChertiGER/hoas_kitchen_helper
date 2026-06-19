# hoas_kitchen_helper — Küchenhelfer Addon

Die Küchenhelfer-Integration für Home Assistant verbindet Essensplanung und Einkaufsliste in einem übersichtlichen Dashboard. Sie bietet:

- Lokale Rezeptdatenbank (SQLite) mit skalierbaren Zutatenmengen
- KI-gestützte Rezeptgenerierung (OpenAI / Anthropic kompatibel)
- Integration in Home Assistant Kalender und Einkaufsliste

Lokaler Schnellstart (Entwicklung):

1) Mit Docker bauen und starten

```bash
# im Projekt-Root
docker build -t hoas_kitchen_helper:local -f kitchen_helper/Dockerfile .
docker run --rm -p 8000:8000 \
	-v $(pwd)/data:/data \
	-e OPENAI_API_KEY=your_key_here \
	hoas_kitchen_helper:local
```

2) Lokal mit Python (Entwicklungsmodus)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r kitchen_helper/requirements.txt
export PYTHONPATH=./kitchen_helper
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Wichtige API Endpunkte:

- `GET /api/ha/status` — HA-Verbindungsstatus
- `GET /api/recipes` — Liste der Rezepte
- `GET /api/recipes/{id}` — Einzelnes Rezept
- `POST /api/recipes` — Rezept anlegen
- `POST /api/recipes/generate` — LLM-Rezept generieren

## Installation in Home Assistant

### Schritt 1: Repository hinzufügen

1. Öffne Home Assistant → **Einstellungen** → **Add-ons & Automationen** → **Add-ons** → **ADD-ON STORE**
2. Klicke auf das **⋮** (Menü) Symbol oben rechts
3. Wähle **Repositories**
4. Gib folgende Repository-URL ein:
   ```
   https://github.com/ChertiGER/hoas_kitchen_helper
   ```
5. Klicke **Hinzufügen** und warte auf die Bestätigung

### Schritt 2: Küchenhelfer-Addon installieren

1. Gehe zurück zum **ADD-ON STORE**
2. Suche nach **"Küchenhelfer"** (oder refreshe die Seite)
3. Klicke auf das Addon und dann auf **INSTALLIEREN**
4. Warte bis die Installation abgeschlossen ist

### Schritt 3: Konfiguration

Bevor du das Addon startest, musst du die Optionen konfigurieren:

1. Klicke auf das Addon im Dashboard
2. Gehe zum Tab **Konfiguration**
3. Wähle deinen **LLM-Anbieter**:

#### Option A: OpenAI verwenden

```yaml
llm_provider: openai
openai_api_key: sk-xxxxx  # Dein OpenAI API Key
openai_model: gpt-4o-mini  # oder gpt-4, gpt-3.5-turbo, etc.
custom_openai_url: ""  # Leer lassen für api.openai.com
```

#### Option B: Anthropic (Claude) verwenden

```yaml
llm_provider: anthropic
anthropic_api_key: sk-ant-xxxxx  # Dein Anthropic API Key
anthropic_model: claude-3-5-haiku-latest
```

#### Option C: OpenAI-kompatible API (Azure, Ollama, etc.)

```yaml
llm_provider: openai_compatible
custom_openai_url: https://your-azure-instance.openai.azure.com
openai_api_key: your-key-or-token
openai_model: gpt-4  # Modellname bei deinem Provider
```

#### Option D: Home Assistant Conversation Entity verwenden

Falls du bereits eine LLM-Integration in HA hast (z.B. Google Generative AI):

```yaml
use_ha_conversation: true
ha_conversation_entity: conversation.google_ai_conversation
# Optional: ein andere Conversation Entity, z.B. conversation.openai
```

4. Speichere die Konfiguration

### Schritt 4: Addon starten

1. Klicke auf **STARTEN** im Addon-Panel
2. Prüfe die Logs:
   - Sollte "Starting Küchenhelfer Addon..." anzeigen
   - Status sollte nach kurzer Zeit **Running** sein

### Schritt 5: Zugriff auf das Dashboard

Nach Start ist das Küchenhelfer-Dashboard unter **Ingress** verfügbar:
- Home Assistant Sidebar → Scrollen → **Küchenhelfer** anklicken

Oder direkt: `https://dein-ha-domain/api/hassio/app/kitchen_helper`

---

## Verwendung

### Rezepte verwalten

1. **Rezepte durchsuchen**: Tab "Rezepte" → Suche oben nutzen
2. **Rezept hinzufügen** (manuell): Tab "Rezept hinzufügen" → Formular ausfüllen → Speichern
3. **KI-Rezept generieren**: Tab "KI-Chefkoch" → Beschreibung eingeben → "Rezept generieren"

### In Kalender planen

1. Öffne ein Rezept aus der Liste
2. Stelle die gewünschte Portionszahl ein (Zutaten skalieren automatisch)
3. Klicke "In Kalender eintragen"
4. Wähle einen Kalender und Datum aus

### Zutaten zur Einkaufsliste

1. Im Rezept-Detail: Hake die Zutaten an, die du kaufen möchtest
2. Klicke "Zur Einkaufsliste hinzufügen"
3. Wähle deine To-Do-Liste / Einkaufsliste aus HA

---

## Troubleshooting

### Addon startet nicht / Fehler in den Logs

- Prüfe die **Konfiguration** im Addon (alle erforderlichen Felder ausfüllen)
- Lies die **Logs** im Addon-Panel für Fehlermeldungen
- Bei API-Key Problemen: Teste den Key auf der Website des Anbieters

### Home Assistant API nicht verfunden

- Das ist in der Entwicklung normal (localhost ohne Supervisor Token)
- In einem echten HA-System verbindet sich das Addon automatisch
- Feature wird für die Planung trotzdem angeboten (Placeholder)

### KI-Rezept generiert wird nicht / leerer Output

- Prüfe deinen **API Key** (falsch eingetragen?)
- Versuche einen anderen **Prompt** im KI-Chefkoch
- Bei rate limiting: Warte kurz und versuche erneut

---

---

## Lizenz

Dieses Projekt steht unter der **GNU General Public License v3.0** — siehe [LICENSE](LICENSE) für Details.

**Kurz gesagt:** Du kannst diesen Code frei verwenden, modifizieren und weitergeben — solange deine Änderungen auch unter GPL3.0 lizenziert sind.

Weitere Infos: [gnu.org/licenses/gpl-3.0](https://www.gnu.org/licenses/gpl-3.0.html)

