from homeassistant.components.http import HomeAssistantView
from aiohttp import web
import json
import uuid

from .const import DOMAIN
from . import load_data, save_data

class PantryDataView(HomeAssistantView):
    url = "/api/pantry/items"
    name = "api:pantry:items"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]
        data = load_data(hass)
        return web.json_response(data)

    async def post(self, request):
        hass = request.app["hass"]
        try:
            req = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        data = load_data(hass)
        item = req
        item["id"] = str(uuid.uuid4())
        if "expiration_dates" not in item:
            item["expiration_dates"] = []
        data["items"].append(item)
        save_data(hass, data)
        sensor = hass.data.get(DOMAIN, {}).get("sensor")
        if sensor:
            sensor.update_data(data)
        return web.json_response(item, status=201)

    async def put(self, request):
        hass = request.app["hass"]
        try:
            req = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        item_id = req.get("id")
        if not item_id:
            return web.json_response({"error": "Missing id"}, status=400)
        data = load_data(hass)
        updated = False
        for idx, item in enumerate(data["items"]):
            if item.get("id") == item_id:
                data["items"][idx] = req
                updated = True
                break
        if not updated:
            return web.json_response({"error": "Item not found"}, status=404)
        save_data(hass, data)
        sensor = hass.data.get(DOMAIN, {}).get("sensor")
        if sensor:
            sensor.update_data(data)
        return web.json_response(req, status=200)

    async def delete(self, request):
        hass = request.app["hass"]
        try:
            req = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        item_id = req.get("id")
        if not item_id:
            return web.json_response({"error": "Missing id"}, status=400)
        data = load_data(hass)
        new_items = [item for item in data["items"] if item.get("id") != item_id]
        if len(new_items) == len(data["items"]):
            return web.json_response({"error": "Item not found"}, status=404)
        data["items"] = new_items
        save_data(hass, data)
        sensor = hass.data.get(DOMAIN, {}).get("sensor")
        if sensor:
            sensor.update_data(data)
        return web.json_response({"message": "Item deleted"}, status=200)
