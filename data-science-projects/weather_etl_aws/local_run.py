"""Run the full Step Functions pipeline locally — no AWS credentials needed.

Interprets the state-machine JSON (Task, Choice, Pass, Catch, Retry) and
invokes each Lambda's handler in-process. Prints each state's input →
output so the pipeline is auditable end-to-end.
"""
from __future__ import annotations

import importlib
import json
import string
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "lambdas"))

# Load and substitute the ASL template (only the Task ARNs are placeholders)
ASL = (HERE / "statemachine" / "pipeline.asl.json").read_text()
substitutions = {
    "FetchArn":    "fetch_weather.handler",
    "ValidateArn": "validate.handler",
    "TransformArn": "transform.handler",
    "LoadArn":     "load_partitioned.handler",
    "NotifyArn":   "notify_failure.handler",
}
ASL = string.Template(ASL.replace("${", "${")).safe_substitute(substitutions)
SM = json.loads(ASL)


def invoke(fn_ref: str, payload: dict) -> dict:
    module_name, handler_name = fn_ref.split(".")
    module = importlib.import_module(module_name)
    fn = getattr(module, handler_name)
    return fn(payload, None)


def run():
    state_name = SM["StartAt"]
    ctx = {}
    while True:
        state = SM["States"][state_name]
        t = state["Type"]
        print(f"\n── {state_name}  ({t})")

        if t == "Task":
            fn_ref = state["Parameters"]["FunctionName"]
            payload = ctx if state["Parameters"].get("Payload.$") == "$" else ctx
            attempts = 0
            retries = state.get("Retry", [{}])[0]
            max_attempts = retries.get("MaxAttempts", 0)
            while True:
                try:
                    result = {"Payload": invoke(fn_ref, payload)}
                    break
                except Exception as e:  # noqa: BLE001
                    attempts += 1
                    if attempts > max_attempts:
                        catch = state.get("Catch", [])
                        if catch:
                            state_name = catch[0]["Next"]
                            ctx = {"error": {"Cause": str(e)}}
                            break
                        raise
                    delay = retries.get("IntervalSeconds", 1) * (
                        retries.get("BackoffRate", 1.0) ** (attempts - 1)
                    )
                    print(f"   retry {attempts}/{max_attempts} in {delay}s :: {e}")
                    time.sleep(delay)
            else:
                pass
            if "error" in ctx:
                # jumped to catch — will re-enter loop with new state_name
                continue

            # ResultSelector picks specific fields from the Lambda payload.
            sel = state.get("ResultSelector", {})
            if sel:
                new_ctx = {}
                for k, v in sel.items():
                    key = k.rstrip(".$")
                    # v is like "$.Payload.records" — walk the path
                    path = v.lstrip("$").lstrip(".").split(".")
                    node = result
                    for step in path:
                        node = node[step]
                    new_ctx[key] = node
                ctx = new_ctx
            else:
                ctx = result["Payload"]
            print(f"   -> {json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in ctx.items() if k != 'records'}, default=str)}")

        elif t == "Choice":
            picked = None
            for c in state["Choices"]:
                var = c["Variable"].lstrip("$").lstrip(".")
                if "NumericGreaterThan" in c and ctx.get(var, 0) > c["NumericGreaterThan"]:
                    picked = c["Next"]; break
            state_name = picked or state["Default"]
            print(f"   -> choice: {state_name}")
            continue

        elif t == "Pass":
            print(f"   -> pass {state.get('Result')}")
            if state.get("End"): break
            state_name = state["Next"]; continue

        if state.get("End"):
            print(f"\nPipeline finished. Final: {json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in ctx.items() if k != 'records'}, default=str)}")
            return ctx
        state_name = state["Next"]


if __name__ == "__main__":
    run()
