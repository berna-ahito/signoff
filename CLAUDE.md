# Signoff — Claude Code Instructions

You are working on Signoff, a portfolio-grade full-stack AI workflow system.

## Product
Signoff is an AI-ready procurement intake, approval, RFQ drafting, and audit system.

It turns messy purchase requests into structured, validated, auditable procurement data.

## Stack
- Backend: FastAPI
- Frontend: React + Vite
- Database: SQLite local-first
- AI: provider-agnostic MockProvider first
- Later AI adapters: Gemini/Groq/Ollama only if free-safe
- Deployment later: free-first only

## Windows command rules
- Use `py`, not `python`.
- Use `py -m pip`, `py -m pytest`, `py -m uvicorn`.
- Do not assume Linux-only commands.

## Build rules
- Do not build everything in one go.
- Use GSD phase workflow.
- Plan first, then execute small milestones.
- No paid APIs.
- No random dependencies.
- No one-file app.
- No autonomous spending approval.
- Deterministic approval rules first.
- AI may classify, summarize, detect missing info, recommend risk, and draft RFQ text only.
- Humans approve or reject spending.
- Every sensitive status change must create an audit log.

## Security rules
- Protect against IDOR/BOLA.
- Avoid mass assignment.
- Use separate create/update/admin schemas.
- Validate server-side.
- Add rate limiting before deployment.
- Add status transition checks.
- Add tests for approval rules and validation.
- Never commit secrets.
- Create `.env.example`, never `.env`.

## Useful skills/agents
Use relevant installed skills automatically:
- api-design
- backend-patterns
- frontend-patterns
- coding-standards
- security-review
- tdd-workflow
- verification-loop
- documentation-lookup

Do not use Obsidian, claude-mem, GraphRAG, ADK, browser automation, or agent platforms unless explicitly requested later.

<!-- KARPATHY_AGENT_PRINCIPLES_START -->

## Karpathy-Inspired Agent Principles

Use these principles for non-trivial coding, refactoring, debugging, architecture, agent-workflow, and product-building tasks. For obvious one-line fixes, use judgment and stay lightweight.

### 1. Think Before Coding

- State assumptions before implementation.
- Do not silently choose between multiple interpretations when the choice changes architecture, data model, security, file scope, or user-visible behavior.
- Surface tradeoffs when there are multiple reasonable paths.
- Push back when a simpler approach is clearly better.
- Stop and ask when confusion could cause wrong code.

### 2. Simplicity First

- Prefer the minimum code that solves the stated problem.
- Do not add speculative features, generic abstractions, or unnecessary configurability.
- Do not create new layers for single-use logic.
- Do not add error handling for impossible scenarios.
- If the solution is bloated, simplify before finalizing.

### 3. Surgical Changes

- Touch only files required by the task.
- Do not rewrite adjacent code, comments, formatting, or architecture unless asked.
- Match the existing project style.
- Mention unrelated dead code or unrelated issues, but do not remove them unless requested.
- Every changed line should trace back to the user request.

### 4. Goal-Driven Execution

- Convert vague implementation requests into verifiable success criteria.
- Prefer tests, builds, lint checks, or explicit manual verification before declaring work done.
- For multi-step work, use: step → verification.
- Keep looping until the stated verification passes or a real blocker is found.
- Report what was verified, what failed, and what was not run.

<!-- KARPATHY_AGENT_PRINCIPLES_END -->
