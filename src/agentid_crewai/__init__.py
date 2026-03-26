"""AgentID tools for CrewAI — cryptographic identity verification for AI agents.

Usage:
    from agentid_crewai import get_all_tools

    agent = Agent(role="Verified Agent", tools=get_all_tools())
"""

from .tools import (
    register_agent,
    verify_agent,
    discover_agents,
    check_trust_level,
    check_spending_authority,
    create_signed_handoff,
)

__version__ = "0.1.0"

__all__ = [
    "register_agent",
    "verify_agent",
    "discover_agents",
    "check_trust_level",
    "check_spending_authority",
    "create_signed_handoff",
    "get_all_tools",
]


def get_all_tools() -> list:
    """Return all AgentID tools as a list, ready to pass to a CrewAI Agent.

    Example:
        from crewai import Agent
        from agentid_crewai import get_all_tools

        agent = Agent(
            role="Identity Verifier",
            goal="Verify agent identities before collaboration",
            tools=get_all_tools(),
        )
    """
    return [
        register_agent,
        verify_agent,
        discover_agents,
        check_trust_level,
        check_spending_authority,
        create_signed_handoff,
    ]
