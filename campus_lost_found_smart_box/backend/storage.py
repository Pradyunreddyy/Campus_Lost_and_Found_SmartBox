"""Storage adapter: local JSON for a simple demo, DynamoDB when configured."""
import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4
from datetime import datetime, timezone

DATA_FILE = Path(__file__).resolve().parent / "data.json"
LOCK = Lock()

def _read_local():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

def _write_local(items):
    DATA_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

def _dynamodb_table():
    table_name = os.getenv("DYNAMODB_TABLE")
    if not table_name:
        return None

    import boto3

    dynamodb = boto3.resource(
        "dynamodb",
        region_name=os.getenv("AWS_REGION", "ap-south-1")
    )
    return dynamodb.Table(table_name)

def list_items():
    table = _dynamodb_table()
    if table:
        return table.scan().get("Items", [])
    with LOCK:
        return _read_local()

def create_item(data):
    item = {
        "id": str(uuid4()),
        "name": data.get("name", "").strip(),
        "type": data.get("type", "Found"),
        "category": data.get("category", "Other"),
        "location": data.get("location", "").strip(),
        "date": data.get("date") or datetime.now().date().isoformat(),
        "rfid": data.get("rfid", "").strip(),
        "description": data.get("description", "").strip(),
        "status": "Found" if data.get("type") == "Found" else "Lost",
        "box_checked_in": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    table = _dynamodb_table()
    if table:
        table.put_item(Item=item)
    else:
        with LOCK:
            items = _read_local()
            items.insert(0, item)
            _write_local(items)
    return item

def update_item(item_id, changes):
    table = _dynamodb_table()
    if table:
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")
        if not item:
            return None
        item.update(changes)
        table.put_item(Item=item)
        return item
    with LOCK:
        items = _read_local()
        for item in items:
            if item["id"] == item_id:
                item.update(changes)
                _write_local(items)
                return item
    return None

def find_by_rfid(tag):
    return next((item for item in list_items() if item.get("rfid") == tag), None)
