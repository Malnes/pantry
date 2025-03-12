# Pantry Integration

Track emergency pantry items with expiration dates and quantity alerts.

![Screenshot](https://example.com/screenshot.png) <!-- Add real screenshot later -->

## Features
- Track items with multiple expiration dates
- Low quantity alerts
- Expiration date warnings (30-day threshold)
- Mobile-friendly interface
- Dark mode support

## Installation
1. Install via HACS
2. Add to sidebar through the Home Assistant panel manager
3. Start adding items through the UI

## Service Calls
```yaml
# Example service calls
service: pantry.add_item
data:
  name: "Canned Beans"
  quantity: 5
  min_quantity: 3
  expirations: ["2024-12-31"]
```