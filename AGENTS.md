# AGENTS.md

# BarBot Autonomous Engineering Ruleset

This document defines the mandatory behavioral, architectural, and coding constraints for all autonomous AI-assisted development within the BarBot repository.

These rules override convenience behaviors and must be followed strictly.

---

# 1. Project Identity

Project Name:
BarBot

System Type:
Distributed cocktail orchestration platform

Core Architecture:

* Raspberry Pi orchestration host
* ESP32 firmware execution layer
* Dynamic recipe ingestion pipeline
* Multi-station execution routing
* Inventory-aware recipe validation
* Touchscreen UI control system

---

# 2. Global Engineering Objectives

The system must:

* support complex cocktail workflows,
* dynamically scale inventory,
* avoid hardcoded recipe logic,
* preserve specialty ingredients,
* support modular hardware expansion,
* remain deterministic and testable.

The system must NOT:

* devolve into a simple valve dispenser,
* rely on blocking execution patterns,
* permit schema drift,
* or sacrifice safety for convenience.

---

# 3. Mandatory Development Workflow

ALL development follows:

1. Analyze
2. Plan
3. Test
4. Implement
5. Verify
6. Refactor
7. Document

Never skip steps.

---

# 4. Test-Driven Development (TDD)

TDD is mandatory.

AI agents must:

1. write failing tests first,
2. verify tests fail,
3. implement logic,
4. verify tests pass,
5. refactor safely.

Never write implementation code before tests.

---

# 5. Python Standards

Required:

* Python 3.11+
* strict type hinting
* Pydantic v2 only
* modern field_validator syntax
* dataclass-style clarity
* deterministic functions

Forbidden:

* legacy validator syntax
* untyped functions
* wildcard imports
* global mutable state
* implicit side effects

---

# 6. Firmware Standards

ESP32 firmware must:

* use non-blocking millis() timing loops,
* remain responsive during execution,
* isolate hardware modules,
* enforce safety boundaries.

Forbidden:

* delay()
* blocking loops
* uncontrolled motor runtime
* unsafe retries
* infinite waits

---

# 7. Recipe Architecture Rules

Recipes are data.

Recipes must NEVER:

* contain executable logic,
* hardcode hardware assumptions,
* bypass routing layers.

Recipes must always:

* use structured schema models,
* map into station instructions,
* remain inventory-aware,
* preserve specialty ingredients.

---

# 8. Inventory Rules

Inventory growth is autonomous.

AI agents may:

* append new ingredients automatically,
* normalize aliases,
* create missing inventory entries.

AI agents must NOT:

* silently delete inventory,
* merge premium liquors into generic categories,
* overwrite human-reviewed entries.

---

# 9. Ingredient Normalization Rules

Required:

* remove parenthetical qualifiers,
* normalize spacing and capitalization,
* preserve premium ingredient identity.

Examples:

* "Gin (London Dry)" → "Gin"
* "Crème de Cacao" remains distinct
* "Kahlúa" remains distinct

Forbidden:

* destructive generalization
* collapsing specialty liquors

---

# 10. Canadian Metric Standard

Global measurement baseline:

1 shot = 30mL

All recipe conversions must normalize into metric units.

Internal orchestration calculations use:

* mL
* grams
* unit counts
* milliseconds

---

# 11. Recipe Variance Gate

When scraped recipes differ from IBA baselines:

≤20% variance:

* may auto-approve

> 20% variance:

* must be routed into:
  artifacts/unresolved_recipes/

Never silently approve high-variance recipes.

---

# 12. Multi-Station Routing Contract

Every recipe step must map to exactly one station:

* fluid_dispenser
* ice_dispenser
* shaker_module
* user_prompt

No step may bypass the routing engine.

---

# 13. Communication Protocol Rules

Host ↔ firmware communication must:

* use structured packets,
* include acknowledgements,
* include retry handling,
* include timeout handling,
* support emergency stop states.

Preferred protocol:
newline-delimited JSON packets.

---

# 14. State Machine Requirements

Drink execution must use explicit state transitions.

Required states:

* IDLE
* VALIDATING_RECIPE
* CHECKING_INVENTORY
* ALLOCATING_STATIONS
* EXECUTING
* WAITING_FOR_USER
* COMPLETED
* FAILED
* CANCELLED
* EMERGENCY_STOP

Implicit execution flow is forbidden.

---

# 15. Logging & Telemetry

Structured logging is required.

System must emit:

* execution events,
* station events,
* inventory events,
* protocol failures,
* safety events.

Preferred library:
structlog

---

# 16. Schema Versioning

All persistent data structures must contain:

schema_version

Breaking changes require:

* migration scripts,
* backward compatibility review,
* regression tests.

---

# 17. Testing Requirements

Required test categories:

* unit tests
* integration tests
* protocol tests
* regression tests
* hardware mock tests

Firmware changes require mock validation before deployment.

---

# 18. File Modification Rules

AI agents must:

* modify the minimum required files,
* avoid unrelated formatting changes,
* preserve architectural consistency,
* explain major changes before implementation.

AI agents must NOT:

* rewrite entire files unnecessarily,
* silently refactor unrelated systems,
* introduce hidden dependencies.

---

# 19. Forbidden Behaviors

AI agents must NEVER:

* bypass tests,
* ignore failed assertions,
* invent fake hardware behavior,
* fabricate successful execution,
* remove safety checks,
* mutate schemas silently,
* hardcode inventory assumptions,
* delete unresolved recipe artifacts.

---

# 20. Preferred Libraries

Python:

* pydantic
* pytest
* mypy
* ruff
* black
* structlog
* pyserial
* requests
* beautifulsoup4
* lxml

Firmware:

* PlatformIO
* ArduinoJson

---

# 21. Initial Project Priority

The first major milestone is:

150 verified normalized cocktail recipes.

Before:

* UI development,
* firmware orchestration,
* physical hardware integration.

The data model defines the architecture.

---

# 22. AI Operational Mode

When beginning work, AI agents must:

1. Read:

   * README.md
   * AGENTS.md
   * schemas
   * existing models

2. Analyze repository state

3. Generate:

   * implementation plan,
   * test plan,
   * dependency analysis,
   * risk analysis

4. Await approval before major architectural changes.

---

# 23. Repository Philosophy

BarBot is an orchestration platform, not a hardcoded appliance.

Architecture quality, safety, determinism, and extensibility are prioritized over speed of implementation.
