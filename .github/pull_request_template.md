## What does this PR do?
<!-- Describe the purpose of this PR. Provide context and describe the architecture/logic changes. -->
Completes the P0 Phase 3 Security and Multi-Tenant Stabilization fixes.
- Introduces `SUPERADMIN` role and prevents privilege escalation on `/register`.
- Scopes all `AdminServices` (Users, Bookings, Analytics) queries by `tenant_id` to prevent cross-tenant data leaks.
- Rewrites dashboard analytics to query real Postgres data instead of mock variables.
- Fixes Redis connection leak in `core/security.py` by sharing the core pool.
- Adds missing idempotent processing logic for Razorpay webhooks (`process_webhook`).
- Pins `requirements.txt` to strictly locked versions to prevent Azure App Service build failures.

## Type of change
- [x] Security Fix (non-breaking change which fixes an issue)
- [x] New feature (non-breaking change which adds functionality)
- [x] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] This change requires a documentation update

## How should this be tested?
- [x] Run `alembic stamp 005` followed by `alembic upgrade head`
- [x] Run `python scripts/promote_superadmin.py <your-email>` to grant platform ownership.
- [x] Run `pytest` to execute the edge-case test suite (`test_auth_roles`, `test_tenant_scoping`, `test_webhook_idempotency`).

## Checklist:
- [x] My code follows the strict DDD architecture and rules in `API_REFERENCE.md`
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation (`README.md`)
- [x] My changes generate no new warnings (MyPy passes)
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New and existing unit tests pass locally with my changes
