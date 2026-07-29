#!/usr/bin/env python3

import json
import os
import time


class ThresholdManager:

    def __init__(self, filename):

        self.filename = filename

        if os.path.exists(filename):
            try:
                with open(filename) as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {}
        else:
            self.state = {}

    def save(self):

        with open(self.filename, "w") as f:
            json.dump(self.state, f, indent=2)

    def cleanup(self):

        now = time.time()

        expired = []

        for logid, data in self.state.items():

            if now - data["first_seen"] >= data["window"]:
                expired.append(logid)

        for logid in expired:
            del self.state[logid]

        if expired:
            self.save()

    def increment(self, logid, count_limit, window):

        now = time.time()

        if logid not in self.state:

            self.state[logid] = {
                "count": 1,
                "first_seen": now,
                "window": window,
                "alerted": False
            }

            self.save()

            return False

        entry = self.state[logid]

        if now - entry["first_seen"] >= window:

            entry["count"] = 1
            entry["first_seen"] = now
            entry["window"] = window
            entry["alerted"] = False

            self.save()

            return False

        entry["count"] += 1

        if entry["count"] >= count_limit and not entry["alerted"]:

            entry["alerted"] = True
            self.save()

            return True

        self.save()

        return False
