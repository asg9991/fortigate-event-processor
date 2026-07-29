#!/usr/bin/env python3

import logging
import subprocess


class Notifier:

    def __init__(self, server, host, key):

        self.server = server
        self.host = host
        self.key = key

    def send(self, value):

        cmd = [
            "zabbix_sender",
            "-z", self.server,
            "-s", self.host,
            "-k", self.key,
            "-o", value
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if result.returncode != 0:

            logging.error(
                f"zabbix_sender failed rc={result.returncode}"
            )
