import importlib
import os

import pytest

PROJECT_DIR = "/home/user/myproject"


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_langfuse_sdk_importable():
    try:
        importlib.import_module("langfuse")
    except ImportError as exc:  # pragma: no cover - assertion message
        pytest.fail(f"Langfuse Python SDK is not importable: {exc}")


def test_langfuse_langchain_callback_importable():
    try:
        module = importlib.import_module("langfuse.langchain")
    except ImportError as exc:  # pragma: no cover - assertion message
        pytest.fail(f"langfuse.langchain is not importable: {exc}")
    assert hasattr(module, "CallbackHandler"), (
        "langfuse.langchain.CallbackHandler is not available."
    )


def test_langchain_core_importable():
    try:
        importlib.import_module("langchain_core")
    except ImportError as exc:  # pragma: no cover - assertion message
        pytest.fail(f"langchain_core is not importable: {exc}")


def test_langchain_community_fake_chat_model_importable():
    try:
        module = importlib.import_module("langchain_community.chat_models.fake")
    except ImportError as exc:  # pragma: no cover - assertion message
        pytest.fail(
            "langchain_community.chat_models.fake is not importable: "
            f"{exc}"
        )
    assert hasattr(module, "FakeListChatModel"), (
        "FakeListChatModel is not available in langchain_community.chat_models.fake."
    )


def test_langfuse_public_key_env_set():
    assert os.environ.get("LANGFUSE_PUBLIC_KEY"), (
        "Environment variable LANGFUSE_PUBLIC_KEY is not set."
    )


def test_langfuse_secret_key_env_set():
    assert os.environ.get("LANGFUSE_SECRET_KEY"), (
        "Environment variable LANGFUSE_SECRET_KEY is not set."
    )


def test_langfuse_base_url_env_set():
    assert os.environ.get("LANGFUSE_BASE_URL"), (
        "Environment variable LANGFUSE_BASE_URL is not set."
    )


def test_run_id_env_set():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "Environment variable ZEALT_RUN_ID is not set."
    assert run_id.startswith("zr-"), (
        f"ZEALT_RUN_ID is expected to start with 'zr-', got: {run_id!r}"
    )
