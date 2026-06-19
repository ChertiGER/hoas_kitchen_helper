// ============================================================
//  Kitchen Helper Card  –  v1.7.0
//  Visuelle Lovelace-Karte für den Küchenhelfer-Addon
// ============================================================

// --------------- CARD EDITOR --------------------------------
class KitchenHelperCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  // Gibt alle calendar.*-Entitäten zurück
  _getCalendarEntities() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states)
      .filter(id => id.startsWith('calendar.'))
      .sort();
  }

  _render() {
    if (!this._hass) return;

    const entities = this._getCalendarEntities();
    const current = this._config.entity || '';
    const title = this._config.title || '';
    const showIngredients = this._config.show_ingredients !== false;
    const showInstructions = this._config.show_instructions !== false;
    const showDescription = this._config.show_description !== false;
    const accentColor = this._config.accent_color || '#f59e0b';
    const maxInstructionHeight = this._config.max_instruction_height || 180;

    this.innerHTML = `
      <style>
        .kh-editor {
          display: flex;
          flex-direction: column;
          gap: 16px;
          padding: 4px 0;
        }
        .kh-editor .row {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .kh-editor label {
          font-size: 12px;
          font-weight: 600;
          color: var(--secondary-text-color);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .kh-editor select,
        .kh-editor input[type="text"],
        .kh-editor input[type="color"],
        .kh-editor input[type="number"] {
          width: 100%;
          padding: 8px 10px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #334155);
          background: var(--card-background-color, #1e293b);
          color: var(--primary-text-color);
          font-size: 14px;
          box-sizing: border-box;
        }
        .kh-editor input[type="color"] {
          padding: 2px 4px;
          height: 38px;
          cursor: pointer;
        }
        .kh-editor .toggle-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 6px 0;
          border-bottom: 1px solid var(--divider-color, rgba(255,255,255,0.07));
        }
        .kh-editor .toggle-row:last-child {
          border-bottom: none;
        }
        .kh-editor .toggle-label {
          font-size: 14px;
          color: var(--primary-text-color);
        }
        .kh-editor .section-title {
          font-size: 13px;
          font-weight: 700;
          color: var(--accent-color, #f59e0b);
          margin-top: 4px;
          padding-bottom: 4px;
          border-bottom: 1px solid var(--divider-color, rgba(255,255,255,0.1));
        }
        ha-switch { --mdc-theme-secondary: var(--accent-color, #f59e0b); }
      </style>
      <div class="kh-editor">
        <div class="section-title">📋 Basiseinstellungen</div>

        <div class="row">
          <label for="kh-entity">Kalender-Entität *</label>
          <select id="kh-entity">
            <option value="">– Entität wählen –</option>
            ${entities.map(e => `<option value="${e}" ${e === current ? 'selected' : ''}>${e}</option>`).join('')}
          </select>
        </div>

        <div class="row">
          <label for="kh-title">Kartentitel (optional)</label>
          <input type="text" id="kh-title" placeholder="z.B. Heutiges Rezept" value="${title}">
        </div>

        <div class="section-title">🎨 Erscheinungsbild</div>

        <div class="row">
          <label for="kh-color">Akzentfarbe</label>
          <input type="color" id="kh-color" value="${accentColor}">
        </div>

        <div class="row">
          <label for="kh-height">Max. Höhe Zubereitung (px)</label>
          <input type="number" id="kh-height" min="60" max="600" step="20" value="${maxInstructionHeight}">
        </div>

        <div class="section-title">👁 Abschnitte anzeigen</div>

        <div class="toggle-row">
          <span class="toggle-label">Beschreibung anzeigen</span>
          <ha-switch id="kh-desc" ${showDescription ? 'checked' : ''}></ha-switch>
        </div>
        <div class="toggle-row">
          <span class="toggle-label">Zutaten anzeigen</span>
          <ha-switch id="kh-ing" ${showIngredients ? 'checked' : ''}></ha-switch>
        </div>
        <div class="toggle-row">
          <span class="toggle-label">Zubereitung anzeigen</span>
          <ha-switch id="kh-instr" ${showInstructions ? 'checked' : ''}></ha-switch>
        </div>
      </div>
    `;

    this.querySelector('#kh-entity').addEventListener('change', e => this._valueChanged('entity', e.target.value));
    this.querySelector('#kh-title').addEventListener('input', e => this._valueChanged('title', e.target.value));
    this.querySelector('#kh-color').addEventListener('input', e => this._valueChanged('accent_color', e.target.value));
    this.querySelector('#kh-height').addEventListener('input', e => this._valueChanged('max_instruction_height', parseInt(e.target.value) || 180));
    this.querySelector('#kh-desc').addEventListener('change', e => this._valueChanged('show_description', e.target.checked));
    this.querySelector('#kh-ing').addEventListener('change', e => this._valueChanged('show_ingredients', e.target.checked));
    this.querySelector('#kh-instr').addEventListener('change', e => this._valueChanged('show_instructions', e.target.checked));
  }

  _valueChanged(key, value) {
    if (!this._config) return;
    if (value === '' || value === undefined) {
      const newConfig = { ...this._config };
      delete newConfig[key];
      this._config = newConfig;
    } else {
      this._config = { ...this._config, [key]: value };
    }
    // Feuert Event, das Home Assistant aufgreift
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    }));
  }
}

