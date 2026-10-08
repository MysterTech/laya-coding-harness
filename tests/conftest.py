"""Test-wide guards (spec §4.4): no test may reach the network."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
