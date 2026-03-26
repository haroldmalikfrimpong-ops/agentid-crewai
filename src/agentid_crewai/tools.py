"""AgentID tools for CrewAI.

Provides six tools that let CrewAI agents register, verify, discover,
and interact with other agents using the AgentID identity layer.

All tools read the API key from the AGENTID_API_KEY environment variable.
"""

import json
import os
import time
from typing import Optional

from crewai.tools import tool

import agentid


def _get_client() -> agentid.Client:
    """Return a shared AgentID client, initialised from env."""
    api_key = os.environ.get("AGENTID_API_KEY")
    if not api_key:
        raise RuntimeError(
            "AGENTID_API_KEY environment variable is not set. "
            "Get your key at https://getagentid.dev"
        )
    return agentid.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# 1. register_agent
# ---------------------------------------------------------------------------

@tool
def register_agent(
    name: str,
    description: str = "",
    capabilities: str = "",
    platform: str = "",
    endpoint: str = "",
) -> str:
    """Register a new agent with AgentID and receive a cryptographic identity.

    Use this tool when you need to create a new agent identity in the AgentID
    registry. Returns the agent_id and certificate that prove the agent's
    identity to other agents.

    Args:
        name: Human-readable name for the agent.
        description: What the agent does (optional).
        capabilities: Comma-separated list of capabilities, e.g. "search,chat,code" (optional).
        platform: Platform the agent runs on, e.g. "crewai" (optional).
        endpoint: URL where the agent can be reached (optional).
    """
    try:
        client = _get_client()
        caps = [c.strip() for c in capabilities.split(",") if c.strip()] if capabilities else []
        result = client.agents.register(
            name=name,
            description=description,
            capabilities=caps,
            platform=platform or "crewai",
            endpoint=endpoint or None,
        )
        return json.dumps({
            "status": "registered",
            "agent_id": getattr(result, "agent_id", None),
            "certificate": getattr(result, "certificate", None),
            "name": name,
        }, indent=2)
    except Exception as e:
        return f"Error registering agent: {e}"


# ---------------------------------------------------------------------------
# 2. verify_agent
# ---------------------------------------------------------------------------

@tool
def verify_agent(agent_id: str) -> str:
    """Verify another agent's identity using the AgentID registry.

    Use this tool before trusting or interacting with another agent. It checks
    whether the agent_id is valid, returns the agent's verified status, trust
    level, and certificate details.

    Args:
        agent_id: The unique AgentID identifier of the agent to verify (e.g. "agent_abc123").
    """
    try:
        client = _get_client()
        result = client.agents.verify(agent_id=agent_id)
        return json.dumps({
            "agent_id": agent_id,
            "verified": getattr(result, "verified", False),
            "trust_score": getattr(result, "trust_score", None),
            "name": getattr(result, "name", None),
            "certificate_valid": getattr(result, "certificate_valid", None),
        }, indent=2)
    except Exception as e:
        return f"Error verifying agent '{agent_id}': {e}"


# ---------------------------------------------------------------------------
# 3. discover_agents
# ---------------------------------------------------------------------------

@tool
def discover_agents(
    capability: str = "",
    owner: str = "",
    limit: int = 10,
) -> str:
    """Search the AgentID registry for agents by capability or owner.

    Use this tool when you need to find other agents that can perform a
    specific task (e.g. "search", "code", "payment") or that belong to
    a specific owner.

    Args:
        capability: Filter by capability, e.g. "search" or "payment" (optional).
        owner: Filter by owner email or organisation (optional).
        limit: Maximum number of results to return (default 10, max 50).
    """
    try:
        client = _get_client()
        results = client.agents.discover(
            capability=capability or None,
            owner=owner or None,
            limit=min(limit, 50),
        )
        agents = []
        for r in results:
            agents.append({
                "agent_id": getattr(r, "agent_id", None),
                "name": getattr(r, "name", None),
                "capabilities": getattr(r, "capabilities", []),
                "trust_score": getattr(r, "trust_score", None),
            })
        return json.dumps({
            "count": len(agents),
            "agents": agents,
        }, indent=2)
    except Exception as e:
        return f"Error discovering agents: {e}"


# ---------------------------------------------------------------------------
# 4. check_trust_level
# ---------------------------------------------------------------------------

