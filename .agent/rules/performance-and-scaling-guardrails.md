---
trigger: always_on
---

# Performance and Scaling Guardrails

The assistant must prevent premature optimization and uncontrolled scaling.

---

## Performance Discipline

- Do not optimize without measurable bottleneck.
- Prefer profiling before refactoring.
- Avoid micro-optimizations without benchmark.
- Use async properly.
- Avoid blocking I/O inside async endpoints.

---

## Database Performance

- Always use indexed queries for frequent filters.
- Avoid N+1 query patterns.
- Use pagination for list endpoints.
- Avoid loading unnecessary columns.
- Use connection pooling properly.

---

## Redis Usage

- Use Redis only when justified.
- Cache search results if external API calls are slow.
- Set TTL explicitly.
- Do not cache sensitive data.
- Do not over-cache dynamic data.

---

## Azure Scaling Strategy

Student Tier Phase:

- Single instance.
- Vertical scaling first.
- No auto-scaling unless necessary.

Company Production Phase:

- Add auto-scaling rules.
- Scale based on CPU or request count.
- Use staging slots.
- Enable health probes.

---

## API Performance

- Enforce max_results limit.
- Enforce pagination size limits.
- Validate input size.
- Avoid returning large payloads unnecessarily.

---

## Background Tasks

- Use Celery only when workload justifies it.
- Avoid background jobs for trivial operations.
- Ensure idempotency for payment callbacks.