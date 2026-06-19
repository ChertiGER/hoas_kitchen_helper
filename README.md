# 🍳 Küchenhelfer Addon

**Die Küchenhelfer-Integration für Home Assistant verbindet Essensplanung, Einkaufslisten und KI-Rezeptgenerierung in einem übersichtlichen, modernen Dashboard.**

---

## ✨ Hauptfunktionen

### 1. Lokale Rezeptdatenbank (SQLite)
*   **Rezepte verwalten**: Erstelle und bearbeite deine Rezepte komfortabel im Dashboard.
*   **Intelligente Portionierung**: Ändere die Portionsanzahl eines Rezepts per Klick, und alle Zutatenmengen passen sich automatisch und präzise an.
*   **Volltextsuche**: Suche blitzschnell nach Rezepttiteln, Beschreibungen oder bestimmten Zutaten.

### 2. KI-Chefkoch (Rezept-Generator)
*   **Kreative Rezeptgenerierung**: Gib eine Idee oder Zutaten ein, die du im Kühlschrank hast, und lass dir ein passendes Rezept kreieren.
*   **Individuelle Vorgaben**: Passe das Rezept an deine Ernährungsform (z. B. vegetarisch, vegan, glutenfrei) oder deinen Lieblings-Küchenstil an.
*   **Direkte Integration**: Nutze wahlweise **Google Gemini**, **OpenAI**, **Anthropic (Claude)** oder andere **OpenAI-kompatible Schnittstellen** (z. B. lokale LLMs über Ollama).

### 3. Wochenplaner & Kalender-Integration
*   **Menüplanung**: Plane deine Gerichte für die Woche und trage sie direkt in deine Home Assistant-Kalender ein.
*   **Skalierte Informationen**: Die Rezepte werden automatisch inklusive aller hochgerechneten Zutaten und der Anleitung als ganztägige Kalendereinträge angelegt.

### 4. Smarte Einkaufsliste
*   **Zutaten auswählen**: Hake im Rezept-Detail genau die Zutaten an, die dir für das Gericht noch fehlen.
*   **Direkter Export**: Füge die ausgewählten Zutaten mit einem Klick zu deinen Home Assistant To-Do-Listen (z. B. der Standard-Einkaufsliste) hinzu.

---

## 🚀 Installation & Setup

### 1. Repository hinzufügen
1. Gehe in Home Assistant zu **Einstellungen** → **Add-ons** → **Add-on Store**.
2. Klicke oben rechts auf **⋮** → **Repositories**.
3. Füge folgende URL hinzu: `https://github.com/ChertiGER/hoas_kitchen_helper`

### 2. Add-on installieren & konfigurieren
1. Suche im Store nach **"Küchenhelfer"** und installiere das Add-on.
2. Gehe zum Tab **Konfiguration** und wähle deinen `llm_provider`:

| `llm_provider` | Beschreibung | Benötigte Felder |
| :--- | :--- | :--- |
| **`openai`** | OpenAI (GPT Modelle) | `openai_api_key`, `openai_model` |
| **`anthropic`** | Anthropic (Claude Modelle) | `anthropic_api_key`, `anthropic_model` |
| **`openai_compatible`** | Eigene APIs (Ollama, Azure, etc.) | `openai_api_key`, `openai_model`, `custom_openai_url` |
| **`gemini`** | Google Gemini | `gemini_api_key`, `gemini_model` |

### 3. Optionale Standard-Einstellungen (Kalender & Einkaufsliste)
Du kannst in der Konfiguration Standard-Entitäten festlegen, damit diese in der App bereits vorausgewählt sind:
- **`default_calendar`**: Die Entity-ID deines HA-Kalenders (z.B. `calendar.weekly_meals`).
- **`default_shopping_list`**: Die Entity-ID deiner HA-To-Do-Liste (z.B. `todo.einkaufsliste`) oder `legacy` für die klassische Einkaufsliste.

---

## 🛡️ Lizenz
Dieses Projekt steht unter der **GNU General Public License v3.0** — siehe [LICENSE](LICENSE) für Details.
