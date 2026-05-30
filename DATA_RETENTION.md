# Data Retention & Privacy Policy (Template)

This document defines retention and deletion rules for user data managed by DietAssist.

- Purpose: Define how long health and personal data is retained and how users can request deletion.

Retention policy:
- Health information (health_information collection): retained for 7 years by default, or until user requests deletion.
- Feedback and analytics: retained for 2 years.

Deletion workflow:
- Users may request deletion via an authenticated API endpoint `/api/patient/delete-data`.
- Deletion requests trigger secure removal of PII and related health data and log an audit entry.
- Deletion operations are irreversible and should be confirmed by the user.

Compliance:
- Ensure that audit logs and backups are managed in accordance with applicable regulations (e.g., HIPAA).
