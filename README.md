# 🍳 Küchenhelfer Addon v1.1.1

**Die Küchenhelfer-Integration für Home Assistant verbindet Essensplanung, Einkaufslisten und KI-Rezeptgenerierung in einem übersichtlichen Dashboard.**

---

## ✨ Features
- **Rezeptdatenbank**: Lokale Verwaltung (SQLite) mit automatischer Zutatenskalierung.
- **KI-Chefkoch**: Generiere Rezepte per OpenAI, Anthropic, OpenAI-kompatiblen APIs (z.B. Ollama) oder direkt über eine Home Assistant Conversation Entity (z.B. Google Generative AI).
- **HA-Integration**: Rezepte direkt in den HA-Kalender eintragen und Zutaten auf die Einkaufsliste setzen.
- **Modernes UI**: Schnelles und responsives Design basierend auf Tailwind CSS.

---

## 🚀 Installation & Setup

### 1. Repository hinzufügen
1. Gehe in Home Assistant zu **Einstellungen** → **Add-ons** → **Add-on Store**.
2. Klicke oben rechts auf das Dreipunkt-Menü **⋮** → **Repositories**.
3. Füge folgende URL hinzu: `https://github.com/ChertiGER/hoas_kitchen_helper`

### 2. Add-on installieren & konfigurieren
1. Suche im Store nach **"Küchenhelfer"** und installiere das Add-on.
2. Gehe zum Tab **Konfiguration** und wähle deinen `llm_provider`:

| `llm_provider` | Beschreibung | Benötigte Felder |
| :--- | :--- | :--- |
| **`openai`** | OpenAI (GPT Modelle) | `openai_api_key`, `openai_model` |
| **`anthropic`** | Anthropic (Claude Modelle) | `anthropic_api_key`, `anthropic_model` |
| **`openai_compatible`** | Eigene APIs (Ollama, Azure, etc.) | `openai_api_key`, `openai_model`, `custom_openai_url` |
| **`homeassistant`** | HA eigene KI-Konversation | `ha_conversation_entity` |

### Optionale Standard-Einstellungen (Kalender & Einkaufsliste)
Du kannst auch Standard-Entitäten für deinen Kalender und deine Einkaufsliste definieren, damit diese in der App direkt vorausgewählt sind:
- **`default_calendar`**: Die Entity-ID deines gewünschten HA-Kalenders (z.B. `calendar.weekly_meals`).
- **`default_shopping_list`**: Die Entity-ID deiner HA-To-Do-Liste (z.B. `todo.einkaufsliste`) oder `legacy` für die klassische HA-Einkaufsliste.

*Hinweis: Wenn ein Provider ausgewählt wird, werden alle ungenutzten API-Schlüssel/Optionen der anderen Anbieter in der App automatisch deaktiviert und ignoriert.*

3. Starte das Add-on und greife über die Seitenleiste (Ingress) darauf zu.

---

## 🛠️ Lokale Entwicklung (Schnellstart)

Falls du am Code arbeiten möchtest:

```bash
# 1. Repository klonen und virtuelles Environment aufsetzen
git clone https://github.com/ChertiGER/hoas_kitchen_helper.git
cd hoas_kitchen_helper
python3 -m venv .venv && source .venv/bin/activate
pip install -r kitchen_helper/requirements.txt

# 2. Server lokal starten (Port 8000)
export PYTHONPATH=./kitchen_helper
uvicorn app.main:app --reload
```

---

## 🛡️ Lizenz & Rechtliches
Dieses Projekt steht unter der **GNU General Public License v3.0** — siehe [LICENSE](LICENSE) für Details.
