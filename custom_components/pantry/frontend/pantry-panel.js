import { LitElement, html, css } from 'https://unpkg.com/lit?module';

class PantryPanel extends LitElement {
  static get properties() {
    return {
      items: { type: Array },
      filter: { type: String },
      newItem: { type: Object }
    };
  }

  constructor() {
    super();
    this.items = [];
    this.filter = "all";
    this.newItem = { name: "", quantity: 0, min_quantity: 0, expiration_dates: [] };
    this.loadData();
  }

  static get styles() {
    return css`
      .expired { background: #f8d7da; }
      .near-expired { background: #fff3cd; }
      .low-quantity { background: #d1ecf1; }
      button { margin: 0.2rem; }
      input { margin: 0.2rem; }
    `;
  }

  async loadData() {
    try {
      const response = await fetch('/api/pantry/items');
      const data = await response.json();
      this.items = data.items || [];
    } catch (e) {
      console.error("Error loading pantry data", e);
    }
  }

  async addItem() {
    try {
      await fetch('/api/pantry/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.newItem)
      });
      this.newItem = { name: "", quantity: 0, min_quantity: 0, expiration_dates: [] };
      this.loadData();
    } catch (e) {
      console.error("Error adding item", e);
    }
  }

  async updateItem(item) {
    try {
      await fetch('/api/pantry/items', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item)
      });
      this.loadData();
    } catch (e) {
      console.error("Error updating item", e);
    }
  }

  async deleteItem(item) {
    try {
      await fetch('/api/pantry/items', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: item.id })
      });
      this.loadData();
    } catch (e) {
      console.error("Error deleting item", e);
    }
  }

  isExpired(expDate) {
    const today = new Date();
    const date = new Date(expDate);
    return date < today;
  }

  isNearExpired(expDate) {
    const today = new Date();
    const date = new Date(expDate);
    const diffDays = (date - today) / (1000 * 60 * 60 * 24);
    return diffDays >= 0 && diffDays <= 3;
  }

  render() {
    return html`
      <div>
        <h2>Add Item</h2>
        <div>
          <input type="text" placeholder="Name" .value="${this.newItem.name}"
            @input="${e => this.newItem.name = e.target.value}" />
          <input type="number" placeholder="Quantity" .value="${this.newItem.quantity}"
            @input="${e => this.newItem.quantity = parseInt(e.target.value)}" />
          <input type="number" placeholder="Min Quantity" .value="${this.newItem.min_quantity}"
            @input="${e => this.newItem.min_quantity = parseInt(e.target.value)}" />
          <input type="text" placeholder="Expiration Dates (comma-separated YYYY-MM-DD)"
            @input="${e => {
              this.newItem.expiration_dates = e.target.value.split(',').map(s => s.trim());
            }}" />
          <button @click="${this.addItem}">Add</button>
        </div>
      </div>
      <div>
        <h2>Pantry Items</h2>
        <div>
          <label>Filter:
            <select @change="${e => { this.filter = e.target.value; }}">
              <option value="all">All</option>
              <option value="expired">Expired</option>
              <option value="near_expired">Near Expired</option>
              <option value="low_quantity">Low Quantity</option>
            </select>
          </label>
        </div>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Quantity</th>
              <th>Min Quantity</th>
              <th>Expiration Dates</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${this.items.filter(item => {
              if (this.filter === "expired") {
                return item.expiration_dates.some(date => this.isExpired(date));
              } else if (this.filter === "near_expired") {
                return item.expiration_dates.some(date => this.isNearExpired(date));
              } else if (this.filter === "low_quantity") {
                return item.quantity < item.min_quantity;
              }
              return true;
            }).map(item => html`
              <tr>
                <td>${item.name}</td>
                <td>
                  <input type="number" .value="${item.quantity}"
                    @change="${e => { item.quantity = parseInt(e.target.value); this.updateItem(item); }}" />
                </td>
                <td>
                  <input type="number" .value="${item.min_quantity}"
                    @change="${e => { item.min_quantity = parseInt(e.target.value); this.updateItem(item); }}" />
                </td>
                <td>
                  <input type="text" .value="${item.expiration_dates.join(', ')}"
                    @change="${e => { item.expiration_dates = e.target.value.split(',').map(s => s.trim()); this.updateItem(item); }}" />
                </td>
                <td>
                  <button @click="${() => this.deleteItem(item)}">Delete</button>
                </td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }
}

customElements.define('pantry-panel', PantryPanel);
