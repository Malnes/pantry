import { LitElement, html, css } from 'lit';
import '@material/web/button/text-button.js';
import '@material/web/dialog/dialog.js';
import '@material/web/textfield/outlined-text-field.js';
import '@material/web/datepicker/date-picker.js';

class PantryPanel extends LitElement {
  static properties = {
    hass: {},
    items: { type: Array },
    _activeTab: { type: Number },
    _editIndex: { type: Number },
    _showDialog: { type: Boolean },
    _dialogType: { type: String },
    _formData: { type: Object }
  };

  static styles = css`
    :host {
      display: block;
      padding: 16px;
    }
    
    .container {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    }
    
    .item-card {
      padding: 16px;
      border-radius: 8px;
      background: var(--card-background-color);
      box-shadow: var(--box-shadow);
    }
    
    .expiration-dates {
      margin-top: 8px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    
    .date {
      padding: 4px 8px;
      border-radius: 4px;
      background: var(--warning-color);
      font-size: 0.8em;
    }
    
    .actions {
      margin-top: 12px;
      display: flex;
      gap: 8px;
    }
    
    @media (max-width: 600px) {
      .container {
        grid-template-columns: 1fr;
      }
    }
    
    /* Dialog styles */
    md-dialog {
      --md-dialog-container-color: var(--card-background-color);
      --md-dialog-headline-color: var(--primary-text-color);
    }

    /* Add these to the styles in pantry-panel.js */
    .warning {
      color: var(--error-color);
      font-weight: bold;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .date.warning {
      background: var(--error-color);
      color: white;
    }

    @media (max-width: 480px) {
      :host {
        padding: 8px;
      }
      
      .item-card {
        padding: 12px;
      }
      
      md-dialog {
        --md-dialog-container-max-inline-size: 100vw;
      }
    }
  `;

  constructor() {
    super();
    this.items = [];
    this._activeTab = 0;
    this._showDialog = false;
    this._formData = this._emptyForm();
  }

  firstUpdated() {
    this._fetchItems();
  }

  async _fetchItems() {
    const data = await this.hass.callWS({
      type: 'pantry/get_items'
    });
    this.items = data.items.map(item => ({
      ...item,
      expiration_dates: item.expiration_dates.sort((a, b) => new Date(a) - new Date(b))
    }));
  }

  _emptyForm() {
    return {
      name: '',
      quantity: 0,
      min_quantity: 0,
      expiration_dates: []
    };
  }

  _openDialog(type, index = -1) {
    this._dialogType = type;
    this._editIndex = index;
    this._formData = index >= 0 ? { ...this.items[index] } : this._emptyForm();
    this._showDialog = true;
  }

  _closeDialog() {
    this._showDialog = false;
    this._formData = this._emptyForm();
  }

  async _saveItem() {
    try {
      if (this._dialogType === 'add') {
        await this.hass.callService('pantry', 'add_item', this._formData);
      } else {
        await this.hass.callService('pantry', 'update_item', {
          item_id: this._editIndex,
          item: this._formData
        });
      }
      this._closeDialog();
      await this._fetchItems();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  }

  async _deleteItem(index) {
    if (confirm('Are you sure you want to delete this item?')) {
      await this.hass.callService('pantry', 'delete_item', { item_id: index });
      await this._fetchItems();
    }
  }

  _renderDialog() {
    return html`
      <md-dialog open ?hidden=${!this._showDialog}>
        <div slot="headline">${this._dialogType === 'add' ? 'Add' : 'Edit'} Item</div>
        
        <div slot="content">
          <md-outlined-text-field
            label="Name"
            .value=${this._formData.name}
            @input=${e => this._formData.name = e.target.value}
          ></md-outlined-text-field>
          
          <md-outlined-text-field
            label="Quantity"
            type="number"
            .value=${this._formData.quantity}
            @input=${e => this._formData.quantity = parseInt(e.target.value)}
          ></md-outlined-text-field>
          
          <md-outlined-text-field
            label="Minimum Quantity"
            type="number"
            .value=${this._formData.min_quantity}
            @input=${e => this._formData.min_quantity = parseInt(e.target.value)}
          ></md-outlined-text-field>
          
          <date-picker
            multiple
            .value=${this._formData.expiration_dates}
            @change=${e => this._formData.expiration_dates = e.target.value}
          ></date-picker>
        </div>
        
        <div slot="actions">
          <md-text-button @click=${this._closeDialog}>Cancel</md-text-button>
          <md-text-button @click=${this._saveItem}>Save</md-text-button>
        </div>
      </md-dialog>
    `;
  }

  _renderItem(item, index) {
    const lowStock = item.quantity < item.min_quantity;
    const expiringSoon = item.expiration_dates.some(date => {
      const diffDays = Math.ceil((new Date(date) - new Date()) / (1000 * 60 * 60 * 24));
      return diffDays <= 30;
    });

    return html`
      <div class="item-card">
        <h3>${item.name}</h3>
        <div class=${lowStock ? 'warning' : ''}>
          Quantity: ${item.quantity}/${item.min_quantity}
        </div>
        <div class="expiration-dates">
          ${item.expiration_dates.map(date => html`
            <div class="date ${this._isExpiringSoon(date) ? 'warning' : ''}">
              ${new Date(date).toLocaleDateString()}
            </div>
          `)}
        </div>
        <div class="actions">
          <md-text-button @click=${() => this._openDialog('edit', index)}>
            Edit
          </md-text-button>
          <md-text-button class="delete" @click=${() => this._deleteItem(index)}>
            Delete
          </md-text-button>
        </div>
      </div>
    `;
  }

  _isExpiringSoon(date) {
    const diffDays = Math.ceil((new Date(date) - new Date()) / (1000 * 60 * 60 * 24));
    return diffDays <= 30;
  }

  render() {
    const filteredItems = this.items.filter(item => {
      if (this._activeTab === 1) { // Expiring Soon
        return item.expiration_dates.some(date => this._isExpiringSoon(date));
      }
      if (this._activeTab === 2) { // Low Stock
        return item.quantity < item.min_quantity;
      }
      return true;
    });

    return html`
      <div class="header">
        <h1>Pantry Management</h1>
        <md-text-button @click=${() => this._openDialog('add')}>
          Add Item
        </md-text-button>
      </div>

      <md-tabs @change=${e => this._activeTab = e.detail.activeTabIndex}>
        <md-tab>All Items</md-tab>
        <md-tab>Expiring Soon</md-tab>
        <md-tab>Low Stock</md-tab>
      </md-tabs>

      <div class="container">
        ${filteredItems.map((item, index) => this._renderItem(item, index))}
      </div>

      ${this._renderDialog()}
    `;
  }
}

customElements.define('pantry-panel', PantryPanel);