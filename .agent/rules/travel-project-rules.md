---
trigger: always_on
---

# Travel Project Rules - XML.AGENCY Flight API Integration

## Project Context
- Building a white-label travel site per "Website-Proposall.pdf": B2B/B2C portals, admin panels, modules (flights/hotels/buses via Trurism/XML APIs).
- Primary API: XML.AGENCY Flight API v3.17 ("XML-Agency-Flight-API.pdf") - SOAP 1.2, endpoints like AeroSearch/AeroPrebook/AeroBook.
- Tech: Python (Zeep for SOAP), async where possible; bridge to PHP/MySQL if needed. Use .env for test creds (ApiLogin: test, ApiPassword: test).

## Coding Standards
- Always validate XML requests/responses against PDF schemas (e.g., SearchFlights with IATA, dates; handle OfferCode/SearchGuid).
- Generate structured code: src/api_client.py for wrappers, agents/flight_agent.py for tasks (search/book flights).
- Error handling: Catch API errors (ErrorCode != -1), log with SearchGuid; retry transients.
- Tests: Unit for API calls (mock Zeep), integration for full flows (search → prebook → book).

## Agent Behaviors
- Before coding: Plan steps referencing PDF examples (e.g., multi-city searches).
- Security: Never hardcode creds; use .env. Confirm destructive ops (e.g., real bookings).
- Output: Create artifacts (plans.md, diagrams), update README.md with changes.
- Optimizations: Prefer EUR/USD currency; filter low-cost/charter flights; handle baggage/tariffs.

## Prohibitions
- No real bookings without explicit confirmation.
- Avoid PHP unless migrating proposal backend; prioritize Python agents.
- Do not assume unlisted API features; stick to PDF (e.g., no unmentioned hotels).
