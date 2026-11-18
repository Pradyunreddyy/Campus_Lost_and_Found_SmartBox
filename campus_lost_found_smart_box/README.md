# Campus Lost & Found Smart Box

A responsive campus lost-and-found dashboard based on Product No. 50 in the supplied Cloud Computing product list.

## Features
- Register lost and found belongings with category, location, date, description and optional RFID tag.
- Search and filter the item directory.
- Mark an item as claimed.
- Simulate RFID check-in/check-out and update the Smart Box OLED display on the dashboard.
- Local JSON storage works immediately; optional DynamoDB storage is supported through environment variables.
- Includes a CloudFormation template for the DynamoDB table.

## Project structure
```text
campus_lost_found_smart_box/
├── infrastructure/       # AWS infrastructure templates
├── frontend/             # HTML, CSS and browser JavaScript
├── backend/              # Flask application and storage layer
├── api/                  # REST API routes and OpenAPI description
├── requirements.txt
├── .env.example
└── .gitignore
```

## Run locally (Windows)
1. Install Python 3.10 or newer.
2. Extract the ZIP and open the extracted folder in VS Code.
3. Open Terminal in that folder.
4. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\\.venv\\Scripts\\activate
   ```
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Start the website:
   ```powershell
   python backend/app.py
   ```
7. Open `http://127.0.0.1:5000` in your browser.

The first run uses `backend/data.json` for local persistence. You do not need AWS credentials for the local demo.

## Connect DynamoDB (optional)
1. Deploy `infrastructure/dynamodb-table.yaml` using AWS CloudFormation.
2. Configure AWS credentials using an IAM role or your normal AWS CLI profile. Do not put access keys in source code.
3. Copy `.env.example` to `.env`, then set:
   ```env
   AWS_REGION=ap-south-1
   DYNAMODB_TABLE=CampusLostFoundItems
   ```
4. Install/load environment variables in your shell before starting the app (or use `python-dotenv` with a small `load_dotenv()` addition in `backend/app.py`).
5. Give the app's IAM identity permission for `dynamodb:Scan`, `dynamodb:GetItem`, and `dynamodb:PutItem` on the table.

## ESP32 / AWS IoT Core integration
This ZIP includes a working browser-based RFID simulation. It does **not** connect to a physical RFID reader yet. For the real device:
- Connect the RFID reader and OLED to the ESP32.
- Have ESP32 publish a tag ID and action to an AWS IoT Core MQTT topic.
- Add an authenticated IoT Rule/Lambda or a secured device endpoint to call the item update logic.
- Send the result back to the ESP32 so the OLED can show check-in/check-out status.

Do not expose AWS IoT certificates, private keys, database credentials or IAM access keys in frontend JavaScript or a public repository.

## Important
This is a student project starter, not a production-ready campus identity or access-control system. Before real deployment, add authentication and role-based permissions, input validation, audit logs, backups, HTTPS and privacy controls.
