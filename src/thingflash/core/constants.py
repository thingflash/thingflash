import re

# Doctor check statuses
OK = "ok"
WARN = "warn"
FAIL = "fail"

# Scaffold
MANIFEST_FILENAME = "thingflash.yaml"
STATE_DIRNAME = ".thingflash"
GITIGNORE_ENTRY = ".thingflash/"

DEFAULT_REGION = "us-east-1"
DEFAULT_THING_TYPE = "sensor"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_PROFILE = "default"
ENVIRONMENTS = ("development", "staging", "production")

_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}$")
_REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-\d$")

_MANIFEST_TEMPLATE = """\
# thingflash.yaml — ThingFlash project manifest
# Docs: https://github.com/thingflash/thingflash/blob/main/docs/manifest-reference.md
apiVersion: thingflash.com/v1
kind: IoTProject

metadata:
  name: {name}
  environment: {environment}  # development | staging | production

aws:
  region: {region}
  profile: {profile}

fleet:
  thingType: {thing_type}
  groups:
    - default
  policies:
    mode: least-privilege   # secure default, explicit for the user

mqtt:
  topics:
    telemetry: devices/{{thingName}}/telemetry
    status: devices/{{thingName}}/status
    commands: devices/{{thingName}}/commands
"""

# State
APPLIED_FILENAME = "applied.json"

# Session
