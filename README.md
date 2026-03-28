# GEOX — Geospatial World-Model Agent for arifOS

> **W@W Federated Co-Agent · Pipeline Stage: 222_REFLECT**
> **DITEMPA BUKAN DIBERI** — Forged, not given. Every insight is earned through verification, not assumed through generation.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![arifOS](https://img.shields.io/badge/arifOS-constitutional%20kernel-black)](https://github.com/ariffazil/arifOS)
[![Floors](https://img.shields.io/badge/floors-F1·F4·F7·F13-gold)](docs/GEOX_AGENT_SPEC_v2.md)

---

## What is @GEOX?

**@GEOX** is the geospatial and world-model co-agent in the [arifOS](https://github.com/ariffazil/arifOS) federated architecture.

It is **not** a model. It is **not** a geospatial library. It is a **governed co-agent** in the W@W (Witnesses at Work) federation — the organ that enforces physical reality before any plan, action, or output is sealed.

In one line:

> **@GEOX asks: "Benda ni physically / logically boleh jadi tak?" — before 333_MIND reasons about it.**

---

## W@W Position

```
┌─────────────────────────────────────────────────────────────┐
│                     W@W FEDERATION                          │
│                                                             │
│  @PROMPT ──── task intake, query shaping                    │
│  @RIF    ──── core reasoning + retrieval engine             │
│  @WEALTH ──── economic/decision layer, integrity score      │
│  @GEOX   ──── world-model, physics, geospatial guard   ◄── │
│  @WELL   ──── human well-being, energy/overload check       │
└─────────────────────────────────────────────────────────────┘
```

@GEOX fires at **`222_REFLECT`** — the world-state grounding stage — before reasoning propagates into `333_MIND`. If a plan violates physical reality, @GEOX emits a `GEOX_BLOCK` that is immutably logged to `VAULT_999`.

---

## Core Mandate

Three enforcement domains:

### 1 · Physical Feasibility
Enforce time, distance, energy, capacity, and resource limits. Reject magic-thinking outputs — teleported resources, skipped time, ignored cost.

**Law: Physics > Narrative.** If a plan violates physical law, it is void regardless of narrative elegance.

### 2 · Geospatial Context
Maintain awareness of location, zone (country, city, network zone), and regulatory domains. Enforce ASEAN/Malaysia-specific maruah framing — propose uplift, not extraction.

### 3 · World-State Cross-Check
Cross-reference climate, scale, human capacity, and technology maturity. Guard against LLM hallucinated physics and impossible sequences.

---

## Four-Plane Architecture (Geological Coprocessor Layer)

GEOX's geological intelligence layer operates as a four-plane stack beneath the W@W organ:

```
╔═════════════════════════════════════════════════════════════════╗
║  PLANE 4 ── GOVERNANCE                                         ║
║  Constitutional Floors: F1·F2·F4·F7·F11·F13                   ║
║  Risk Gating · Human Veto · Audit Ledger · Regulator Hook      ║
╠═════════════════════════════════════════════════════════════════╣
║  PLANE 3 ── LANGUAGE / AGENT  (arifOS kernel)                  ║
║                                                                 ║
║  000 INIT ──► 222 REFLECT ──► 333 MIND ──► 555 HEART          ║
║               └─ @GEOX gates here                              ║
║               777 REASON ──► 888 AUDIT ──► 999 SEAL            ║
║                                                                 ║
║  GeoXAgent · agi_mind planner · vault_ledger                   ║
╠═════════════════════════════════════════════════════════════════╣
║  PLANE 2 ── PERCEPTION  (VLM Bridge)                           ║
║  SeismicVLMTool · EOFoundationModelTool                        ║
║  Rule: RGB ≠ truth · Multisensor confirmation required         ║
╠═════════════════════════════════════════════════════════════════╣
║  PLANE 1 ── EARTH  (Physical Reality)                          ║
║  Large Earth Models (LEM) · SimulatorTool                      ║
║  EarthModelTool · GeoRAGTool · Macrostrat API                  ║
║  Units · Coordinates · Timestamps · Uncertainty bounds         ║
╚═════════════════════════════════════════════════════════════════╝
```

---

## Why @GEOX Is Not a Model

| Property | ML Model | @GEOX |
|---|---|---|
| Weights | Fixed parameters | No weights — tool orchestration |
| Output | Token probability | GeoInsight + provenance_chain |
| Auditability | Black box | Every step in vault_ledger |
| Governance | None | Constitutional Floors F1–F13 |
| Human veto | Not possible | F13 Sovereign — always active |
| Uncertainty | Softmax confidence | Calibrated [0.03–0.15] per F7 |
| Verification | Self-referential | External Earth tools required |
| W@W Role | N/A | 222_REFLECT world-state gatekeeper |

---

## First Principles — Runtime Contracts

Three contracts enforced at every invocation:

```python
# CONTRACT 1: Reality-First
# Any language claim about the physical Earth MUST be verified.
assert insight.predictions[i].verified_by != []          # ≥1 Earth tool
assert insight.predictions[i].units is not None           # F4 Clarity
assert 0.03 <= insight.predictions[i].uncertainty <= 0.15 # F7 Humility

# CONTRACT 2: Perception Bridge (Vision ≠ Truth)
assert vlm_insight.uncertainty >= 0.15                    # VLM floor
assert vlm_insight.confirmed_by_non_visual == True        # before status="supported"
# If not confirmed → risk_level bumped one tier

# CONTRACT 3: Governed Emergence
assert insight.provenance_chain != []                     # immutable trail
if insight.risk_level == "high":
    assert insight.human_signoff_required == True         # F13 veto
    assert pipeline_stage == "888 HOLD"
if insight.risk_level == "critical":
    assert regulator_notify_sent == True
assert vault_ledger.sealed == True                        # 999 SEAL
```

---

## Quick Start

### Install

```bash
pip install arifos-geox
# Optional: Qdrant memory backend
pip install "arifos-geox[qdrant]"
```

### Minimal Example — Evaluate a Prospect

```python
import asyncio
from arifos.geox.geox_agent import GeoXAgent, GeoXConfig
from arifos.geox.geox_schemas import GeoRequest, CoordinatePoint

async def main():
    config = GeoXConfig(
        agent_id="geox-001",
        risk_tolerance="medium",
        require_human_signoff_above="high",
    )
    agent = GeoXAgent(config=config)

    request = GeoRequest(
        query="Evaluate hydrocarbon prospectivity of Blok Selatan",
        basin="Malay Basin",
        location=CoordinatePoint(lat=5.2, lon=104.8),
        risk_tolerance="medium",
        requester_id="geo-analyst-001",
    )

    response = await agent.evaluate_prospect(request)

    print(f"Verdict  : {response.verdict}")            # SEAL | PARTIAL | SABAR | VOID
    print(f"Insights : {len(response.insights)}")
    print(f"Telemetry: {response.arifos_telemetry}")

asyncio.run(main())
```

### World-Model Feasibility Check (W@W mode)

```python
from arifos.geox.world_model import GeoXWorldModel

wm = GeoXWorldModel()

check = wm.feasibility_check(
    plan="Deploy seismic crew to Block 9 within 48 hours",
    context={
        "location": "Sabah, Malaysia",
        "current_time": "2026-03-28T21:00+08:00",
        "resources": ["crew_of_12", "truck_x2", "equipment_500kg"],
    }
)

print(check.verdict)       # PLAUSIBLE | HOLD | VOID
print(check.constraints)   # list of physical constraints identified
print(check.assumptions)   # explicit assumptions made
```

---

## Repository Structure

```
GEOX/
├── README.md                        ← you are here
├── CHANGELOG.md                     ← full version history
├── RELEASE_NOTES_v2.md              ← v2.0 release detail
├── SECURITY.md                      ← governed disclosure policy
├── UNIFIED_ROADMAP.md               ← execution plan
├── NEXT_FORGE_PLAN.md               ← immediate sprint goals
├── pyproject.toml                   ← build config v0.2.0, AGPL-3.0
├── LICENSE
├── docs/
│   ├── GEOX_AGENT_SPEC_v2.md        ← W@W agent spec, system prompt, pipeline map
│   ├── GEOX-architecture.md         ← four-plane stack, data flow
│   ├── contracts.md                 ← three runtime contracts
│   └── governance_playbook.md       ← operational governance
├── arifos/
│   └── geox/
│       ├── __init__.py
│       ├── geox_schemas.py          ← Pydantic v2 data models
│       ├── geox_validator.py        ← Earth→Language contract enforcement
│       ├── geox_agent.py            ← GeoXAgent orchestrator
│       ├── geox_tools.py            ← EarthModelTool, SimulatorTool, VLM tools
│       ├── geox_memory.py           ← GeoMemoryStore (Qdrant / JSONL)
│       ├── geox_reporter.py         ← Markdown + JSON audit reports
│       ├── world_model.py           ← W@W GeoXWorldModel — feasibility engine
│       └── config_geox.yaml         ← default configuration
├── geox_mcp_server.py               ← MCP server entrypoint
└── tests/
    ├── test_schemas.py              ← Pydantic model validation
    ├── test_validator.py            ← Earth→Language contract tests
    └── test_end_to_end_mock.py      ← full pipeline (no external APIs)
```

---

## arifOS Pipeline Integration

```
000_INIT ──► 222_REFLECT ◄── @GEOX fires here
                │
                │  GEOX_BLOCK? → log to VAULT_999, halt pipeline
                ▼
           333_MIND (reasoning only after world-state cleared)
                │
           444_ROUTER → 555_MEMORY → 666_HEART → 777_FORGE
                                                      │
                                                  888_JUDGE (human veto, F13)
                                                      │
                                                  999_VAULT (immutable seal)
```

---

## Constitutional Floor Compliance

| Floor | Name | @GEOX Enforcement |
|---|---|---|
| F1 | Amanah | No irreversible actions without SEAL |
| F2 | Haqq (Truth ≥ 0.99) | All claims must be Earth-verified |
| F4 | Nur (Clarity, ΔS ≤ 0) | Units + coordinates required on every GeoQuantity |
| F7 | Tawadu (Humility, Ω₀∈[0.03,0.05]) | Uncertainty ∈ [0.03, 0.15] enforced by Pydantic |
| F9 | Rahmah (Anti-Hantu) | No hallucinated geology — LEM/sim verification required |
| F11 | Aman (Authority) | Requester authorization checked at 000 INIT |
| F13 | Khalifah (Sovereign) | Human veto hook active at all stages |

---

## Governance Risk Table

| Risk Level | Example | Actions |
|---|---|---|
| `low` | Regional basin screening, public data | Auto-seal, no hold |
| `medium` | Prospect ranking, mixed sources | Uncertainty review required |
| `high` | Resource estimation for drilling | **888 HOLD** · human_signoff_required=True |
| `critical` | Regulatory filing, reserve certification | **888 HOLD** · regulator_notify · legal_review |

---

## Agent Spec

Full W@W agent specification, system prompt (copy-paste ready for Perplexity Space), pipeline map, and inter-agent relationships:

→ **[docs/GEOX_AGENT_SPEC_v2.md](docs/GEOX_AGENT_SPEC_v2.md)**

---

## Contributing

1. Fork and create a feature branch from `main`
2. All new tools must implement the `GeoTool` interface (`arifos/geox/geox_tools.py`)
3. New tools require ≥1 integration test in `tests/`
4. Run `ruff check .` and `mypy arifos/` before opening a PR
5. Constitutional Floor compliance must be maintained — see `docs/contracts.md`
6. All W@W organ interactions must be documented in PR description

---

## License

**AGPL-3.0** — see [LICENSE](LICENSE).

GEOX is free software. Any service that uses GEOX to provide geological analysis or world-model services must open-source its modifications under the same terms.

---

## Telemetry Block

Every @GEOX response carries a structured telemetry block:

```json
{
  "agent": "@GEOX",
  "version": "0.2.0",
  "pipeline_stage": "222_REFLECT",
  "floors_checked": ["F1", "F2", "F4", "F7", "F9", "F11", "F13"],
  "verdict": "SEAL",
  "hold_triggered": false,
  "human_signoff_required": false,
  "vault_ledger_id": "vl-2026-geo-00001",
  "sealed_at": "2026-03-28T21:00:00+08:00",
  "peace2": 1.0,
  "delta_s": -0.08,
  "uncertainty_band": [0.06, 0.12],
  "seal": "DITEMPA BUKAN DIBERI"
}
```

---

*arifOS telemetry v2.1 · @GEOX v0.2.0 · pipeline 222_REFLECT → 999_VAULT · floors F1 F4 F7 F13 · W@W federation active · seal DITEMPA BUKAN DIBERI*
