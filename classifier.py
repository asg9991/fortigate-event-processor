#!/usr/bin/env python3

import csv


class Classifier:

    def __init__(self, csv_file):
        self.rules = {}

        with open(csv_file, newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:

                self.rules[row["logid"]] = {
                    "classification": row["classification"].upper(),
                    "count": int(row["count"]),
                    "window": int(row["window"]),
                    "enabled": row["enabled"].lower() == "true"
                }

    def classify(self, logid):

        return self.rules.get(logid, {
            "classification": "AUDIT",
            "count": 0,
            "window": 0,
            "enabled": True
        })
