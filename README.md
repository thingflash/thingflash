# ThingFlash

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License: Apache-2.0"></a>
  <a href="https://github.com/Alisherka7/thingflash"><img src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg" alt="Open Source"></a>
  <a href="https://aws.amazon.com/cdk/"><img src="https://img.shields.io/badge/AWS-CDK%20v2-FF9900?logo=amazonaws&logoColor=white" alt="AWS CDK v2"></a>
  <a href="https://aws.amazon.com/iot-core/"><img src="https://img.shields.io/badge/AWS-IoT%20Core-232F3E?logo=amazonaws&logoColor=white" alt="AWS IoT Core"></a>
</p>

**Production-ready AWS IoT infrastructure in three commands.**

Building an IoT backend on AWS means wiring together 15+ services — IoT Core, X.509 certificates, IoT policies, Device Shadows, Rules, Lambda, S3, DynamoDB, CloudWatch — and getting the security right on every one of them.

ThingFlash compresses that into a declarative workflow:

```bash
pipx install thingflash

thingflash init
thingflash plan
thingflash apply
```

From an empty AWS account to a secure MQTT-connected device with telemetry flowing into a database — **in under 15 minutes**.

---

## What is ThingFlash?

ThingFlash is an open-source, opinionated CLI for provisioning and operating AWS IoT infrastructure. You describe your device fleet in a single version-controlled YAML manifest — ThingFlash safely creates and manages everything else.

It is **not** a Terraform replacement. It's a specialized layer for connected products that knows how IoT should be built:

- **Secure by default** — one certificate per device, least-privilege IoT policies, topic access scoped by Thing name
- **Plan before apply** — every change is previewed with security warnings; nothing touches your infrastructure silently
- **Batteries included** — device registry, certificate lifecycle, MQTT topics, telemetry pipelines, image upload, monitoring
- **Automation-first** — every command is idempotent, non-interactive, and supports `--output json` for CI/CD and AI agents

## Who is it for?

Developers and teams building connected products — from ESP32 microcontrollers to Raspberry Pi gateways, sensors, cameras, and robot fleets — who need a real cloud backend without becoming AWS IoT experts first.

```yaml
# thingflash.yaml — your entire IoT backend in one file
fleet:
  thingType: camera
  policies:
    mode: least-privilege

telemetry:
  rules:
    - name: telemetry-to-dynamodb
      source: devices/+/telemetry
      destination:
        type: dynamodb
```

## Get involved

- ⭐ Star the [main repository](https://github.com/thingflash/thingflash) to follow progress
- 💬 Open an [issue](https://github.com/thingflash/thingflash/issues) — feedback from real IoT teams shapes the roadmap
- 📖 Read the [documentation](https://github.com/thingflash/thingflash/tree/main/docs)

## License

Apache 2.0 — open source.