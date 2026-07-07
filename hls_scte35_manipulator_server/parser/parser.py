import argparse

parser = argparse.ArgumentParser(
    description="Run SCTE-35 manipulator middleware between injector and origin"
)
parser.add_argument(
    "--origin-base-url",
    required=True,
    help="Origin base URL where incoming PUT requests are forwarded",
)
parser.add_argument(
    "--profile",
    default="profiles/profile.json",
    help="Path to profile.json containing filter and overwrite rules",
)
parser.add_argument("--host", default="0.0.0.0", help="HTTP bind host")
parser.add_argument("--port", type=int, default=4999, help="HTTP bind port")
parser.add_argument(
    "--request-timeout",
    type=float,
    default=10.0,
    help="Upstream origin request timeout in seconds",
)

parser.add_argument(
    "--log-level",
    default="INFO",
    choices=["DEBUG", "INFO", "WARN", "ERROR"],
    help="Log level"
)