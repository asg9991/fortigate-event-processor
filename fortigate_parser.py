#!/usr/bin/env python3

import json
import logging
import re
import subprocess
import yaml

from classifier import Classifier
from notifier import Notifier
from thresholds import ThresholdManager

FIELD_RE = re.compile(r'(\w+)=(".*?"|\S+)')


def parse(line):

    fields = dict(FIELD_RE.findall(line))

    return {
        "logid": fields.get("logid", "").replace('"', ""),
        "level": fields.get("level", "").replace('"', ""),
        "type": fields.get("type", "").replace('"', ""),
        "subtype": fields.get("subtype", "").replace('"', ""),
        "action": fields.get("action", "").replace('"', ""),
        "msg": fields.get("msg", "").replace('"', ""),
        "raw": line.strip()
    }


with open("/opt/fortigate-event-processor/config/parser.yaml") as f:
    cfg = yaml.safe_load(f)

logging.basicConfig(
    filename="/opt/fortigate-event-processor/logs/parser.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logging.info("FortiGate Event Processor started")
logging.info(f"Monitoring {cfg['log_file']}")

classifier = Classifier(cfg["classification_file"])

thresholds = ThresholdManager(cfg["state_file"])

notifier = Notifier(
    cfg["zabbix"]["server"],
    cfg["zabbix"]["host"],
    cfg["zabbix"]["key"]
)

tail = subprocess.Popen(
    ["tail", "-F", cfg["log_file"]],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True
)

for line in tail.stdout:

    event = parse(line)

    if not event["logid"]:
        continue

    rule = classifier.classify(event["logid"])

    if not rule["enabled"]:
        continue

    classification = rule["classification"]

    if classification == "IGNORE":
        continue

    payload = {
        "classification": classification,
        "logid": event["logid"],
        "level": event["level"],
        "type": event["type"],
        "subtype": event["subtype"],
        "action": event["action"],
        "message": event["msg"]
    }

    thresholds.cleanup()

    if classification == "THRESHOLD":

        send = thresholds.increment(
            event["logid"],
            rule["count"],
            rule["window"]
        )

        if send:
            logging.info(
                f"THRESHOLD reached logid={event['logid']} "
                f"count={rule['count']} window={rule['window']}"
            )

            notifier.send(json.dumps(payload, ensure_ascii=False))

    else:

        logging.info(
            f"{classification} sent "
            f"logid={event['logid']} "
            f"level={event['level']}"
        )

        notifier.send(json.dumps(payload, ensure_ascii=False))
