---
trigger: always_on
---

# Deployment Review Discipline

This project deploys first on Azure Student Tier and later migrates to Company Azure subscription.

The assistant must enforce structured deployment planning.

---

## Environment Separation

- Never mix development and production configuration.
- Always distinguish between:
  - Local
  - Azure Student
  - Company Production
- Ensure ENVIRONMENT variable is set correctly.
- Do not suggest using test keys in production.
- Enforce strict separation of secrets.

---

## Azure Student Tier Constraints

When recommending infrastructure for Azure Student:

- Minimize cost.
- Prefer single App Service instance.
- Avoid over-provisioning.
- Use basic PostgreSQL tier.
- Use minimal Redis tier or disable if optional.
- Avoid unnecessary background workers.
- Suggest consumption-based services when possible.

Always consider credit limits.

---

## Migration to Company Deployment

When suggesting production setup:

- Recommend separate resource group.
- Recommend staging slot.
- Recommend managed identity instead of raw secrets.
- Suggest Azure Key Vault for secrets.
- Recommend proper monitoring with Azure Monitor.
- Enforce HTTPS only.
- Enforce CORS restrictions.

---

## Deployment Safety

Before proposing deployment changes, evaluate:

1. Will this increase Azure cost?
2. Does this require downtime?
3. Does this require database migration?
4. Does this require secret rotation?

Explicitly mention these impacts.

---

## Infrastructure Discipline

- Do not suggest Kubernetes unless scale requires it.
- Prefer Azure App Service over AKS for early stage.
- Prefer managed PostgreSQL over self-hosted.
- Avoid complex architecture during Student tier phase.
- Gradually increase complexity only when needed.

---

## Production Hardening Checklist

When user says "ready for production", verify:

- DEBUG=false
- ENVIRONMENT=production
- Strong JWT_SECRET_KEY
- Live Razorpay keys
- Proper CORS origins
- Database SSL enabled
- Rate limiting enabled
- Health endpoint verified
- Logging level appropriate