# Signoff Specification

Signoff is an AI-ready procurement intake, approval, RFQ drafting, and audit system.

Core flow:
1. Employee submits purchase request.
2. Backend validates request.
3. AI review suggests category, urgency, missing info, risk level, summary, and RFQ draft.
4. Deterministic approval rules decide next status.
5. Human approves, rejects, or requests more info.
6. Audit log records sensitive status changes.

AI never approves spending.
