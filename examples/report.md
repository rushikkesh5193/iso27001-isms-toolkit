# ISMS Readiness Report: ExampleOrg Pvt Ltd (fictional)

As of **2026-10-24**. Based on ISO/IEC 27001:2022 Annex A (93 controls). Data is synthetic unless you supplied your own.

## Summary

- Readiness score: **91.2%** (82 implemented, 2 partial of 91 in-scope controls)
- Excluded as not applicable: 2. Not yet assessed: 5
- Open issues: 0 critical, 7 high, 9 medium, 3 low
- Risks on register: 10. Control gaps to close: 4

### Readiness by theme

| Theme | Controls | In scope | Implemented | Partial | Not assessed | Score |
|---|---|---|---|---|---|---|
| Organizational | 37 | 37 | 33 | 1 | 2 | 90.5% |
| People | 8 | 8 | 8 | 0 | 0 | 100.0% |
| Physical | 14 | 14 | 12 | 0 | 2 | 85.7% |
| Technological | 34 | 32 | 29 | 1 | 1 | 92.2% |

## Issues needing action

### High (7)

| Area | Ref | Check | Detail | Action |
|---|---|---|---|---|
| audit | F-01 | FINDING_OVERDUE | Open major nc F-01 is past its due date. Critical patches not applied within policy timelines. Due 2026-09-30 (24 days late), owner IT Manager. | Agree a dated corrective action and verify closure. |
| controls | 8.30 | EXCLUDED_NO_JUSTIFICATION | Control 8.30 excluded without justification. Outsourced development is marked not applicable with no reason recorded. | Record why the control is not applicable; auditors will ask. |
| programme | Cl. 9.2 | INTERNAL_AUDIT_OVERDUE | No internal audit in the last 12 months. Last internal audit: 2025-09-15. | Plan and complete an internal audit covering the ISMS scope. |
| risks | R02 | RISK_RELIES_ON_GAP | Risk R02 lowered by control 8.12 which is planned. Insider copies customer data to personal cloud: residual 8 < inherent 12, but 8.12 (Data leakage prevention) is not fully implemented. | Either finish the control or restore the risk score until it is in place. |
| risks | R03 | RISK_UNTREATED | High risk R03 has no treatment decision. Phishing leads to credential theft (residual 12). | Choose to mitigate, transfer, avoid or formally accept, with an owner and date. |
| risks | R07 | RISK_ACCEPT_NO_APPROVAL | Risk R07 accepted without recorded approval. Primary data centre outage | Obtain and record sign-off from the risk owner / management. |
| risks | R09 | CRITICAL_RISK_ACCEPTED | Critical risk R09 is being accepted. Legacy unsupported OS still in production (residual 20). | Confirm top management has explicitly agreed. |

### Medium (9)

| Area | Ref | Check | Detail | Action |
|---|---|---|---|---|
| audit | F-02 | FINDING_OVERDUE | Open minor nc F-02 is past its due date. Access control policy not reviewed after reorganisation. Due 2026-10-01 (23 days late), owner CISO. | Agree a dated corrective action and verify closure. |
| controls | 5.9 | NO_EVIDENCE | Control 5.9 is implemented but has no evidence reference. Inventory of information and other associated assets | Link the policy, record or screenshot that proves it. |
| controls | 6.1 | EVIDENCE_STALE | Control 6.1 not reviewed in over 12 months. Screening: last reviewed 2025-06-01. | Re-review the control and refresh the evidence. |
| controls | SoA | NOT_ASSESSED | 5 Annex A controls have not been assessed. Statement of Applicability is incomplete: 5.6, 5.32, 7.12, 7.13, 8.34. | Decide applicability and status for each control, with a justification for any exclusion. |
| risks | R01 | RISK_RELIES_ON_GAP | Risk R01 lowered by control 8.16 which is partial. Ransomware encrypts file servers: residual 10 < inherent 20, but 8.16 (Monitoring activities) is not fully implemented. | Either finish the control or restore the risk score until it is in place. |
| risks | R02 | TREATMENT_OVERDUE | Treatment for risk R02 is overdue. Insider copies customer data to personal cloud: due 2026-09-15 (39 days late), owner CISO. | Re-baseline the date with the owner or escalate. |
| risks | R07 | RISK_ACCEPT_REVIEW_OVERDUE | Accepted risk R07 is past its review date. Review was due 2026-08-01. | Re-confirm the acceptance or choose a treatment. |
| risks | R07 | RISK_RELIES_ON_GAP | Risk R07 lowered by control 5.30 which is partial. Primary data centre outage: residual 5 < inherent 10, but 5.30 (ICT readiness for business continuity) is not fully implemented. | Either finish the control or restore the risk score until it is in place. |
| risks | R08 | RISK_UNKNOWN_CONTROL | Risk R08 cites unknown control 9.9. Weak guest Wi-Fi segregation | Correct the control reference. |

### Low (3)

| Area | Ref | Check | Detail | Action |
|---|---|---|---|---|
| audit | F-03 | FINDING_OVERDUE | Open observation F-03 is past its due date. Awareness attendance records incomplete. Due 2026-10-10 (14 days late), owner HR Head. | Agree a dated corrective action and verify closure. |
| audit | F-06 | FINDING_UNKNOWN_CONTROL | Finding F-06 cites unknown control 9.9. Consider automating evidence collection | Correct the reference. |
| controls | SoA | NO_OWNER | 1 in-scope controls have no owner. 7.4. | Assign an accountable owner to each control. |

## Control gaps (in scope, not fully implemented)

| Control | Title | Status | Owner |
|---|---|---|---|
| 5.7 | Threat intelligence | not implemented | Compliance Lead |
| 8.12 | Data leakage prevention | planned | IT Manager |
| 5.30 | ICT readiness for business continuity | partial | Compliance Lead |
| 8.16 | Monitoring activities | partial | IT Manager |

## Risk register (highest residual first)

| ID | Risk | Inherent | Residual | Rating | Treatment | Owner |
|---|---|---|---|---|---|---|
| R09 | Legacy unsupported OS still in production | 20 | 20 | critical | accept | - |
| R03 | Phishing leads to credential theft | 16 | 12 | high | none | - |
| R01 | Ransomware encrypts file servers | 20 | 10 | medium | mitigate | IT Manager |
| R04 | KYC vendor suffers a breach | 15 | 10 | medium | mitigate | Compliance Lead |
| R02 | Insider copies customer data to personal cloud | 12 | 8 | medium | mitigate | CISO |
| R05 | Unpatched internet-facing server exploited | 12 | 8 | medium | mitigate | IT Manager |
| R06 | Loss of a key team member | 6 | 6 | medium | accept | - |
| R07 | Primary data centre outage | 10 | 5 | low | accept | - |
| R08 | Weak guest Wi-Fi segregation | 4 | 4 | low | mitigate | IT Manager |
| R10 | Loss of backup media in transit | 6 | 3 | low | mitigate | IT Manager |

### Residual risk heat map (count of risks)

| Impact \ Likelihood | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | 1 | 2 | · | · | · |
| **4** | · | 2 | 1 | · | 1 |
| **3** | 1 | 1 | · | · | · |
| **2** | · | 1 | · | · | · |
| **1** | · | · | · | · | · |

Scores are likelihood x impact (1-25). Ratings: low <6, medium 6-11, high 12-19, critical 20+ (editable in config.json).
