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

### 4. Küchenpräferenzen & Unverträglichkeiten (ab v1.8.0)
* **Küchengeräte & Modelle**: Wähle deine Küchenausstattung aus 23 typischen Geräten aus und definiere optional Marke/Modell (z.B. *Vorwerk TM6* oder *Ninja DoubleStack*). Die KI optimiert alle Rezepte und Schritte exakt auf deine Hardware (z.B. TM-Varoma-Schritte, Airfryer-Garzeiten).
* **Multi-Select Allergene**: Wähle per Dropdown aus den 14 EU-Hauptallergenen und häufigen Intoleranzen (z.B. Gluten, Laktose, Nüsse, kein Schweinefleisch). Die KI schließt diese Zutaten strikt aus.
* **Weitere Präferenzen**: Freitextfeld für zusätzliche Wünsche (z.B. „Low-Carb", „saisonal").

### 5. KI-Chefkoch, Web-Scraper & Bild-Import
* **KI-Chef**: Gib einfach Zutaten oder Wünsche ein, wähle Ernährungsform oder Küchenstil, und lass dir ein Rezept generieren.
* **Web Scraper**: Trage die URL einer Koch-Webseite (z.B. Chefkoch) ein, um das Rezept direkt zu digitalisieren.
* **Foto-Import**: Lade ein Foto eines gedruckten Rezepts hoch. Die KI liest es ein und erstellt einen Entwurf.
* **Resteverwertung (Vision)**: Fotografiere deinen Kühlschrank oder deine Vorräte. Die KI erkennt die Zutaten und schlägt passende Rezepte vor.

---

## 🎴 Lovelace Dashboard Rezeptkarte

Du kannst dein Dashboard mit einer schicken Rezeptkarte verschönern, die das heute geplante Rezept direkt anzeigt.

### Installation der Karte

1. Lade die `kitchen-helper-card.js` herunter und lege sie in den `www`-Ordner deiner Home Assistant Konfiguration (z.B. `/config/www/kitchen-helper-card.js`).
2. Registriere sie unter **Einstellungen** → **Dashboards** → **Ressourcen** als JavaScript-Modul mit der URL `/local/kitchen-helper-card.js`.
3. Leere den Browser-Cache (Shift+F5).

### Karte hinzufügen (visuell, ab v1.7.0)

Ab Version 1.7.0 erscheint die Karte direkt im **„Karte hinzufügen"**-Dialog:

1. Gehe auf dein Dashboard → **Bearbeiten** → **Karte hinzufügen**.
2. Suche nach **„Kitchen Helper"** oder **„🍳"**.
3. Klicke auf die Karte – ein visueller Editor öffnet sich automatisch.

Im Editor kannst du folgendes konfigurieren:
- **Kalender-Entität**: Dropdown mit allen deinen `calendar.*`-Entitäten
- **Kartentitel**: Optionaler Freitext
- **Akzentfarbe**: Farbpicker für den Header und alle Akzente
- **Abschnitte**: Beschreibung, Zutaten und Zubereitung per Toggle ein-/ausblenden
- **Max. Höhe der Zubereitung**: Scrollbereich in Pixeln begrenzen

### Alternative: Manuelle YAML-Konfiguration

```yaml
type: custom:kitchen-helper-card
entity: calendar.dein_kochplan_kalender
title: Heutiges Rezept          # optional
accent_color: "#f59e0b"          # optional, Standardfarbe
show_description: true           # optional
show_ingredients: true           # optional
show_instructions: true          # optional
max_instruction_height: 180      # optional, in px
```


---

## ☕ Support & Spenden

Die Entwicklung und Pflege dieses Addons erfolgt in meiner Freizeit. Wenn dir der Küchenhelfer gefällt und er deinen Alltag erleichtert, freue ich mich riesig über eine kleine Unterstützung!

* **PayPal.me**: [Kaffee spendieren via paypal.me/YHolz](https://paypal.me/YHolz)

Vielen Dank für deine Unterstützung!
