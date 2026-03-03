import argparse
import sys
from .calculator import calculate_cost


def main() -> None:
    parser = argparse.ArgumentParser(prog="llmcost")
    parser.add_argument("model")
    parser.add_argument("input_tokens", type=int)
    parser.add_argument("output_tokens", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = calculate_cost(args.model, args.input_tokens, args.output_tokens)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Model:  {result.model}  ({result.input_tokens} in / {result.output_tokens} out)\n")
        for s in result.sources:
            if s.available:
                print(f"  [{s.source:<12}] ${s.total_cost_usd:.6f} USD")
            else:
                print(f"  [{s.source:<12}] unavailable — {s.error}")