@tool
def check_trust_level(agent_id: str) -> str:
    """Check an agent's trust level (L0-L4), permissions, and spending limit.

    Use this tool to understand what an agent is allowed to do before
    delegating tasks or trusting its output. Trust levels range from
    L0 (unverified) to L4 (full authority).

    Trust level summary:
      L0 — Unverified: no permissions
      L1 — Basic: read, discover
      L2 — Verified: + send messages, connect
      L3 — Trusted: + handle data, payments up to $100/day
      L4 — Full Authority: + sign contracts, manage funds up to $10,000/day

    Args:
        agent_id: The AgentID identifier of the agent to check.
    """
    try:
        client = _get_client()
        result = client.agents.verify(agent_id=agent_id)
        agent_data = result._data if hasattr(result, "_data") else {}

        level = agentid.calculate_trust_level(agent_data)
        permissions = agentid.TRUST_PERMISSIONS.get(level, [])
        spending_limit = agentid.get_spending_limit(level)
        requirements = agentid.level_up_requirements(level, agent_data)

        level_labels = {
            0: "L0 — Unverified",
            1: "L1 — Basic",
            2: "L2 — Verified",
            3: "L3 — Trusted",
            4: "L4 — Full Authority",
        }

        return json.dumps({
            "agent_id": agent_id,
            "trust_level": int(level),
            "trust_level_label": level_labels.get(int(level), f"L{int(level)}"),
            "permissions": permissions,
            "daily_spending_limit_usd": spending_limit,
            "level_up": requirements,
        }, indent=2)
    except Exception as e:
        return f"Error checking trust level for '{agent_id}': {e}"


# ---------------------------------------------------------------------------
# 5. check_spending_authority
# ---------------------------------------------------------------------------

@tool
def check_spending_authority(
    agent_id: str,
    amount: float,
    currency: str = "usd",
) -> str:
    """Check whether an agent is authorised to spend a given amount.

    Use this tool before initiating any payment or purchase on behalf of
    an agent. It verifies the agent's trust level is sufficient and that
    the amount is within the daily spending limit.

    Args:
        agent_id: The AgentID identifier of the agent.
        amount: The amount to check (e.g. 25.00).
        currency: Currency code (default "usd").
    """
    try:
        api_key = os.environ.get("AGENTID_API_KEY")
        if not api_key:
            return "Error: AGENTID_API_KEY environment variable is not set."

        spending = agentid.SpendingClient(api_key=api_key)
        result = spending.check_spending_authority(
            agent_id=agent_id,
            amount=amount,
            currency=currency,
        )

        return json.dumps({
            "agent_id": agent_id,
            "amount": amount,
            "currency": currency,
            "authorized": getattr(result, "authorized", False),
            "reason": getattr(result, "reason", None),
            "trust_level": getattr(result, "trust_level", None),
            "daily_limit": getattr(result, "daily_limit", None),
            "spent_today": getattr(result, "spent_today", None),
            "remaining_daily_limit": getattr(result, "remaining_daily_limit", None),
        }, indent=2)
    except Exception as e:
        return f"Error checking spending authority for '{agent_id}': {e}"


# ---------------------------------------------------------------------------
# 6. create_signed_handoff
# ---------------------------------------------------------------------------

@tool
def create_signed_handoff(
    from_agent_id: str,
    to_agent_id: str,
    summary: str,
    private_key_hex: str = "",
) -> str:
    """Create a cryptographically signed handoff receipt between two agents.

    Use this tool when transferring a task from one agent to another. The
    handoff is signed with Ed25519 so the receiving agent can verify the
    sending agent's identity. If no private key is provided, a new keypair
    is generated for the handoff.

    Args:
        from_agent_id: AgentID of the agent handing off the task.
        to_agent_id: AgentID of the agent receiving the task.
        summary: Description of what is being handed off.
        private_key_hex: 64-char hex Ed25519 private key seed (optional — a new key is generated if omitted).
    """
    try:
        if private_key_hex:
            identity = agentid.Ed25519Identity.from_seed(bytes.fromhex(private_key_hex))
        else:
            identity = agentid.Ed25519Identity.generate()

        timestamp = int(time.time())
        handoff_payload = (
            f"agentid-handoff:{from_agent_id}:{to_agent_id}:{timestamp}:{summary}"
        )
        signature = identity.sign(handoff_payload.encode())

        return json.dumps({
            "handoff": {
                "from_agent": from_agent_id,
                "to_agent": to_agent_id,
                "summary": summary,
                "timestamp": timestamp,
            },
            "crypto": {
                "algorithm": "Ed25519",
                "payload": handoff_payload,
                "signature": signature.hex(),
                "public_key": identity.ed25519_public_key_hex,
            },
            "verification": (
                "Verify by checking the Ed25519 signature over 'payload' "
                "using the provided 'public_key'."
            ),
        }, indent=2)
    except Exception as e:
        return f"Error creating signed handoff: {e}"
