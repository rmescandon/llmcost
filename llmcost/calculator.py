from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import CostResult, SourceCost
from .providers.openrouter import fetch_openrouter_prices, find_model
from .providers.litellm import fetch_litellm_prices


def _compute(
    source_name: str, fetch_fn, model: str, input_tokens: int, output_tokens: int
) -> SourceCost:
    try:
        prices = fetch_fn()
        pricing = (
            find_model(model, prices)
            if source_name == "openrouter"
            else prices.get(model)
        )
        if pricing is None:
            return SourceCost(
                source=source_name,
                total_cost_usd=None,
                price_per_million_input=None,
                price_per_million_output=None,
                error=f"Model '{model}' not found",
            )
        cost = pricing["prompt"] * input_tokens + pricing["completion"] * output_tokens
        return SourceCost(
            source=source_name,
            total_cost_usd=cost,
            price_per_million_input=pricing["prompt"] * 1_000_000,
            price_per_million_output=pricing["completion"] * 1_000_000,
        )
    except Exception as e:
        return SourceCost(
            source=source_name,
            total_cost_usd=None,
            price_per_million_input=None,
            price_per_million_output=None,
            error=str(e),
        )


def _tokencost_source(model: str, input_tokens: int, output_tokens: int) -> SourceCost:
    try:
        from tokencost.costs import calculate_cost_by_tokens

        input_cost  = calculate_cost_by_tokens(input_tokens,  model, "input")
        output_cost = calculate_cost_by_tokens(output_tokens, model, "output")
        total = float(input_cost + output_cost)

        from tokencost.constants import TOKEN_COSTS
        entry = TOKEN_COSTS[model.lower()]

        return SourceCost(
            source="tokencost",
            total_cost_usd=total,
            price_per_million_input=float(entry["input_cost_per_token"]) * 1_000_000,
            price_per_million_output=float(entry["output_cost_per_token"]) * 1_000_000,
        )
    except KeyError as e:
        return SourceCost(
            source="tokencost", total_cost_usd=None,
            price_per_million_input=None, price_per_million_output=None,
            error=f"Model not found: {e}",
        )
    except ImportError:
        return SourceCost(
            source="tokencost", total_cost_usd=None,
            price_per_million_input=None, price_per_million_output=None,
            error="tokencost not installed",
        )
    except Exception as e:
        return SourceCost(
            source="tokencost", total_cost_usd=None,
            price_per_million_input=None, price_per_million_output=None,
            error=str(e),
        )


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> CostResult:
    tasks = {
        "litellm": (fetch_litellm_prices, model, input_tokens, output_tokens),
        "openrouter": (fetch_openrouter_prices, model, input_tokens, output_tokens),
    }

    results: dict[str, SourceCost] = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_compute, name, fn, m, i, o): name
            for name, (fn, m, i, o) in tasks.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            results[name] = future.result()

    # tokencost es local, no necesita thread
    results["tokencost"] = _tokencost_source(model, input_tokens, output_tokens)

    return CostResult(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        sources=[results["litellm"], results["openrouter"], results["tokencost"]],
    )
