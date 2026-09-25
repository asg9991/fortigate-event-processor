#!/usr/bin/env python3

import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
import yaml

from classifier import Classifier
from notifier import Notifier
from thresholds import ThresholdManager

BASE_DIR = "/opt/fortigate-event-processor"

FIELD_RE = re.compile(r'(\w+)=(".*?"|\S+)')

# Run cleanup every N lines processed
CLEANUP_INTERVAL = 500

# Seconds to wait before restarting tail after failure
TAIL_RESTART_DELAY = 5

logger = logging.getLogger("fortigate")


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


def start_tail(log_file):
    """Start tail -F on the given log file. Returns the Popen object."""
    return subprocess.Popen(
        ["tail", "-F", log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )


def load_config():
    config_path = os.path.join(BASE_DIR, "config/parser.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def setup_logging(log_directory):
    log_path = os.path.join(log_directory, "parser.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )


def main():
    cfg = load_config()
    setup_logging(cfg["log_directory"])

    shutdown_requested = False

    def handle_shutdown(signum, frame):
        nonlocal shutdown_requested
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, shutting down...")
        shutdown_requested = True

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logger.info("FortiGate Event Processor started")
    logger.info(f"Monitoring {cfg['log_file']}")

    classifier = Classifier(cfg["classification_file"])
    thresholds = ThresholdManager(cfg["state_file"])

    notifier = Notifier(
        cfg["zabbix"]["server"],
        cfg["zabbix"]["host"],
        cfg["zabbix"]["key"]
    )

    tail = start_tail(cfg["log_file"])
    lines_since_cleanup = 0

    logger.info(f"Tail process started (pid={tail.pid})")

    try:
        while not shutdown_requested:

            # Check if tail is still alive
            ret = tail.poll()
            if ret is not None:
                logger.warning(
                    f"Tail process died (rc={ret}), "
                    f"restarting in {TAIL_RESTART_DELAY}s..."
                )
                time.sleep(TAIL_RESTART_DELAY)
                if shutdown_requested:
                    break
                tail = start_tail(cfg["log_file"])
                logger.info(f"Tail restarted (pid={tail.pid})")
                continue

            # Non-blocking read with timeout
            line = tail.stdout.readline()

            if line == "":
                # EOF — tail exited or no data yet
                time.sleep(0.1)
                continue

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

            if classification == "THRESHOLD":

                send = thresholds.increment(
                    event["logid"],
                    rule["count"],
                    rule["window"]
                )

                if send:
                    logger.info(
                        f"THRESHOLD reached logid={event['logid']} "
                        f"count={rule['count']} window={rule['window']}"
                    )

                    notifier.send(json.dumps(payload, ensure_ascii=False))

            else:

                logger.info(
                    f"{classification} sent "
                    f"logid={event['logid']} "
                    f"level={event['level']}"
                )

                notifier.send(json.dumps(payload, ensure_ascii=False))

            # Periodic cleanup
            lines_since_cleanup += 1
            if lines_since_cleanup >= CLEANUP_INTERVAL:
                thresholds.cleanup()
                lines_since_cleanup = 0

    finally:
        logger.info("Shutting down...")
        if tail.poll() is None:
            tail.terminate()
            try:
                tail.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tail.kill()
        logger.info("FortiGate Event Processor stopped")


if __name__ == "__main__":
    main()
