class KitchenHelperCard extends HTMLElement {
  // Sets the configuration for the card
  setConfig(config) {
    if (!config.entity) {
      throw new Error('Bitte definiere eine Entität (einen Kalender)');
    }
    this.config = config;
  }

  // The height of your card. Home Assistant uses this to lay out the grid
  getCardSize() {
    return 3;
  }
  
  // Set the hass object, which contains the states of all entities
  set hass(hass) {
    this._hass = hass;
    const entityId = this.config.entity;
    const state = hass.states[entityId];
    
    // Let's render the card
    if (!this.content) {
      this.innerHTML = `
        <ha-card>
          <div class="card-content"></div>
        </ha-card>
      `;
      this.content = this.querySelector('.card-content');
      
      // Let's add styling
      const style = document.createElement('style');
      style.textContent = `
        .recipe-card {
          font-family: var(--paper-font-body1_-_font-family), sans-serif;
          background-color: var(--ha-card-background, var(--card-background-color, #1e293b));
          border-radius: var(--ha-card-border-radius, 16px);
          overflow: hidden;
          border: 1px solid var(--ha-card-border-color, var(--divider-color, #334155));
        }
        .recipe-header {
          position: relative;
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          height: 110px;
          display: flex;
          align-items: flex-end;
          padding: 16px;
        }
        .recipe-title {
          color: #0f172a;
          font-size: 20px;
          font-weight: 800;
          z-index: 1;
          margin: 0;
          line-height: 1.2;
        }
        .recipe-info {
          display: flex;
          gap: 16px;
          padding: 12px 16px;
          background-color: rgba(15, 23, 42, 0.3);
          border-bottom: 1px solid var(--divider-color, #334155);
          font-size: 12px;
          color: var(--secondary-text-color, #94a3b8);
          font-weight: 600;
        }
        .recipe-info div {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .recipe-info ha-icon {
          --mdc-icon-size: 16px;
          color: #f59e0b;
        }
        .recipe-body {
          padding: 16px;
        }
        .recipe-description {
          font-size: 13px;
          line-height: 1.5;
          color: var(--secondary-text-color, #94a3b8);
          margin-bottom: 16px;
          font-style: italic;
          border-left: 2px solid #f59e0b;
          padding-left: 8px;
        }
        .recipe-section-title {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1px;
          font-weight: 700;
          color: #f59e0b;
          margin-bottom: 8px;
          margin-top: 12px;
        }
        .recipe-ingredients {
          list-style: none;
          padding: 0;
          margin: 0 0 16px 0;
          display: grid;
          grid-template-cols: 1fr;
          gap: 6px;
        }
        @media(min-width: 400px) {
          .recipe-ingredients {
            grid-template-cols: 1fr 1fr;
            gap: 6px 12px;
          }
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
          color: #f59e0b;
        }
        .recipe-instructions {
          font-size: 12px;
          color: var(--primary-text-color, #e2e8f0);
          line-height: 1.6;
          white-space: pre-line;
          max-height: 180px;
          overflow-y: auto;
          padding-right: 6px;
          background-color: rgba(15, 23, 42, 0.2);
          padding: 10px;
          border-radius: 8px;
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
          --mdc-icon-size: 32px;
          color: #475569;
        }
      `;
      this.appendChild(style);
    }

    if (!state || state.state === 'off') {
      this.content.innerHTML = `
        <div class="recipe-card">
          <div class="no-recipe">
            <ha-icon icon="mdi:silverware-clean"></ha-icon>
            <div>Heute steht kein Gericht auf dem Plan.</div>
          </div>
        </div>
      `;
      return;
    }

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
        if (servingsMatch) {
          servings = servingsMatch[1];
        }
        
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
              const content = line.substring(1).trim(); // remove '-'
              const match = content.match(/^([\d.,\/]+)?\s*([a-zA-ZäöüÄÖÜß]+)?\s+(.+)$/);
              if (match) {
                return {
                  qty: (match[1] || '') + (match[2] ? ' ' + match[2] : ''),
                  name: match[3]
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
      console.error("Error parsing recipe description:", err);
      description = rawDescription;
    }

    const cleanTitle = title.replace(/^Kochplan:\s*/, '');
    
    this.content.innerHTML = `
      <div class="recipe-card">
        <div class="recipe-header">
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
          ${description ? `<p class="recipe-description">${description}</p>` : ''}
          
          ${ingredients.length > 0 ? `
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
          
          ${instructions ? `
            <div class="recipe-section-title">Zubereitung</div>
            <div class="recipe-instructions">${instructions}</div>
          ` : ''}
        </div>
      </div>
    `;
  }
}

customElements.define('kitchen-helper-card', KitchenHelperCard);
