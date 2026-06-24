# Redrob Intelligent Candidate Ranking System

This repository implements a high-performance, explainable, and zero-network-call candidate ranking system for the "India Runs — Data & AI Challenge: Intelligent Candidate Discovery" hackathon.

## System Architecture

The ranking system uses a two-stage funnel designed for speed, compliance, and auditing:

1. **Honeypot Filter (`honeypot_filter.py`)**: Filters out inconsistent or fake profiles based on experience mismatches and expert skills with zero duration.
2. **Hard Exclusion Engine (`exclusion_engine.py`)**: Implements strict job description (JD) filters (such as location/visa constraints, consulting/research-only profiles, and stale architecture experience).
3. **Decomposable Scoring (`scoring.py`)**: Base fit combines local embeddings, skill match metrics, narrative matches, and experience-band fit, which are then multiplied by candidate activity, location fit, and notice-period fit.
4. **Deterministic Reasoning (`reasoning.py`)**: Generates 1-2 sentence explanations using deterministic rotating templates to avoid LLM hallucinations.

## Setup Instructions

Ensure Python 3.10+ is installed.

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

```bash
# 1. Precompute embeddings (one-time step)
python -m scripts.precompute_embeddings

# 2. Run the ranking pipeline
python -m src.rank --candidates ./data/candidates.jsonl --out ./submission.csv
```
