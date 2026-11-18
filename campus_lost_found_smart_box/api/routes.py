from flask import Blueprint, jsonify, request
from backend import storage

api = Blueprint("api", __name__)

@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Campus Lost & Found Smart Box"})

@api.get("/items")
def get_items():
    items = storage.list_items()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify({"items": items})

@api.post("/items")
def add_item():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("location"):
        return jsonify({"error": "Item name and location are required."}), 400
    item = storage.create_item(data)
    return jsonify({"message": "Item registered.", "item": item}), 201

@api.patch("/items/<item_id>")
def edit_item(item_id):
    data = request.get_json(silent=True) or {}
    allowed = {"status", "location", "description"}
    changes = {key: value for key, value in data.items() if key in allowed}
    if not changes:
        return jsonify({"error": "No supported changes supplied."}), 400
    item = storage.update_item(item_id, changes)
    if not item:
        return jsonify({"error": "Item not found."}), 404
    return jsonify({"item": item})

@api.post("/rfid/scan")
def rfid_scan():
    data = request.get_json(silent=True) or {}
    tag, action = (data.get("tag") or "").strip(), data.get("action")
    if not tag or action not in {"checkin", "checkout"}:
        return jsonify({"error": "A tag ID and valid scan action are required."}), 400
    item = storage.find_by_rfid(tag)
    if not item:
        return jsonify({"error": "No item is registered with this RFID tag. Add the item first."}), 404
    if action == "checkin":
        updated = storage.update_item(item["id"], {"status": "In Smart Box", "box_checked_in": True})
        message, display = f"{item['name']} checked into the Smart Box.", "ITEM CHECKED IN"
    else:
        updated = storage.update_item(item["id"], {"status": "Found", "box_checked_in": False})
        message, display = f"{item['name']} checked out of the Smart Box.", "ITEM CHECKED OUT"
    # A real ESP32 integration can publish this event to AWS IoT Core.
    return jsonify({"message": message, "display": display, "item": updated, "device": "simulated ESP32 RFID"})
