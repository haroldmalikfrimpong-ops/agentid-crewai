# agentid-crewai

AgentID tools for [CrewAI](https://www.crewai.com/) — cryptographic identity verification for AI agents.

Gives your CrewAI agents the ability to register identities, verify other agents, discover collaborators, check trust levels, validate spending authority, and create signed handoff receipts — all backed by [AgentID](https://getagentid.dev).

## Installation

```bash
pip install agentid-crewai
```

## Quick start

```python
from crewai import Agent
from agentid_crewai import get_all_tools

agent = Agent(
    role="Verified Agent",
    goal="Verify identities before collaborating with other agents",
    backstory="A security-conscious agent that always checks credentials.",
    tools=get_all_tools(),
)
```

Set your API key:

```bash
export AGENTID_API_KEY="agentid_sk_..."
```

## Tools

| Tool | Description |
|------|-------------|
| `register_agent` | Register a new agent and receive an agent_id + certificate |
| `verify_agent` | Verify another agent's identity and trust status |
| `discover_agents` | Search the registry by capability or owner |
| `check_trust_level` | Get an agent's L0-L4 trust level, permissions, and spending limit |
| `check_spending_authority` | Check if an agent can spend a given amount |
| `create_signed_handoff` | Create an Ed25519-signed handoff receipt between agents |

## Trust levels

| Level | Label | Permissions | Daily spend |
|-------|-------|-------------|-------------|
| L0 | Unverified | None | $0 |
| L1 | Basic | read, discover | $0 |
| L2 | Verified | + send messages, connect | $0 |
| L3 | Trusted | + handle data, payments | $100 |
| L4 | Full Authority | + sign contracts, manage funds | $10,000 |

## Using individual tools

```python
from agentid_crewai import register_agent, verify_agent, check_trust_level

# Pick only the tools you need
agent = Agent(
    role="Auditor",
    goal="Audit agent trust levels",
    tools=[verify_agent, check_trust_level],
)
```

## Multi-agent example

```python
from crewai import Agent, Task, Crew
from agentid_crewai import get_all_tools

verifier = Agent(
    role="Identity Verifier",
    goal="Verify all agents before they join the crew",
    backstory="Security specialist that validates cryptographic identities.",
    tools=get_all_tools(),
)

task = Task(
    description="Verify agent_abc123 and report their trust level and permissions.",
    expected_output="Trust level report with permissions and spending limit.",
    agent=verifier,
)

crew = Crew(agents=[verifier], tasks=[task])
result = crew.kickoff()
```

## Development

```bash
git clone https://github.com/haroldmalikfrimpong-ops/getagentid-crewai.git
cd getagentid-crewai
pip install -e ".[dev]"
pytest
```

## Links

- [AgentID](https://getagentid.dev) — The identity layer for AI agents
- [AgentID Python SDK](https://pypi.org/project/getagentid/) — `pip install getagentid`
- [CrewAI](https://www.crewai.com/) — AI agent orchestration framework

## License

MIT
