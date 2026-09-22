# 🤖 AGENTS.md — ModelNorth HyperBrowser Engine

Welcome, Agent. This document defines the engineering discipline, architectural constraints, and operational protocols for contributing to **ModelNorth HyperBrowser**.

---

## 🎯 North Star Metric & Purpose

ModelNorth HyperBrowser is an open-source (Apache 2.0) **Tri-Tier Sovereign Web Agent** designed to deliver:
1. **Sub-20ms reflex latency** for standard web interactions via local System 1 decision models and in-browser V8 compilation.
2. **$0.00 base execution cost** without reliance on proprietary cloud decision endpoints.
3. **Flawless visual grounding fallback** via Gemini 2.5 Flash / multimodal sentries for Canvas, WebGL, and CAPTCHAs.

---

## 🛡️ Karpathy Engineering Guidelines

Every change in this codebase MUST follow these four core principles:

### 1. Think Before Coding
- **Surface assumptions explicitly**: Never guess DOM attributes, race conditions, or network timeouts silently.
- **Push back on unnecessary complexity**: If an in-browser CSS/JS evaluator solves the problem in 2 lines, do not spin up an LLM prompt.
- **Fail loud and clear**: Ambiguous states must trigger the Tier 2 Vision circuit breaker or report explicit blockage.

### 2. Simplicity First (Anti-Bloat)
- **Zero speculative abstractions**: Do not build generic multi-layered plugin systems for code that runs in one place.
- **Minimal dependencies**: Prefer standard library, `onnxruntime`, and direct Chrome DevTools Protocol (`cdp`) websocket communication.
- **50-line rule**: If an action parser takes 200 lines and could be 50, refactor it down.

### 3. Surgical Edits
- Touch only the target module required for your task.
- Clean up any dead imports or variables created by your changes.
- Never reformat or "clean up" adjacent code in unrelated modules.

### 4. Goal-Driven & Verifiable Execution
Every change must be validated against a measurable success criterion:
```
1. Feature / Bugfix → verify: [Automated test in tests/ or offline script]
2. Latency optimization → verify: [Step time measured in milliseconds (ms)]
3. Fallback routing → verify: [Synthetic test asserting Tier 0 -> Tier 1 -> Tier 2 path]
```

---

## 🏗️ Architecture & Component Boundaries

```
modelnorth-hyperbrowser/
├── modelnorth/
│   ├── agent.py               # Master Tri-Tier loop: Tier 0 -> Tier 1 -> Tier 2
│   ├── core/
│   │   ├── snapshot.js        # In-V8 atomic DOM element indexer & coordinate reader
│   │   ├── fastpath.js        # Sub-1ms deterministic regex/intent matcher
│   │   └── browser.py         # CDP harness, viewport geometry & pixel-click executor
│   ├── engine/
│   │   ├── decision_local.py  # Local HyperLocal ONNX runtime (7-15ms System 1 classifier)
│   │   ├── text_engine.py     # Local Ollama (qwen2.5-coder) or API text helper
│   │   └── vision_sentry.py   # Gemini 2.5 Flash / multimodal coordinate resolver
│   └── ui/
│       └── flight_deck.py     # High-speed live inspector & latency visualizer
```

---

## 🧪 Testing & Verification Protocol

Before declaring any task or PR complete, run the following verification suite:

```bash
# 1. Lint & Format Verification
uv run ruff check .

# 2. Offline Unit & Heuristic Tests
uv run pytest tests/ -v

# 3. Syntax Verification on V8 Injected Scripts
node --check modelnorth/core/snapshot.js
node --check modelnorth/core/fastpath.js
```

---

## 📜 Licensing & Provenance

This project is released under the **Apache License, Version 2.0**. All newly created files must preserve clean-room provenance and attribution to `ModelNorth Sovereign AI`.
