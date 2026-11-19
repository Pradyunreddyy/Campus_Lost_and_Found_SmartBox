
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _resolve_path(env_name):
    value = os.getenv(env_name)

    if not value:
        raise ValueError(f"Missing environment variable: {env_name}")

    path = Path(value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.is_file():
        raise FileNotFoundError(
            f"File not found for {env_name}: {path}"
        )

    return str(path)


def publish_event(event):
    endpoint = os.getenv("IOT_ENDPOINT")
    thing_name = os.getenv("IOT_THING_NAME")
    topic = os.getenv("IOT_TOPIC")

    if not endpoint or not thing_name or not topic:
        raise ValueError(
            "Missing IoT endpoint, thing name, or topic in .env"
        )

    cert_path = _resolve_path("IOT_CERT_PATH")
    key_path = _resolve_path("IOT_PRIVATE_KEY_PATH")
    ca_path = _resolve_path("IOT_ROOT_CA_PATH")

    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(
        event_loop_group, host_resolver
    )

    connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert_path,
        pri_key_filepath=key_path,
        ca_filepath=ca_path,
        client_id=thing_name,
        clean_session=True,
        keep_alive_secs=30,
        client_bootstrap=client_bootstrap,
    )

    try:
        print("Connecting to AWS IoT Core...")
        connection.connect().result(timeout=15)
        print("Connected successfully!")

        payload = json.dumps(event)

        publish_future, packet_id = connection.publish(
            topic=topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE,
        )

        publish_future.result(timeout=10)

        print(f"Published event to: {topic}")
        print(f"Packet ID: {packet_id}")
        print(f"Payload: {payload}")

    finally:
        try:
            connection.disconnect().result(timeout=10)
            print("Disconnected from AWS IoT Core.")
        except Exception:
            pass
