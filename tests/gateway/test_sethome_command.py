"""Tests for gateway /sethome persistence behavior."""

from __future__ import annotations

import os

import pytest
import yaml

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent
from gateway.session import SessionSource


def _make_event(
    *,
    platform: Platform = Platform.DISCORD,
    chat_id: str = "1234567890",
    chat_name: str = "general",
) -> MessageEvent:
    return MessageEvent(
        text="/sethome",
        source=SessionSource(
            platform=platform,
            chat_id=chat_id,
            chat_name=chat_name,
            chat_type="channel",
            user_id="u1",
            user_name="tester",
        ),
        message_id="m1",
    )


def _make_runner() -> object:
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(
        platforms={Platform.DISCORD: PlatformConfig(enabled=True, token="***")}
    )
    return runner


@pytest.mark.asyncio
async def test_sethome_writes_env_and_keeps_config_yaml_clean(tmp_path, monkeypatch):
    import gateway.run as gateway_run

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)

    config_path = tmp_path / "config.yaml"
    original_config = {"model": {"default": "openai/gpt-5-mini"}}
    config_path.write_text(yaml.safe_dump(original_config, sort_keys=False), encoding="utf-8")

    env_path = tmp_path / ".env"
    env_path.write_text("DISCORD_BOT_TOKEN=test-token\n", encoding="utf-8")

    runner = _make_runner()
    result = await runner._handle_set_home_command(_make_event())

    assert "Home channel set to **general**" in result
    assert os.environ["DISCORD_HOME_CHANNEL"] == "1234567890"
    assert "DISCORD_HOME_CHANNEL=1234567890" in env_path.read_text(encoding="utf-8")
    assert yaml.safe_load(config_path.read_text(encoding="utf-8")) == original_config
    assert "DISCORD_HOME_CHANNEL" not in config_path.read_text(encoding="utf-8")

    home_channel = runner.config.platforms[Platform.DISCORD].home_channel
    assert home_channel is not None
    assert home_channel.chat_id == "1234567890"
    assert home_channel.name == "general"
