"""Tests run the development configuration, whatever DEMO_MODE the local .env sets."""
import os

os.environ["DEMO_MODE"] = "0"
