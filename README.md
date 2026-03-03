# LLM Cost Calculator

Calculate the cost of using large language models (LLMs) from various sources, including OpenAI and Litellm.

## As CLI

```bash
$ llm-cost --model gpt-4o --prompt-tokens 1000 --completion-tokens 500
```


## As library

```python
from llm_cost import calculate_cost

result = calculate_cost("gpt-4o", response.usage.prompt_tokens, response.usage.completion_tokens)

for source in result.available_sources:
    print(f"{source.source}: ${source.total_cost_usd:.6f}")

litellm_cost = next(s for s in result.sources if s.source == "litellm")
```
