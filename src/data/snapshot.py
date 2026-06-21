"""DAO governance — Snapshot.org GraphQL (free, no key).

Snapshot is where most DeFi protocols run off-chain governance votes. Recent
proposals and turnout are a read on how actively a protocol is being steered."""

import requests

HUB = "https://hub.snapshot.org/graphql"
HEAD = {"User-Agent": "FinR1-Terminal/0.2", "Content-Type": "application/json"}

# Subject symbol / slug → Snapshot space ENS.
SPACES = {
    "UNISWAP": "uniswapgovernance.eth", "uniswap": "uniswapgovernance.eth",
    "AAVE": "aavedao.eth", "aave": "aavedao.eth",
    "CURVE": "curve.eth", "curve-dex": "curve.eth",
    "COMPOUND": "comp-vote.eth", "compound-finance": "comp-vote.eth",
    "ENS": "ens.eth", "ARB": "arbitrumfoundation.eth", "ARBITRUM": "arbitrumfoundation.eth",
    "OP": "opcollective.eth", "OPTIMISM": "opcollective.eth",
    "BALANCER": "balancer.eth", "SUSHI": "sushigov.eth",
    "FRAX": "frax.eth", "GMX": "gmx.eth", "PENDLE": "pendle.eth",
    "LIDO": "lido-snapshot.eth", "lido": "lido-snapshot.eth",
    "MAKER": "makerdao.eth", "makerdao": "makerdao.eth", "SKY": "makerdao.eth",
    "STARKNET": "starknet.eth", "SAFE": "safe.eth", "DYDX": "dydxgov.eth", "dydx": "dydxgov.eth",
}

_STATE = {"active": "● live", "closed": "closed", "pending": "pending"}


def space_for(token: str):
    return SPACES.get(token) or SPACES.get((token or "").upper())


def governance(token: str, name: str = "") -> str:
    space = space_for(token)
    if not space:
        return (f"No Snapshot governance space mapped for {name or token}.\n"
                "  Covered: Uniswap, Aave, Curve, Compound, ENS, Arbitrum, "
                "Optimism, Lido, Maker, GMX, Pendle, dYdX …")
    query = """
    { proposals(first: 10, where: {space: "%s"}, orderBy: "created", orderDirection: desc)
      { title state votes scores_total end } }""" % space
    try:
        r = requests.post(HUB, json={"query": query}, headers=HEAD, timeout=20)
        r.raise_for_status()
        proposals = (r.json().get("data") or {}).get("proposals") or []
    except Exception as e:
        return f"Could not fetch governance for {name or token}: {e}"
    if not proposals:
        return f"No recent Snapshot proposals for {space}."

    from datetime import datetime
    out = [
        f"Governance — {name or token}  ({space})",
        "Source: Snapshot.org",
        "",
        f"  {'State':<9}{'Votes':>8}{'Power':>12}  Proposal",
        "  " + "─" * 60,
    ]
    for p in proposals:
        state = _STATE.get(p.get("state", ""), p.get("state", ""))
        votes = p.get("votes") or 0
        power = p.get("scores_total") or 0
        power_s = f"{power/1e6:.1f}M" if power >= 1e6 else f"{power/1e3:.0f}k" if power >= 1e3 else f"{power:.0f}"
        title = (p.get("title") or "").replace("\n", " ")[:34]
        out.append(f"  {state:<9}{votes:>8,}{power_s:>12}  {title}")
    return "\n".join(out)
