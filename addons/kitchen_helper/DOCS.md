# 🍳 Küchenhelfer Addon Dokumentation

Willkommen beim Küchenhelfer! Dieses Addon verbindet deine Rezeptdatenbank, Essensplanung (über Home Assistant Kalender) und deine Einkaufslisten (über Home Assistant To-Do-Listen) in einem modernen, KI-unterstützten Dashboard.

---

## 🚀 Erste Schritte

### 1. Installation
Stelle sicher, dass du das Repository `https://github.com/ChertiGER/hoas_kitchen_helper` in deinem Home Assistant Add-on Store hinzugefügt hast. Nach der Installation kannst du das Addon starten. Aktiviere am besten **"In der Seitenleiste anzeigen"**, um schnellen Zugriff auf das Dashboard zu haben.

### 2. Konfiguration des KI-Anbieters
Gehe in den Tab **Konfiguration** des Addons und wähle deinen bevorzugten `llm_provider`:

| Provider | Beschreibung | Benötigte Einstellungen |
| :--- | :--- | :--- |
| **`gemini`** (Empfohlen) | Google Gemini | `gemini_api_key`, `gemini_model` (z.B. `gemini-1.5-flash`) |
| **`openai`** | OpenAI (GPT-Modelle) | `openai_api_key`, `openai_model` (z.B. `gpt-4o-mini`) |
| **`anthropic`** | Anthropic (Claude-Modelle) | `anthropic_api_key`, `anthropic_model` |
| **`openai_compatible`** | Eigene APIs (z.B. Ollama, LocalAI) | `openai_api_key`, `openai_model`, `custom_openai_url` |

---

## 🍲 Funktionen im Überblick

### 1. Rezeptdatenbank & Portionierung
* Du kannst Rezepte manuell anlegen oder bestehende Rezepte per Mausklick portionieren.
* Die Zutatenmengen passen sich dabei vollautomatisch an die gewünschte Personenanzahl an.

### 2. Kalenderplanung
* Wähle ein Datum im Rezept-Detail, um das Gericht direkt in deinen Home Assistant Kalender einzutragen.
* Das Addon skaliert die Zutaten und fügt die komplette Anleitung in das Kalenderereignis ein.

### 3. Smarte Einkaufsliste
* Hake Zutaten an, die dir fehlen, und exportiere sie direkt in deine Home Assistant To-Do-Liste.
* **Standardvorrat (Pantry)**: Zutaten auf deiner Pantry-Liste (z.B. Salz, Öl, Mehl) werden automatisch als vorrätig markiert und beim Einkaufslisten-Export standardmäßig abgewählt.

### 4. KI-Chefkoch, Web-Scraper & Bild-Import
* **KI-Chef**: Gib einfach Zutaten oder Wünsche ein, wähle Ernährungsform oder Küchenstil, und lass dir ein Rezept generieren.
* **Web Scraper**: Trage die URL einer Koch-Webseite (z.B. Chefkoch) ein, um das Rezept direkt zu digitalisieren.
* **Foto-Import**: Lade ein Foto eines gedruckten Rezepts hoch. Die KI liest es ein und erstellt einen Entwurf.
* **Resteverwertung (Vision)**: Fotografiere deinen Kühlschrank oder deine Vorräte. Die KI erkennt die Zutaten und schlägt passende Rezepte vor.

---

## 🎴 Lovelace Dashboard Rezeptkarte

Du kannst dein Dashboard mit einer schicken Rezeptkarte verschönern, die das heute geplante Rezept direkt anzeigt:

1. Lade dir die `kitchen-helper-card.js` aus dem Konfigurations-Tab der App oder direkt aus dem GitHub-Repository herunter.
2. Registriere sie in Home Assistant unter **Einstellungen** → **Dashboards** → **Ressourcen** als JavaScript-Modul (`/local/kitchen-helper-card.js` o.ä.).
3. Füge auf deinem Dashboard eine manuelle Karte hinzu:
   ```yaml
   type: custom:kitchen-helper-card
   entity: calendar.dein_kochplan_kalender
   ```

---

## ☕ Support & Spenden

Die Entwicklung und Pflege dieses Addons erfolgt in meiner Freizeit. Wenn dir der Küchenhelfer gefällt und er deinen Alltag erleichtert, freue ich mich riesig über eine kleine Unterstützung!

* **PayPal.me**: [Kaffee spendieren via paypal.me/YHolz](https://paypal.me/YHolz)

Vielen Dank für deine Unterstützung!
