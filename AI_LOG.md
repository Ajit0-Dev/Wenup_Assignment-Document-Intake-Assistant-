# AI_LOG.md — Document Intake Assistant

This log records the meaningful AI-assisted design and engineering decisions made during development of this project. Entries are organized by phase and topic. Low-level code generation details are omitted — only decisions that shaped the architecture are recorded.

---

## Entry 1 — Architecture & State Design

**Tool:** Antigravity IDE (AI pair programmer)  
**Phase:** Phase 1 (Design)  
**Goal:** Establish how structured state should be maintained across turns.

**Key prompt:**
> "The assignment says conversation history must NOT be the source of truth. How do we maintain structured state while still using an LLM?"

**AI suggestion:**
> Use a `canonical IntakeState` Pydantic model as the single source of truth. The LLM produces `ProposedUpdate` objects (field, value, confidence, is_correction). The application validates and applies these separately. Conversation history is sent to the LLM as context only — not as the record of truth.

**What I questioned:**
> Whether this adds unnecessary complexity over just parsing conversation history at document-generation time.

**Final decision:** Use canonical `IntakeState`.

**Reason:** The assignment explicitly requires structured state. Parsing history at generation time is fragile and inconsistent with the correction scenario — if a user corrects a field mid-conversation, history-based generation could produce incorrect output depending on how the LLM reads conflicting turns.

---

## Entry 2 — LLM Contract Design

**Tool:** Antigravity IDE  
**Phase:** Phase 3 (LLM Integration)  
**Goal:** Define the structured response format the LLM must return.

**Key prompt:**
> "What should the LLM response schema look like to enable field extraction and corrections safely?"

**AI suggestion:**
> Define `LLMResponse` with three fields: `proposed_updates` (list of `ProposedUpdate`), `clarification_needed` (optional string), and `assistant_message` (string). Each `ProposedUpdate` includes `field` (dot-path like `executor.name`), `value`, `confidence`, and `is_correction`.

**What I questioned:**
> Whether `is_correction` should be inferred by the application (if a confirmed field is being overwritten) rather than stated by the LLM.

**Final decision:** Keep `is_correction` in the LLM contract, but also apply application-level logic. If the LLM marks something as a correction, it's passed through. If a confirmed field is proposed without `is_correction=True`, it is rejected (preventing silent overwrites).

**Reason:** Defense in depth — both the LLM intent and the application rule must agree for a confirmed field to be changed.

---

## Entry 3 — Validation Strategy (Atomic Updates)

**Tool:** Antigravity IDE  
**Phase:** Phase 3 (LLM Integration)  
**Goal:** Prevent partial state corruption when LLM response is partially valid.

**Key prompt:**
> "If the LLM proposes 3 updates and 1 is invalid, what happens?"

**AI suggestion:**
> Validate each update independently. Apply valid ones. Reject invalid ones with a rejection reason. Do not roll back valid updates because one failed.

**What I questioned:**
> Whether to reject the entire batch if any update is invalid (strict atomicity) vs. apply partial updates.

**Final decision:** Per-field validation with independent application. Invalid updates are collected as rejection messages and logged, while valid ones are applied.

**Reason:** The assignment requires the assistant to be resilient. If the LLM extracts name=valid, address=invalid, rejecting the valid name extraction creates a worse UX than applying it and asking about the address again.

---

## Entry 4 — Mock LLM Provider Design

**Tool:** Antigravity IDE  
**Phase:** Phase 2–3 (Testing)  
**Goal:** Allow full test coverage without needing a live LLM API.

**Key prompt:**
> "How should the mock LLM work for testing — full fixture JSONs or deterministic rule-based logic?"

**AI suggestion:**
> Use a deterministic rule-based `MockLLMService` that reads the last user message and matches trigger phrases (e.g. "rahul sharma" → set `full_name`). This avoids maintaining large fixture files while keeping tests readable and fast.

**What I changed:**
> Initially the mock only matched a few cases. Expanded trigger coverage to include correction patterns, ambiguity triggers ("everything" + "family"), worldwide assets, executor fields, and children names to support all test scenarios.

**Final decision:** Deterministic rule-based mock with clear trigger phrases documented in the source.

**Reason:** Tests are then predictable, fast, and free. The mock is explicitly labeled for testing — it is not intended to handle natural language.

---

## Entry 5 — Gemini Provider Integration

**Tool:** Antigravity IDE  
**Phase:** Phase 3 (LLM Integration)  
**Goal:** Replace mock with a real Gemini provider.

**Key prompt:**
> "Use Gemini API key and three free models."

**AI suggestion:**
> Use `google-genai` SDK with `response_mime_type=application/json` and a structured `response_schema` to force JSON output from the model. Support `gemini-2.0-flash-lite`, `gemini-1.5-flash`, and `gemini-1.5-flash-8b` as configured options.

