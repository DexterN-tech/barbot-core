# barbot-core
# BarBot

BarBot is a distributed cocktail orchestration platform designed to automate and coordinate complex drink preparation workflows across multiple hardware and user-interaction stations.

Unlike traditional automated dispensers that only handle liquids, BarBot treats cocktails as structured execution pipelines capable of coordinating:

* liquid dispensing,
* ice handling,
* mechanical shaking,
* garnish prompts,
* and user-assisted preparation steps.

---

# Core Objectives

BarBot is designed to:

* support real-world cocktail preparation workflows,
* dynamically ingest and normalize recipes,
* scale inventory automatically,
* preserve specialty liquor identity,
* route drink instructions across multiple stations,
* and maintain deterministic execution behavior.

---

# System Architecture

## Raspberry Pi Host

The Raspberry Pi serves as the orchestration layer.

Responsibilities:

* recipe validation
* inventory management
* touchscreen UI
* execution state management
* hardware routing
* telemetry logging
* serial communication

---

## ESP32 Firmware Layer

ESP32 microcontrollers act as hardware execution clients.

Responsibilities:

* station execution
* motor control
* timing loops
* pump management
* acknowledgement handling
* hardware safety enforcement

Firmware must remain non-blocking and responsive.

---

## Recipe Ingestion Engine

The ingestion pipeline:

* scrapes cocktail recipes,
* normalizes ingredient naming,
* standardizes units,
* compares against IBA baselines,
* generates structured recipe data,
* and isolates high-variance recipes.

---

# Repository Structure

```text
barbot-core/
├── .kilocode/
├── data/
├── src/
├── tests/
├── artifacts/
├── docs/
├── AGENTS.md
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

# Multi-Station Routing System

Every recipe step must route into exactly one station:

| Station         | Purpose                     |
| --------------- | --------------------------- |
| fluid_dispenser | Automated liquid dispensing |
| ice_dispenser   | Ice handling                |
| shaker_module   | Mechanical mixing           |
| stir_module     | Mechanical stirring         |
| user_prompt     | Manual user instructions    |
---

# Canadian Metric Standard

Global conversion baseline:

1 shot = 30mL

All internal calculations normalize into:

* metric units,
* milliseconds,
* and structured execution payloads.

---

# Recipe Integrity Rules

The system preserves specialty liquor identity.

Examples:

* Crème de Cacao remains distinct
* Kahlúa remains distinct
* premium ingredients are never generalized

Normalization removes parenthetical qualifiers only.

Example:

* "Gin (London Dry)" → "Gin"

---

# Recipe Variance Rules

Recipes are compared against IBA baselines.

Rules:

* ≤20% variance → may auto-approve
* > 20% variance → routed into unresolved review artifacts

Review path:
artifacts/unresolved_recipes/

---

# Development Standards

Required:

* Python 3.11+
* Pydantic v2
* strict typing
* TDD workflow
* structured logging
* deterministic execution

Firmware requirements:

* non-blocking loops
* millis() scheduling
* hardware safety enforcement

---

# Initial Development Priority

The first major milestone is:

150 verified normalized cocktail recipes.

Before:

* UI development
* hardware orchestration
* physical deployment

The recipe corpus defines the orchestration architecture.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/barbot-core.git
cd barbot-core
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Recommended Tooling

## Python

* pydantic
* pytest
* mypy
* ruff
* black
* structlog

## Firmware

* PlatformIO
* ArduinoJson

---

# Testing Philosophy

All features follow strict TDD:

1. failing tests
2. implementation
3. verification
4. refactor

Required test categories:

* unit
* integration
* protocol
* regression
* hardware mocks

---

# Long-Term Expansion Targets

Future roadmap may include:

* flow sensors
* weight sensors
* computer vision
* mobile ordering
* queue management
* recipe recommendation systems
* telemetry dashboards

---

# License

Add your selected license here.
