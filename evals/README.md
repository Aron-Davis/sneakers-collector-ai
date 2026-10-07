# LLM Evaluations

This directory contains evaluation datasets and runners for the
LLM-powered components of Sneakers Collector.

## Model

- Model: qwen2.5:3b
- Runtime: Ollama
- Structured output validated with Pydantic

## Routing baseline v1

Dataset:
- 18 cases

Results:
- Routing accuracy: 100.0%

The routing evaluation checks both:
- selected action
- action arguments such as query and sneaker_id

## Extraction baseline v1

Dataset:
- 12 cases
- 88 evaluated fields

Results:
- Case accuracy: 75.0%
- Field accuracy: 95.5%

Known failure modes:
- Negative box statements may be extracted as null instead of false.
- Heavily worn sneakers may be classified as used instead of worn.
- Natural-language dates may be incorrectly normalized.

The evaluation datasets are kept separate from prompt-specific fixes
to reduce the risk of overfitting prompts to individual examples.