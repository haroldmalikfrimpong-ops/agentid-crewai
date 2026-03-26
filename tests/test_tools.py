"""Tests for agentid_crewai tools.

These tests verify tool metadata and structure without making real API calls.
"""

import pytest

from agentid_crewai import (
    register_agent,
    verify_agent,
    discover_agents,
    check_trust_level,
    check_spending_authority,
    create_signed_handoff,
    get_all_tools,
)


# ---------------------------------------------------------------------------
# Tool collection
# ---------------------------------------------------------------------------

class TestGetAllTools:
    def test_returns_list(self):
        tools = get_all_tools()
        assert isinstance(tools, list)

    def test_returns_six_tools(self):
        tools = get_all_tools()
        assert len(tools) == 6

    def test_all_tools_are_callable(self):
        for t in get_all_tools():
            assert callable(t)


# ---------------------------------------------------------------------------
# Individual tool metadata
# ---------------------------------------------------------------------------

class TestToolNames:
    def test_register_agent_name(self):
        assert register_agent.name == "register_agent"

    def test_verify_agent_name(self):
        assert verify_agent.name == "verify_agent"

    def test_discover_agents_name(self):
        assert discover_agents.name == "discover_agents"

    def test_check_trust_level_name(self):
        assert check_trust_level.name == "check_trust_level"

    def test_check_spending_authority_name(self):
        assert check_spending_authority.name == "check_spending_authority"

    def test_create_signed_handoff_name(self):
        assert create_signed_handoff.name == "create_signed_handoff"


class TestToolDescriptions:
    """Each tool must have a non-empty description for the LLM."""

    def test_all_tools_have_descriptions(self):
        for t in get_all_tools():
            assert t.description, f"Tool '{t.name}' has no description"

    def test_register_mentions_identity(self):
        assert "identity" in register_agent.description.lower()

    def test_verify_mentions_verify(self):
        assert "verify" in verify_agent.description.lower()

    def test_discover_mentions_search(self):
        assert "search" in discover_agents.description.lower()

    def test_trust_mentions_trust(self):
        assert "trust" in check_trust_level.description.lower()

    def test_spending_mentions_spend(self):
        assert "spend" in check_spending_authority.description.lower()

    def test_handoff_mentions_signed(self):
        assert "signed" in create_signed_handoff.description.lower()


# ---------------------------------------------------------------------------
# Signed handoff (local crypto — no API call needed)
# ---------------------------------------------------------------------------

class TestSignedHandoff:
    """The handoff tool uses local Ed25519 crypto, so we can test it end-to-end."""

    def test_handoff_returns_json(self):
        import json
        result = create_signed_handoff.run(
            from_agent_id="agent_sender",
            to_agent_id="agent_receiver",
            summary="Transfer search task",
        )
        data = json.loads(result)
        assert data["handoff"]["from_agent"] == "agent_sender"
        assert data["handoff"]["to_agent"] == "agent_receiver"
        assert "signature" in data["crypto"]
        assert "public_key" in data["crypto"]

    def test_handoff_with_provided_key(self):
        import json
        from agentid import Ed25519Identity

        identity = Ed25519Identity.generate()
        seed_hex = identity.seed.hex()

        result = create_signed_handoff.run(
            from_agent_id="agent_a",
            to_agent_id="agent_b",
            summary="Hand off analysis",
            private_key_hex=seed_hex,
        )
        data = json.loads(result)
        assert data["crypto"]["public_key"] == identity.ed25519_public_key_hex

    def test_handoff_signature_verifies(self):
        import json
        from agentid import Ed25519Identity

        result = create_signed_handoff.run(
            from_agent_id="agent_x",
            to_agent_id="agent_y",
            summary="Test verification",
        )
        data = json.loads(result)

        pub_key = bytes.fromhex(data["crypto"]["public_key"])
        payload = data["crypto"]["payload"].encode()
        signature = bytes.fromhex(data["crypto"]["signature"])

        assert Ed25519Identity.verify(pub_key, payload, signature)


# ---------------------------------------------------------------------------
# Error handling (no API key set)
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tools that require an API key should return a clear error, not crash."""

    def test_register_without_api_key(self, monkeypatch):
        monkeypatch.delenv("AGENTID_API_KEY", raising=False)
        result = register_agent.run(name="test-agent")
        assert "error" in result.lower()

    def test_verify_without_api_key(self, monkeypatch):
        monkeypatch.delenv("AGENTID_API_KEY", raising=False)
        result = verify_agent.run(agent_id="agent_fake")
        assert "error" in result.lower()

    def test_discover_without_api_key(self, monkeypatch):
        monkeypatch.delenv("AGENTID_API_KEY", raising=False)
        result = discover_agents.run(capability="search")
        assert "error" in result.lower()
