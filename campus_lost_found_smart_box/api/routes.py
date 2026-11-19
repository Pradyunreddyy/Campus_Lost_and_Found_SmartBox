
from flask import Blueprint, jsonify, request

from backend import storage

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Campus Lost & Found Smart Box"
    })


@api.get("/items")
def get_items():
    items = storage.list_items()
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify({"items": items})


@api.post("/items")
def add_item():
    data = request.get_json(silent=True) or {}

    if not data.get("name") or not data.get("location"):
        return jsonify({
            "error": "Item name and location are required."
        }), 400

    item = storage.create_item(data)

    return jsonify({
        "message": "Item registered.",
        "item": item
    }), 201


@api.patch("/items/<item_id>")
def edit_item(item_id):
    data = request.get_json(silent=True) or {}

    allowed = {"status", "location", "description"}
    changes = {
        key: value
        for key, value in data.items()
        if key in allowed
    }

    if not changes:
        return jsonify({
            "error": "No supported changes supplied."
        }), 400

    item = storage.update_item(item_id, changes)

    if not item:
        return jsonify({"error": "Item not found."}), 404

    return jsonify({"item": item})


@api.post("/rfid/scan")
def rfid_scan():
    data = request.get_json(silent=True) or {}

    tag = (data.get("tag") or "").strip()
    action = data.get("action")

    if not tag or action not in {"checkin", "checkout"}:
        return jsonify({
            "error": "A tag ID and valid scan action are required."
        }), 400

    item = storage.find_by_rfid(tag)

    if not item:
        return jsonify({
            "error": "No item is registered with this RFID tag. Add the item first."
        }), 404

    if action == "checkin":
        updated = storage.update_item(
            item["id"],
            {
                "status": "In Smart Box",
                "box_checked_in": True
            }
        )

        message = f"{item['name']} checked into the Smart Box."
        display = "ITEM CHECKED IN"

    else:
        updated = storage.update_item(
            item["id"],
            {
                "status": "Found",
                "box_checked_in": False
            }
        )

        message = f"{item['name']} checked out of the Smart Box."
        display = "ITEM CHECKED OUT"

    # Publish the RFID event to AWS IoT Core.
    mqtt_published = False
    mqtt_error = None

    try:
        from backend.iot_client import publish_event

        publish_event({
            "device": "CampusSmartBox",
            "tag": tag,
            "action": action,
            "item_id": item["id"],
            "item_name": item["name"],
            "status": updated["status"]
        })

        mqtt_published = True

    except Exception as error:
        # Keep the successful item update even if MQTT is unavailable.
        mqtt_error = str(error)
        print(f"AWS IoT MQTT publishing failed: {mqtt_error}")

    return jsonify({
        "message": message,
        "display": display,
        "item": updated,
        "device": "simulated ESP32 RFID",
        "mqtt_published": mqtt_published,
        "mqtt_error": mqtt_error
    })
