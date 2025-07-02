# Example Tune Change: Addressing Lean AFR Condition

This document shows how the "tuning-ai" agent summarizes a detected lean condition and the corresponding fuel map adjustment. Use this as a reference for the tune changes page so that end users can quickly understand the rationale behind each change.

## Issue Summary

| Item | Details |
|------|---------|
| **ID** | `afr_lean_condition` |
| **Type** | Fuel Enrichment |
| **Priority** | **Critical** |
| **Description** | Detected 3760 lean AFR readings (>15.0). Average AFR: 14.75 |
| **Safety Impact** | Prevents engine damage from lean conditions |
| **Performance Impact** | Safer operation, prevents detonation |

## Recommended Change

- **Parameter**: `fuel_map`
- **Change Type**: Increase by **8%**
- **Effective Range**: **5.3 psi** at **1808 rpm**
- **Tuning Cells**:
  - Pressure range: 1.9–19.1 psi
  - RPM range: 307–4714 rpm
- **Tuning Strategy**: `weighted_average_4x4`
- **Affected Areas**: Lean AFR regions in the fuel map

The goal is to enrich the fuel mixture in the highlighted regions to bring the AFR back into a safe range. This prevents detonation and maintains reliability.

## Why It Matters

The "tuning-ai" agent analyzes datalogs to detect dangerous conditions. In this case, the engine ran lean more than three thousand times, which can lead to higher combustion temperatures and potential engine damage. Increasing fuel in the specified cells reduces the risk and helps maintain consistent power delivery.

For additional data verification steps, see [docs/data_validation.md](data_validation.md).

