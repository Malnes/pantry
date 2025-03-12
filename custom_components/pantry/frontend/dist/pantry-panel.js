// Add these AT THE TOP of pantry-panel.js
import { LitElement, html, css } from 'https://unpkg.com/lit@2.6.1/index.js?module';
import { mdiAlert, mdiFoodDrumstick, mdiPlus, mdiDelete, mdiPencil } from 'https://unpkg.com/@mdi/js@6.5.95/mdi.js?module';

// Material Web Components imports
import '@material/mwc-button';
import '@material/mwc-dialog';
import '@material/mwc-fab';
import '@material/mwc-icon-button';
import '@material/mwc-textfield';

export function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
}

class PantryPanel extends LitElement {
  static properties = {
    items: { type: Array },
    alerts: { type: Object },
    activeTab: { type: String },
    editItem: { type: Object },
    showDialog: { type: Boolean }
  };

  static styles = css`
    :host {
      padding: 16px;
      display: block;
    }
    .tab-content {
      margin-top: 16px;
    }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    }
    .card {
      padding: 16px;
      border-radius: 8px;
      background: var(--card-background-color);
      box-shadow: var(--box-shadow);
    }
    .expiration-list {
      margin-top: 8px;
    }
    .alert {
      color: var(--error-color);
    }
    .fab {
      position: fixed;
      bottom: 24px;
      right: 24px;
    }
    @media (max-width: 600px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  `;

  constructor() {
    super();
    this.items = [];
    this.alerts = { expiring: [], lowStock: [] };
    this.activeTab = 'items';
    this.editItem = null;
    this.showDialog = false;
  }

  firstUpdated() {
    this._loadData();
  }

  async _loadData() {
    const response = await fetch('/api/pantry/data');
    const data = await response.json();
    this.items = Object.entries(data.items).map(([id, item]) => ({ id, ...item }));
    this._calculateAlerts();
  }

  _calculateAlerts() {
    const now = new Date();
    const thirtyDays = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    
    this.alerts = {
      expiring: this.items.flatMap(item => 
        item.expirations
          .filter(date => new Date(date) < thirtyDays)
          .map(date => ({ ...item, date }))
      ),
      lowStock: this.items.filter(item => item.quantity < item.min_quantity)
    };
  }

  _openEditDialog(item = null) {
    this.editItem = item ? { ...item } : {
      name: '',
      quantity: 0,
      min_quantity: 0,
      expirations: []
    };
    this.showDialog = true;
  }

  render() {
    return html`
      <div class="container">
        <div class="tabs">
          <button @click=${() => this.activeTab = 'items'} ?active=${this.activeTab === 'items'}>
            All Items
          </button>
          <button @click=${() => this.activeTab = 'alerts'} ?active=${this.activeTab === 'alerts'}>
            Alerts (${this.alerts.expiring.length + this.alerts.lowStock.length})
          </button>
        </div>

        ${this.activeTab === 'items' ? this._renderItems() : this._renderAlerts()}
        
        <mwc-fab class="fab" icon="add" @click=${() => this._openEditDialog()}></mwc-fab>
        
        ${this.showDialog ? this._renderEditDialog() : ''}
      </div>
    `;
  }

  _renderItems() {
    return html`
      <div class="grid">
        ${this.items.map(item => html`
          <div class="card">
            <h3>${item.name}</h3>
            <div>Quantity: ${item.quantity}/${item.min_quantity}</div>
            <div class="expiration-list">
              ${item.expirations.map(date => html`
                <div>${formatDate(date)}</div>
              `)}
            </div>
            <div class="actions">
              <mwc-icon-button icon="edit" @click=${() => this._openEditDialog(item)}></mwc-icon-button>
              <mwc-icon-button icon="delete" @click=${() => this._deleteItem(item.id)}></mwc-icon-button>
            </div>
          </div>
        `)}
      </div>
    `;
  }

  async _deleteItem(itemId) {
    await fetch('/api/services/pantry/delete_item', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId })
    });
    this._loadData();
  }

  _renderEditDialog() {
    return html`
      <mwc-dialog open>
        <div class="dialog-content">
          <mwc-textfield label="Name" .value=${this.editItem.name}></mwc-textfield>
          <mwc-textfield label="Quantity" type="number" .value=${this.editItem.quantity}></mwc-textfield>
          <mwc-textfield label="Min Quantity" type="number" .value=${this.editItem.min_quantity}></mwc-textfield>
          <div class="expiration-dates">
            ${this.editItem.expirations.map((date, index) => html`
              <div>
                <input type="date" .value=${date}>
                <mwc-icon-button icon="delete" @click=${() => this._removeDate(index)}></mwc-icon-button>
              </div>
            `)}
            <mwc-button @click=${this._addDate}>Add Expiration Date</mwc-button>
          </div>
        </div>
        <mwc-button slot="primaryAction" @click=${this._saveItem}>Save</mwc-button>
        <mwc-button slot="secondaryAction" @click=${() => this.showDialog = false}>Cancel</mwc-button>
      </mwc-dialog>
    `;
  }

  _addDate() {
    this.editItem.expirations = [...this.editItem.expirations, new Date().toISOString().split('T')[0]];
    this.requestUpdate();
  }

  _removeDate(index) {
    this.editItem.expirations.splice(index, 1);
    this.requestUpdate();
  }

  async _saveItem() {
    const service = this.editItem.id ? 'update_item' : 'add_item';
    const data = {
      ...this.editItem,
      expirations: this.editItem.expirations
    };
    
    if (this.editItem.id) data.item_id = this.editItem.id;
    
    await fetch(`/api/services/pantry/${service}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    this.showDialog = false;
    this._loadData();
  }
}

customElements.define('pantry-panel', PantryPanel);