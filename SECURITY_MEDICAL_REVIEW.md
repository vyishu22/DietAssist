# Security & Medical Content Review Checklist

This checklist is designed to help ensure DietAssist is safe and compliant when used in healthcare settings.

## Security
- [ ] Ensure `.env` files with secrets are not committed to source control.
- [ ] Store `GEMINI_API_KEY` and other secrets in secure vaults or repository secrets (e.g., GitHub Secrets).
- [ ] Use HTTPS in production and enforce secure cookies for auth tokens.
- [ ] Apply input validation and sanitization on all endpoints.
- [ ] Monitor and limit API usage to prevent abuse and runaway costs.

## Medical Content
- [ ] Have a qualified clinician review the prompt and sample outputs for medical safety.
- [ ] Add clear disclaimers in UI that recommendations are informational and not a substitute for medical advice.
- [ ] Ensure `doctorAlert` messages are prominent and instruct users to seek medical care when necessary.
- [ ] Log and audit all AI outputs (for debugging and review) without exposing PII.
- [ ] Ensure privacy compliance (e.g., HIPAA) if storing or processing protected health information.

## Operational
- [ ] Rate limit GenAI calls and add caching for repeated requests to reduce cost and latency.
- [ ] Add monitoring and alerts for errors and unusual model behavior.
- [ ] Test model outputs regularly and add regression tests for prompt changes.
- [ ] Implement scheduled backups, retention policies, and secure offsite storage (e.g., S3/GCS) and periodically test restores.
- [ ] Ensure backups and snapshots are encrypted at rest and in transit. Also consider immutable backups for tamper resistance.

## Privacy & Compliance
- [ ] Maintain data retention policies and deletion workflows; provide users with an authenticated data deletion endpoint (`/api/patient/delete-data`).
- [ ] Ensure audit logging and access control for administrative data operations.
- [ ] Perform a privacy impact assessment and legal review for health data processing (HIPAA/GDPR or local regulations).
- [ ] Ensure transport security (HTTPS/TLS) everywhere and enforce strong TLS ciphers and HSTS in production.

