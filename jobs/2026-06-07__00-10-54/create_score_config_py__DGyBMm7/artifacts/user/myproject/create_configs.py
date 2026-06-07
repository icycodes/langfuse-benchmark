#!/usr/bin/env python3
"""Create Langfuse score configs for the current Zealt run.

This script creates two project-level score configurations via the
Langfuse Python SDK public API and writes the returned IDs to output.log.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langfuse import get_client
from langfuse.api.commons.types import ConfigCategory, ScoreConfigDataType

OUTPUT_PATH = Path(__file__).with_name("output.log")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def _find_score_config_id(langfuse: Any, name: str) -> str | None:
    """Return an existing score config ID by name, if one is present.

    Score config names should be unique per run. This fallback only makes the
    script safe to rerun after a partial success.
    """
    page = 1
    limit = 100

    while True:
        response = langfuse.api.score_configs.get(page=page, limit=limit)
        configs = getattr(response, "data", None) or []

        for config in configs:
            if getattr(config, "name", None) == name:
                return getattr(config, "id")

        meta = getattr(response, "meta", None)
        total_pages = getattr(meta, "total_pages", None) or getattr(meta, "totalPages", None)
        if total_pages is not None:
            if page >= total_pages:
                return None
        elif len(configs) < limit:
            return None

        page += 1


def _create_or_find_numeric_config(langfuse: Any, name: str) -> str:
    try:
        config = langfuse.api.score_configs.create(
            name=name,
            data_type=ScoreConfigDataType.NUMERIC,
            description="Bounded numeric response quality rating for this evaluation run.",
            min_value=1.0,
            max_value=5.0,
        )
        return config.id
    except Exception:
        existing_id = _find_score_config_id(langfuse, name)
        if existing_id:
            return existing_id
        raise


def _create_or_find_categorical_config(langfuse: Any, name: str) -> str:
    categories = [
        ConfigCategory(value=-1.0, label="negative"),
        ConfigCategory(value=0.0, label="neutral"),
        ConfigCategory(value=1.0, label="positive"),
    ]

    try:
        config = langfuse.api.score_configs.create(
            name=name,
            data_type=ScoreConfigDataType.CATEGORICAL,
            description="Sentiment bucket assigned to the evaluated response.",
            categories=categories,
        )
        return config.id
    except Exception:
        existing_id = _find_score_config_id(langfuse, name)
        if existing_id:
            return existing_id
        raise


def main() -> None:
    run_id = _require_env("ZEALT_RUN_ID")
    _require_env("LANGFUSE_PUBLIC_KEY")
    _require_env("LANGFUSE_SECRET_KEY")
    _require_env("LANGFUSE_BASE_URL")

    langfuse = get_client()

    numeric_id = _create_or_find_numeric_config(langfuse, f"quality-{run_id}")
    categorical_id = _create_or_find_categorical_config(langfuse, f"sentiment-{run_id}")

    OUTPUT_PATH.write_text(
        f"Numeric Score Config ID: {numeric_id}\n"
        f"Categorical Score Config ID: {categorical_id}\n",
        encoding="utf-8",
    )

    langfuse.flush()


if __name__ == "__main__":
    main()