customElements.define('kitchen-helper-card-editor', KitchenHelperCardEditor);

// --------------- MAIN CARD ----------------------------------
class KitchenHelperCard extends HTMLElement {
  // Gibt Home Assistant die Standardkonfiguration für den "Karte hinzufügen"-Dialog
  static getStubConfig(hass) {
    const calendarEntity = Object.keys(hass.states).find(id => id.startsWith('calendar.'));
    return {
      type: 'custom:kitchen-helper-card',
      entity: calendarEntity || 'calendar.kochplan',
      title: '',
      show_description: true,
      show_ingredients: true,
      show_instructions: true,
      accent_color: '#f59e0b',
      max_instruction_height: 180,
    };
  }

  // Gibt den visuellen Editor zurück
  static getConfigElement() {
    return document.createElement('kitchen-helper-card-editor');
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Bitte eine Kalender-Entität konfigurieren.');
    }
    this.config = config;
    this._accentColor = config.accent_color || '#f59e0b';
  }

  getCardSize() {
    return 4;
  }

  set hass(hass) {
    this._hass = hass;
    const entityId = this.config.entity;
    const state = hass.states[entityId];
    const accent = this._accentColor;

    if (!this.content) {
      this.innerHTML = `<ha-card><div class="card-content"></div></ha-card>`;
      this.content = this.querySelector('.card-content');

      const style = document.createElement('style');
      style.textContent = `
        :host {
          --kh-accent: ${accent};
        }
        .recipe-card {
          font-family: var(--paper-font-body1_-_font-family), sans-serif;
          background-color: var(--ha-card-background, var(--card-background-color, #1e293b));
          border-radius: var(--ha-card-border-radius, 16px);
          overflow: hidden;
          border: 1px solid var(--ha-card-border-color, var(--divider-color, #334155));
        }
        .recipe-header {
          position: relative;
          background: linear-gradient(135deg, var(--kh-accent, #f59e0b) 0%, color-mix(in srgb, var(--kh-accent, #f59e0b) 75%, black) 100%);
          min-height: 100px;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          justify-content: flex-end;
          padding: 16px;
          gap: 4px;
        }
        .recipe-title {
          color: #0f172a;
          font-size: 20px;
          font-weight: 800;
          margin: 0;
          line-height: 1.2;
          word-break: break-word;
          overflow-wrap: break-word;
        }
        .recipe-subtitle {
          color: rgba(15, 23, 42, 0.7);
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.5px;
          text-transform: uppercase;
          margin: 0;
        }
        .recipe-info {
          display: flex;
          gap: 16px;
          padding: 10px 16px;
          background-color: rgba(15, 23, 42, 0.3);
          border-bottom: 1px solid var(--divider-color, #334155);
          font-size: 12px;
          color: var(--secondary-text-color, #94a3b8);
          font-weight: 600;
          flex-wrap: wrap;
        }
        .recipe-info div {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .recipe-info ha-icon {
          --mdc-icon-size: 16px;
          color: var(--kh-accent, #f59e0b);
        }
        .recipe-body { padding: 16px; }
        .recipe-description {
          font-size: 13px;
          line-height: 1.5;
          color: var(--secondary-text-color, #94a3b8);
          margin-bottom: 16px;
          font-style: italic;
          border-left: 2px solid var(--kh-accent, #f59e0b);
          padding-left: 8px;
        }
        .recipe-section-title {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1px;
          font-weight: 700;
          color: var(--kh-accent, #f59e0b);
          margin-bottom: 8px;
          margin-top: 12px;
        }
        .recipe-ingredients {
          list-style: none;
          padding: 0;
          margin: 0 0 16px 0;
          display: grid;
          grid-template-columns: 1fr;
          gap: 6px;
        }
        @media (min-width: 400px) {
          .recipe-ingredients { grid-template-columns: 1fr 1fr; gap: 6px 12px; }
        }
        .recipe-ingredients li {
          font-size: 12px;
          color: var(--primary-text-color, #e2e8f0);
          display: flex;
          justify-content: space-between;
          border-bottom: 1px dashed var(--divider-color, #334155);
          padding-bottom: 3px;
        }
        .recipe-ingredients li .ing-qty {
          font-weight: 700;
          color: var(--kh-accent, #f59e0b);
        }
        .recipe-instructions {
          font-size: 12px;
          color: var(--primary-text-color, #e2e8f0);
          line-height: 1.6;
          white-space: pre-line;
          overflow-y: auto;
          padding: 10px;
          border-radius: 8px;
          background-color: rgba(15, 23, 42, 0.2);
          border: 1px solid rgba(245, 158, 11, 0.1);
        }
        .no-recipe {
          padding: 32px 16px;
          text-align: center;
          color: var(--secondary-text-color, #94a3b8);
          font-style: italic;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }
        .no-recipe ha-icon {
          --mdc-icon-size: 40px;
          color: #475569;
        }
        .no-recipe .no-recipe-hint {
          font-size: 12px;
          opacity: 0.6;
        }
      `;
      this.appendChild(style);
    }

    // CSS-Variable dynamisch aktualisieren wenn Farbe in Config geändert wurde
    if (this.config.accent_color) {
      this.style.setProperty('--kh-accent', this.config.accent_color);
    }

    if (!state || state.state === 'off' || state.state === 'unavailable') {
      const cardTitle = this.config.title || '';
      this.content.innerHTML = `
        <div class="recipe-card">
          ${cardTitle ? `<div class="recipe-header"><h2 class="recipe-title">${cardTitle}</h2></div>` : ''}
          <div class="no-recipe">
            <ha-icon icon="mdi:silverware-clean"></ha-icon>
            <div>Heute steht kein Gericht auf dem Plan.</div>
            <div class="no-recipe-hint">Entität: ${entityId}</div>
          </div>
        </div>
      `;
      return;
    }

    const cardTitle = this.config.title || '';
    const showDescription = this.config.show_description !== false;
    const showIngredients = this.config.show_ingredients !== false;
    const showInstructions = this.config.show_instructions !== false;
    const maxHeight = this.config.max_instruction_height || 180;

    const title = state.attributes.message || 'Heutiges Gericht';
    const rawDescription = state.attributes.description || '';

    let description = '';
    let servings = '';
    let ingredients = [];
    let instructions = '';

    try {
      if (rawDescription) {
        const sections = rawDescription.split('\n\n');
        description = sections[0] || '';

        const servingsMatch = rawDescription.match(/Geplante Portionen:\s*(\d+)/);
        if (servingsMatch) servings = servingsMatch[1];

        const zutatenIndex = rawDescription.indexOf('ZUTATEN:');
        const zubereitungIndex = rawDescription.indexOf('ZUBEREITUNG:');

        if (zutatenIndex !== -1) {
          const zutatenBlock = zubereitungIndex !== -1
            ? rawDescription.substring(zutatenIndex + 8, zubereitungIndex)
            : rawDescription.substring(zutatenIndex + 8);

          ingredients = zutatenBlock.split('\n')
            .map(line => line.trim())
            .filter(line => line.startsWith('-'))
            .map(line => {
              const content = line.substring(1).trim();
              const match = content.match(/^([\d.,\/]+)?\s*([a-zA-ZäöüÄÖÜß]+)?\s+(.+)$/);
              if (match) {
                return {
                  qty: (match[1] || '') + (match[2] ? ' ' + match[2] : ''),
                  name: match[3],
                };
              }
              return { qty: '', name: content };
            });
        }

        if (zubereitungIndex !== -1) {
          instructions = rawDescription.substring(zubereitungIndex + 12).trim();
        }
      }
    } catch (err) {
      console.error('Kitchen Helper Card: Error parsing recipe description:', err);
      description = rawDescription;
    }

    const cleanTitle = title.replace(/^Kochplan:\s*/, '');

    this.content.innerHTML = `
      <div class="recipe-card">
        <div class="recipe-header">
          ${cardTitle ? `<p class="recipe-subtitle">${cardTitle}</p>` : ''}
          <h2 class="recipe-title">${cleanTitle}</h2>
        </div>
        <div class="recipe-info">
          <div>
            <ha-icon icon="mdi:account-group"></ha-icon>
            <span>${servings ? servings + ' Portionen' : 'Portionen n.a.'}</span>
          </div>
          <div>
            <ha-icon icon="mdi:calendar-star"></ha-icon>
            <span>Kochplan für heute</span>
          </div>
        </div>
        <div class="recipe-body">
          ${showDescription && description ? `<p class="recipe-description">${description}</p>` : ''}

          ${showIngredients && ingredients.length > 0 ? `
            <div class="recipe-section-title">Zutaten</div>
            <ul class="recipe-ingredients">
              ${ingredients.map(ing => `
                <li>
                  <span class="ing-name">${ing.name}</span>
                  <span class="ing-qty">${ing.qty}</span>
                </li>
              `).join('')}
            </ul>
          ` : ''}

          ${showInstructions && instructions ? `
            <div class="recipe-section-title">Zubereitung</div>
            <div class="recipe-instructions" style="max-height:${maxHeight}px">${instructions}</div>
          ` : ''}
        </div>
      </div>
    `;
  }
}

customElements.define('kitchen-helper-card', KitchenHelperCard);

// Registrierung im Home Assistant Lovelace-Card-Picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'kitchen-helper-card',
  name: '🍳 Kitchen Helper',
  description: 'Zeigt das heutige Rezept aus dem Küchenhelfer-Addon an.',
  preview: true,
  documentationURL: 'https://github.com/YannickHolz/hoas_kitchen_helper',
});
