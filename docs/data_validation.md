# Tuning Data Verification Guide

This guide outlines the key data points exposed by the application so that tuners can verify and validate every recommendation. It was prepared with advice from the `tuning-ai` expert agent.

## What the User Should See

- **ROM Metadata** – file name, size, checksum and parser version.
- **Analysis Metadata** – timestamps, tables parsed, issues count and safety status for traceability.
- **Detailed Tune Changes** – each change lists the parameter, new and old value range, affected cells and estimated impact.
- **Table Previews** – before/after values for ROM tables to cross-check with the original tune.
- **Compatibility Information** – ROM compatibility metrics and any warnings about unsupported tables.
- **Raw Exports** – downloadable JSON or CSV files containing all computed changes for offline review.

Consult this document when building UI components to ensure end users can inspect every value used by the AI recommendation engine.
