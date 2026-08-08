# ThingFlash

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License: Apache-2.0"></a>
  <a href="https://github.com/Alisherka7/thingflash"><img src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg" alt="Open Source"></a>
  <a href="https://aws.amazon.com/cdk/"><img src="https://img.shields.io/badge/AWS-CDK%20v2-FF9900?logo=amazonaws&logoColor=white" alt="AWS CDK v2"></a>
  <a href="https://aws.amazon.com/iot-core/"><img src="https://img.shields.io/badge/AWS-IoT%20Core-232F3E?logo=amazonaws&logoColor=white" alt="AWS IoT Core"></a>
</p>

**Connect physical devices to AWS IoT Core in minutes.**

ThingFlash is a CLI tool for provisioning AWS IoT infrastructure and
connecting physical devices to AWS IoT Core using a simple declarative workflow.

Instead of manually configuring IoT Things, certificates, policies,
IAM roles, storage, and rules across multiple AWS services, describe
what you need in `thingflash.yaml` and let ThingFlash plan and apply it.

```bash
pipx install thingflash

thingflash init
thingflash plan
thingflash apply
```

> 🚧 ThingFlash is currently in early development.

---

## Why ThingFlash?

Connecting a physical device to AWS IoT usually requires configuring
multiple AWS resources:

- IoT Things and Thing Types
- X.509 certificates
- IoT policies
- Thing Groups
- IAM roles
- IoT Rules
- S3 and DynamoDB
- IoT Jobs

ThingFlash provides one workflow for managing them.

---

## Who is it for?

ThingFlash is for developers building connected products such as:

- ESP32 and other microcontrollers
- Raspberry Pi devices
- sensors
- cameras
- gateways
- robotics and IoT fleets

The goal is to make AWS IoT infrastructure easier to create,
understand, and automate.

---

## ThingFlash Structure

<img src="./images/structure.svg" alt="ThingFlash Logo" width="1200">

---

## Get involved

- ⭐ Star the [main repository](https://github.com/thingflash/thingflash) to follow progress
- 💬 Open an [issue](https://github.com/thingflash/thingflash/issues) — feedback from real IoT teams shapes the roadmap
- 📖 Read the [documentation](https://github.com/thingflash/thingflash/tree/main/docs)

---

## Contributing

Contributions are welcome! To get started:

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# 3. Verify the CLI works
thingflash --help

# 4. Run the tests and linter
python3 -m pytest        # Run tests
python3 -m ruff check .  # Lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## License

Apache 2.0 — open source.
