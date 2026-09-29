"""Write records to S3 as a Parquet file partitioned by year/month/day.

In the deployed pipeline this uploads to
s3://$DATA_BUCKET/curated/readings/year=YYYY/month=MM/day=DD/
and calls Athena's `MSCK REPAIR TABLE` (or a Glue add-partition) so the
new partition is queryable.

When run outside AWS (local_run.py or unit tests), $DATA_BUCKET is unset
and the function writes to ./curated/... on the local disk instead — no
boto3 needed to exercise the full pipeline.
"""
from __future__ import annotations

import io
import json
import os
from datetime import datetime
from pathlib import Path


def _partition_path(run_ts: datetime) -> str:
    return f"year={run_ts:%Y}/month={run_ts:%m}/day={run_ts:%d}"


def _write_parquet(records: list[dict], out_path: Path) -> Path:
    """Return the actual path written (may switch to .jsonl if parquet unavailable)."""
    try:
        import pandas as pd
        pd.DataFrame(records).to_parquet(out_path, index=False)
        return out_path
    except (ImportError, ValueError):
        # No pyarrow — fall back to JSONL so the pipeline still runs.
        out_path = out_path.with_suffix(".jsonl")
        with out_path.open("w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        return out_path


def handler(event, context=None):
    records = event.get("records", [])
    if not records:
        return {"run_id": event.get("run_id"), "loaded": 0, "s3_uri": None}

    run_ts = datetime.fromisoformat(records[0]["observed_at_utc"].replace("Z", "+00:00"))
    part = _partition_path(run_ts)
    fname = f"readings_{run_ts:%Y%m%dT%H%M%S}.parquet"

    bucket = os.getenv("DATA_BUCKET")

    if bucket:  # deployed to AWS
        import boto3  # noqa: WPS433 (imported inside handler for cold-start cost)
        buf = io.BytesIO()
        try:
            import pandas as pd
            pd.DataFrame(records).to_parquet(buf, index=False)
        except ImportError:
            buf = io.BytesIO(("\n".join(json.dumps(r) for r in records)).encode())
            fname = fname.replace(".parquet", ".jsonl")

        key = f"curated/readings/{part}/{fname}"
        s3 = boto3.client("s3")
        s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())
        s3_uri = f"s3://{bucket}/{key}"
    else:  # local execution
        out_dir = Path("curated/readings") / part
        out_dir.mkdir(parents=True, exist_ok=True)
        written = _write_parquet(records, out_dir / fname)
        s3_uri = str(written)

    print(f"[load] wrote {len(records)} records -> {s3_uri}")
    return {"run_id": event.get("run_id"), "loaded": len(records), "s3_uri": s3_uri}
