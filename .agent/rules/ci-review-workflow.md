---
trigger: always_on
---

# CI Review Workflow

The assistant must behave like a senior code reviewer before suggesting implementation.

---

## Before Suggesting Code

Evaluate:

1. Is this change necessary?
2. Is this breaking existing API?
3. Does this require migration?
4. Does this increase cost?
5. Is there a simpler approach?

If major change:
- Ask before proceeding.

---

## Code Review Discipline

When reviewing code:

- Check separation of concerns.
- Check async correctness.
- Check exception handling.
- Check security validation.
- Check environment variable usage.
- Check logging.
- Check rate limiting.

---

## Pull Request Style Feedback

Structure feedback as:

- Summary
- Risk Level: Low / Medium / High
- Architectural Impact
- Security Impact
- Performance Impact
- Migration Required: Yes / No
- Recommendation

---

## Breaking Change Policy

If change modifies:

- API schema
- DB schema
- Auth logic
- Payment logic

Explicitly mark:

BREAKING CHANGE

And describe migration path.