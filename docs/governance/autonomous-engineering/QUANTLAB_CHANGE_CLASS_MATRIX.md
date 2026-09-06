# QUANTLAB CHANGE CLASS MATRIX v1.0

## Purpose

Authority is determined by change class, not merely by whether something is "code".

| Class | Name | Typical examples | Autonomous? |
|---|---|---|---|
| Q0 | Observation | audits, inventories, metrics, read-only reconciliation | YES |
| Q1 | Test / Evidence | tests, probes, acceptance evidence, non-mutating tooling | YES |
| Q2 | Safe Phase Engineering | deterministic implementation required by approved acceptance; bounded refactor; bug fix; schema-neutral code | YES within approved phase |
| Q3 | Controlled Structural Change | new migration, new persistent model, new worker/service, major engine boundary change | Only if current phase + Owner authorization explicitly permit |
| Q4 | Product / Authority Change | new feature outside acceptance, UX mission change, Constitution change, new external authority | NO |
| Q5 | Production / Capital Authority | production deployment, broker credential activation, Live enablement, real-money order path, risk-threshold authority | NO unless Owner explicitly authorizes that exact action |

## Default rule

Unclear classification => choose the higher-risk class.

## Structural-change checks

Before Q3:
- demonstrate need
- show no adequate existing asset
- define rollback
- define migration/recovery
- define tests
- define blast radius
- obtain required authorization

## Permanent restrictions

These cannot be downgraded by an implementation agent:
- Constitution changes
- Live activation
- real-money execution
- broker credentials
- next-phase admission
- weakening safety gates
- deleting historical evidence to simplify architecture
