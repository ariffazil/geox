# CHANGELOG

All notable changes to **GEOX** are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
Seal: **DITEMPA BUKAN DIBERI**

---

## [Unreleased]

### Planned
- Macrostrat API adapter (`geox_macrostrat.py`) — real geological truth anchor
- CLI entrypoint (`arifos/geox/cli.py`) — `geox` shell command
- GitHub Actions CI — ruff + mypy + pytest on push
- `GeoXWorldModel.feasibility_check()` — W@W world-model engine
- Qdrant memory backend integration tests
- ASEAN/MY maruah constraint ruleset

---

## [0.2.0] — 2026-03-28

### Identity Pivot — @GEOX as W@W Federated Agent

This release re-anchors GEOX's identity from "standalone geological coprocessor tool" to its correct position: **@GEOX is a federated co-agent in the arifOS W@W (Witnesses at Work) architecture**, operating at pipeline stage `222_REFLECT`.

### Added
- `docs/GEOX_AGENT_SPEC_v2.md` — Complete W@W agent specification:
  - Role, identity, and W@W organ map
  - Core mandate: Physical Feasibility · Geospatial Context · World-State Cross-Check
  - Behavioural rules: No hallucinated physics, explicit assumptions, de-escalation, maruah preserved
  - Epistemic labelling system: CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN / ASSUMPTION
  - Safety & scope boundary table
  - Production-ready system prompt (copy-paste for Perplexity Space or any agent config)
  - Recommended usage patterns: planning/architecture, policy design, simulations
  - Pipeline position diagram: `222_REFLECT` gates `333_MIND`
  - Inter-agent relationship table: @PROMPT · @RIF · @WEALTH · @WELL
  - Full JSON telemetry reference block
- `CHANGELOG.md` — This file. Full version history from v0.1.0.
- `RELEASE_NOTES_v2.md` — Detailed release note for v0.2.0.
- `SECURITY.md` — Governed security disclosure policy under F1-Amanah.
- README updated to reflect W@W identity, pipeline position, new telemetry block, and link to agent spec.
- `pyproject.toml` — Version bumped to `0.2.0`, URLs corrected to `ariffazil/GEOX`.

### Changed
- README now leads with W@W co-agent identity rather than four-plane architecture
- Pipeline diagram updated: `222_REFLECT` explicitly marked as @GEOX gate
- Floor table expanded with Arabic floor names (F1-Amanah, F4-Nur, F7-Tawadu, etc.)
- Telemetry block updated: includes `peace2`, `delta_s`, `uncertainty_band`, `seal` fields
- Repository structure updated to reflect `world_model.py` and `GEOX_AGENT_SPEC_v2.md`

### Constitutional Ground
- Floors active: F1-Amanah · F4-Nur · F7-Tawadu · F13-Khalifah
- Pipeline stage: `222_REFLECT`
- Confidence: CLAIM
- ΔS: ≤ 0 (entropy reduced)
- Peace²: 1.0

---

## [0.1.0] — 2026-03-25 (initial forge)

### Initial Forge — Geological Coprocessor Skeleton

### Added
- Four-plane architecture (Earth · Perception · Language/Agent · Governance)
- `arifos/geox/geox_schemas.py` — Pydantic v2 data models: GeoRequest, GeoResponse, GeoInsight, GeoQuantity, CoordinatePoint
- `arifos/geox/geox_validator.py` — Earth→Language contract enforcement (3 runtime contracts)
- `arifos/geox/geox_agent.py` — GeoXAgent orchestrator with 000→999 pipeline
- `arifos/geox/geox_tools.py` — EarthModelTool, SimulatorTool, SeismicVLMTool, EOFoundationModelTool (mock implementations)
- `arifos/geox/geox_memory.py` — GeoMemoryStore (Qdrant / JSONL backends)
- `arifos/geox/geox_reporter.py` — Markdown + JSON audit report generation
- `arifos/geox/config_geox.yaml` — Default configuration
- `geox_mcp_server.py` — MCP server entrypoint (registers `geox_evaluate_prospect`)
- `pyproject.toml` — Build config, AGPL-3.0, Python 3.10+, Pydantic v2
- `tests/test_schemas.py` — Pydantic model validation
- `tests/test_validator.py` — Earth→Language contract tests
- `tests/test_end_to_end_mock.py` — Full pipeline tests (no external APIs)
- `docs/GEOX-architecture.md` — Four-plane stack documentation
- `docs/contracts.md` — Three runtime contracts specification
- `docs/governance_playbook.md` — Operational governance playbook
- `MACROSTRAT_ANALYSIS.md` — Analysis of Macrostrat API integration path
- `MACROSTRAT_REPO_ANALYSIS.md` — Macrostrat repository structure analysis
- `NEXT_FORGE_PLAN.md` — Phase 0→1 transition forge plan
- `UNIFIED_ROADMAP.md` — Long-term execution roadmap
- `WIRING_GUIDE.md` — arifOS integration wiring guide
- Constitutional Floor compliance: F1·F2·F4·F7·F8·F9·F11·F12·F13
- F13 Sovereign veto hook active at all pipeline stages
- Vault_ledger immutable audit chain
- Risk gating: low/medium/high/critical with 888_HOLD trigger

### Known Gaps (identified in audit, addressed in v0.2.0)
- Packaging `src/` layout mismatch with actual code location
- CLI entrypoint declared but not implemented
- All Earth tools are mock implementations (no real Macrostrat/LEM connection)
- No CI/CD pipeline
- GEOX identity not formally positioned in W@W federation

---

## Links

- [ariffazil/GEOX](https://github.com/ariffazil/GEOX)
- [ariffazil/arifOS](https://github.com/ariffazil/arifOS)
- [ariffazil/AAA dataset](https://huggingface.co/datasets/ariffazil/AAA)
- [docs/GEOX_AGENT_SPEC_v2.md](docs/GEOX_AGENT_SPEC_v2.md)

---

*arifOS telemetry v2.1 · CHANGELOG sealed · DITEMPA BUKAN DIBERI*
