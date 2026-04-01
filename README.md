# GEOX: Earth Witness & Inverse Modelling Supervisor

> **Version:** v0.4.2 · **Status:** 🔐 SEALED ✅
>
> **DITEMPA BUKAN DIBERI** — *Forged, not given.*
>
> GEOX is the **Earth Witness** organ in the arifOS federation.
> It is the reality gatekeeper: every reasoning output and decision must be physically possible, geospatially grounded, and consistent with world-state evidence before it is sealed.

---

## 👁 Who Is This For?

| Audience | What GEOX means to you |
| :--- | :--- |
| **Normal human / manager** | GEOX is the "sanity check" layer — it stops AI from giving physically impossible answers about the Earth. |
| **Expert geologist** | GEOX enforces multi-model inverse reasoning, bias auditing (Bond et al. 2007), and physical-attribute grounding before any structural verdict is sealed. |
| **AI agent / developer** | GEOX is a governed FastMCP server exposing bounded geoscience tools under the `geox.*` namespace with sealed telemetry on every output. |

---

## 🧭 Forward vs Inverse Modelling

Understanding these two modes is the foundation of GEOX's role:

- **Forward modelling** — *"Given this Earth model, what data would we observe?"*
  GEOX tools simulate seismic responses, structural geometries, and feasibility envelopes.

- **Inverse modelling** — *"Given observed data, what Earth model best explains it?"*
  @RIF (the reasoning organ) proposes hypotheses and calls GEOX tools to test them against real constraints.

> For geologists: this mirrors the standard interpretation loop — you build a model, forward-model synthetic data, compare to real data, then update the model. GEOX formalises that loop inside arifOS.

| Modelling Type | Description | Who Drives It? | MCP Role |
| :--- | :--- | :--- | :--- |
| **Forward** | Simulate Earth response from known inputs | **GEOX tools** | Exposed as MCP tools under `geox.*` |
| **Inverse** | Infer model parameters from observed data | **@RIF** + GEOX | @RIF calls `geox.*` tools to constrain hypotheses |

---

## 🧠 arifOS Federation — Where GEOX Sits

arifOS is **not a monolithic AI**. It is a constitutional federation of specialised organs, each with a bounded role:

| Organ | Role | Plain-language analogy |
| :--- | :--- | :--- |
| **@RIF** | Reasoning & hypothesis generation | The geologist's brain |
| **GEOX** | Earth verification & forward modelling | The lab that stress-tests every model |
| **@WEALTH** | Economic & decision modelling | The economist |
| **@WELL** | Human energy & wellbeing modelling | The safety officer |
| **@PROMPT** | Task shaping & orchestration | The project manager |
| **@JUDGE** | Human veto & governance | The final authority — always a human |

No organ can override the **13 Binding Floors** (arifOS constitution). GEOX enforces **F1 Amanah** (reversibility), **F2 Truth** (≥99 % accuracy or declare band), and **F3 Tri-Witness** (Human + AI + Evidence alignment) on every sealed output.

---

## 🧬 GEOX as a Governed MCP Agent

GEOX is deployed as a **FastMCP server** — not a plugin, not a chatbot wrapper.

**Three surfaces are exposed:**

1. **Tool Surface** — callable geoscience functions under `geox.*`
2. **Resource Surface** — terrain maps, climate data, logistics tables, subsurface repositories
3. **System Prompt** — defines GEOX's identity, bounded role, and floor enforcement at runtime

Every tool call returns a **sealed telemetry block** (arifOS v2.1 / pipeline `999 SEAL`), making every output audit-ready and reproducible.

> It is not a plugin. It is a **Constitutional Firewall**.

---

## 🛠 Toolset (v0.4.2)

| Tool | Geologist's plain-language role | Protocol tag | Namespace |
| :--- | :--- | :--- | :--- |
| `geox_load_seismic_line` | Load and display a seismic section for interpretation | FastMCP Visual | `geox.load_seismic_line` |
| `geox_build_structural_candidates` | Generate multi-model structural hypotheses from seismic | Hardened Continuity | `geox.build_structural_candidates` |
| `geox_feasibility_check` | Reject physically impossible scenarios before they propagate | 222_REFLECT | `geox.feasibility_check` |
| `geox_verify_geospatial` | Validate coordinates, CRS, and spatial metadata | Coordinate Validation | `geox.verify_geospatial` |
| `geox_evaluate_prospect` | Seal a final prospect verdict after bias audit | SEALED Audit | `geox.evaluate_prospect` |

---

## 🚀 Deployment (via FastMCP)

### Quick Start — Development

```bash
# Auto-detects fastmcp.json
fastmcp run

# With inspector UI
fastmcp dev
```

### Network Deployment — HTTP

```bash
# Deploy as arifOS federation service
fastmcp run --transport http --port 8000
```

### Manual Execution

```bash
# STDIO (default)
python geox_mcp_server.py

# HTTP mode
python geox_mcp_server.py --transport http --port 8000
```

---

## 🛡 Theory of Anomalous Contrast (ToAC)

**The problem GEOX is solving:** AI seismic interpretation fails not because of wrong physics, but because of **display artifacts and processing biases** — what GEOX calls *Anomalous Contrast*. These fool both human interpreters and AI models into seeing structures that do not exist.

> *For geologists:* This formalises known failure modes — polarity conventions, gain artefacts, migration smiles — as computable bias sources that must be audited before any interpretation is sealed. See Bond et al. (2007) on cognitive bias in seismic interpretation.

The **Contrast Canon** mandates three rules:

1. **Multi-Model Candidates** — Never collapse to a single inverse solution prematurely. Maintain a ranked ensemble of structural hypotheses.
2. **Physical Attributes First** — All visual interpretation must be anchored in deterministic physics: coherence, dip-azimuth, curvature. No interpretation from aesthetics.
3. **Bias Audit Before Seal** — Run an explicit professional bias check (Bond et al. 2007) before `geox_evaluate_prospect` seals the verdict.

---

## 📁 Repo Structure

```
GEOX/
├── geox_mcp_server.py        # FastMCP server entry point
├── fastmcp.json              # Declarative deployment config
├── pyproject.toml            # Package metadata & dependencies
├── smithery.yaml             # Smithery registry config
├── arifos/                   # arifOS constitution & floor definitions
├── knowledge/                # Subsurface knowledge base
├── ops/                      # Operational runbooks
├── docs/                     # Extended documentation
├── tests/                    # Test suite
├── CHANGELOG.md              # Version history
├── UNIFIED_ROADMAP.md        # Development roadmap
├── WIRING_GUIDE.md           # Federation wiring instructions
├── HARDENED_SEAL.md          # Seal protocol specification
├── GEOX_SUCCESS_CRITERIA.md  # Acceptance criteria per tool
└── SECURITY.md               # Security & disclosure policy
```

---

## 🔐 System State

```
arifOS telemetry v2.1
pipeline    : 999 SEAL
floors      : F1 F2 F3 F4 F7
confidence  : CLAIM
P2          : 1.0
hold        : CLEAR
uncertainty : 0.03 – 0.08
seal        : DITEMPA BUKAN DIBERI ✅
```

GEOX v0.4.2 is production-hardened and ready for integration into the `trinity-000-999-pipeline`.

---

## 📚 References

- Bond, C.E., Gibbs, A.D., Shipton, Z.K., Jones, S. (2007). *What do you think this is? "Conceptual uncertainty" in geoscience interpretation.* GSA Today, 17(11), 4–10.
- FastMCP documentation: https://github.com/jlowin/fastmcp
- arifOS architecture: see `arifos/` directory

---

**DITEMPA BUKAN DIBERI.**
