from datetime import timedelta

DOMAIN = "pantry"
STORAGE_KEY = "pantry_data"
STORAGE_VERSION = 1
DATA_STORAGE = "storage"
ATTR_ITEM_ID = "item_id"
ATTR_NAME = "name"
ATTR_QUANTITY = "quantity"
ATTR_MIN_QUANTITY = "min_quantity"
ATTR_EXPIRATIONS = "expirations"

DEFAULT_SCAN_INTERVAL = timedelta(hours=6)