**What I changed:**
> The model `gemini-2.0-flash-lite` was deprecated during development. Updated default to `gemini-3.5-flash-lite`.

**Final decision:** Gemini as the default provider, configurable via `GEMINI_MODEL` in `.env`.

**Reason:** Free tier availability. The response schema enforcement reduces malformed output significantly compared to prompt-only JSON requests.

---

## Entry 6 — Document Generation Strategy

**Tool:** Antigravity IDE  
**Phase:** Phase 5 (Testing & Reliability)  
**Goal:** Decide how to generate the Personal Wishes Document.

**Key prompt:**
> "Should document generation be done client-side or server-side?"

**AI suggestion:**
> Server-side. Add a `GET /api/document/{session_id}` endpoint that reads the current `IntakeState` and generates HTML from it. The frontend renders this HTML.

**What I questioned:**
> Client-side generation from the `state` object received in chat responses would avoid a second API call.

**Final decision:** Server-side generation via dedicated endpoint.

**Reason:** Consistent with the architecture principle that the backend owns state logic. The document format logic belongs in the backend where it can be independently tested. Frontend only renders what the backend confirms.

---

## Entry 7 — UI Layout and Information Architecture

**Tool:** Antigravity IDE  
**Phase:** Phase 4 (Frontend)  
**Goal:** Design the three-column split that makes the application self-explanatory.

**Key prompt:**
> "UI should make three things immediately understandable: what the assistant is asking, what info is collected, and what the document looks like."

**AI suggestion:**
> Two-panel layout: Chat Panel (left, 50%) and Context Panel (right, 50%) with Information and Document tabs. Information tab shows a live field-by-field view with color-coded status badges. Document tab shows the generated HTML preview with a prominent disclaimer.

**What I changed:**
> Added a progress bar to the Information tab to give a clear sense of completion without requiring users to count fields.

**Final decision:** Two-panel split with tabbed context panel.

**Reason:** Clean separation of concerns. The chat panel handles interaction; the context panel handles transparency. A reviewer can see at a glance that structured state is being maintained.

---

## Entry 8 — Testing Scope and Coverage

**Tool:** Antigravity IDE  
**Phase:** Phase 5 (Testing & Reliability)  
**Goal:** Define what constitutes a complete and meaningful test suite.

**Key prompt:**
> "Tests should not depend on a live LLM."

**AI suggestion:**
> All tests use `monkeypatch` to force `LLM_PROVIDER=mock`. Test classes cover: single field extraction, multiple fields, corrections, ambiguous input, validation rejections, state preservation, LLM failure handling, session API, document API, and a full end-to-end journey.

**Final decision:** 39 backend tests, all using `MockLLMService` via monkeypatch. No live API calls in CI.

**Reason:** Fast, deterministic, free. Real Gemini calls are validated separately by running the application manually.

---

## What I Would Improve for Production

This section is a personal note on what I'd want to fix or add if this were going to a real production environment rather than being a demo submission.

**1. Sessions stored in memory — not suitable for production**
Right now, all sessions are stored in a Python dictionary in memory. That means if the server restarts, all sessions are lost. In a real app, I'd store session state in something like PostgreSQL or Redis so sessions can survive restarts and scale across multiple server instances.

**2. No real user authentication**
Anyone who knows a session ID can access that session. For a real product dealing with personal legal wishes, I'd add proper user accounts, login, and make sure sessions are tied to a specific authenticated user.

**3. LLM is called on every single message**
Currently every message goes to Gemini even if the user says something like "yes" or "okay". I'd add a lightweight check to see if a message is likely to contain useful field information before making an API call. This would reduce cost and latency significantly.

**4. The Gemini model name is hardcoded in .env**
We've already had the problem twice during development where the model name became deprecated overnight (gemini-2.0-flash-lite, gemini-2.5-flash-lite). In production, I'd add automatic fallback logic — if the configured model returns a 404, try the next available model.

**5. No rate limiting or request validation on the API**
The backend currently accepts any input without rate limiting. In production, I'd add rate limiting per session, input length validation, and basic abuse prevention.

**6. Document generation could be richer**
The current HTML document is functional but basic. For a real product, I'd want it to generate a properly formatted PDF with legal-style formatting, not just raw HTML rendered in an iframe.

**7. Better handling of partial/incomplete conversations**
Right now if a user just closes the tab mid-conversation, there's no way to resume. I'd add session recovery so a returning user can pick up where they left off, since filling in personal wishes information can be emotional and interrupted easily.

Overall the architecture is solid — the canonical state approach, the validation layer, and the LLM abstraction are all production-ready patterns. The gaps are mostly infrastructure (storage, auth, rate limiting) rather than core design.

