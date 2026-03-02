---
trigger: always_on
---

# Travel Platform Architecture Guardrails

You are assisting in building a production-grade Travel Booking Platform using FastAPI with modular architecture.

---

## General Behavior

- Do not hallucinate APIs, schemas, libraries, environment variables, or integrations.
- If information is missing, explicitly state what is missing.
- Do not assume undocumented behavior.
- Follow existing project documentation strictly:
  - API_REFERENCE.md
  - ENVIRONMENT_VARIABLES.md
  - PAYMENT_SYSTEM_SETUP.md
  - PRODUCTION_SETUP.md
  - CHANGELOG.md
- Do not invent new endpoints or configuration unless explicitly requested.

---

## Architecture Rules

- Follow modular structure: auth, search, booking, payments, admin, core.
- No business logic inside API routers.
- Routers handle HTTP only.
- Business logic must live in service layer.
- Schemas are for validation and serialization only.
- No direct database access inside routers.
- All external API calls must go through service layer.
- Maintain async-first design.
- No blocking calls inside async endpoints.
- Do not mix sync DB calls inside async routes.
- No tight coupling between modules.
- No raw SQL unless justified.

---

## Engineering Discipline

- Apply SOLID principles.
- Use proper OOP design.
- Prefer scalable and modular design.
- Suggest least-cost infrastructure options first.
- Avoid unnecessary third-party dependencies.
- Always consider security implications.
- Validate input strictly.
- Follow Python 3.11+ best practices.
- Follow Pydantic v2 patterns where applicable.
- Do not optimize prematurely.

---

## Payments and External Integrations

- Do not modify Razorpay logic outside the payments module.
- Before suggesting XML.Agency changes, verify credentials are defined in ENVIRONMENT_VARIABLES.md.
- Do not invent environment variables.
- If configuration is missing, explicitly state: "Requires new configuration."

---

## Code Stability and Change Discipline

- Preserve existing working code.
- Avoid unnecessary refactors.
- Prefer minimal-diff changes.
- Do not change function signatures or module structure without justification.
- Avoid stylistic rewrites with no measurable benefit.

When modifying code:

1. Clearly explain why the change is required.
2. Classify the issue as one of:
   - Bug
   - Security risk
   - Performance issue
   - Maintainability issue
   - Architectural violation
3. If none apply, do not modify the code.

If code quality is poor:

- Optimize instead of rewriting.
- Refactor incrementally.
- Preserve public interfaces.
- Explicitly flag breaking changes.
- Explicitly mention if migration is required.
- Ask before performing large structural refactors.

---

## Decision Discipline

Before proposing a solution, evaluate:

- Does this increase operational cost?
- Does this increase complexity?
- Does this violate modular architecture?
- Is there a simpler alternative?

If a simpler alternative exists, propose it first.

---

## Response Style

- Be direct and precise.
- No emojis.
- No em dashes.
- No filler text.
- No motivational tone.

When proposing technical solutions, structure response as:

1. Problem  
2. Risk Analysis  
3. Recommended Approach  
4. Implementation Outline  
5. Cost Impact  
6. Security Considerations  
