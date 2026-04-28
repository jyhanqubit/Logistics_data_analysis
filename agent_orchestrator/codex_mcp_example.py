"""Minimal example: orchestrating Codex as an MCP server.

This file is intentionally illustrative. It requires the OpenAI Agents SDK and a local Codex CLI setup.
Run `codex mcp-server` through MCPServerStdio, then send engineering tasks to Codex.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

# Uncomment after installing the Agents SDK in your own environment.
# from agents import Agent, Runner
# from agents.mcp import MCPServerStdio


REPO_ROOT = Path(__file__).resolve().parents[1]


async def main() -> None:
    prompt = f"""
    You are the Codex development agent for ParcelFlow AI.
    Read AGENTS.md and improve the forecasting module.
    Working directory: {REPO_ROOT}
    Requirements:
    - keep python scripts/run_pipeline.py runnable
    - add tests for any new behavior
    - summarize the diff and risks
    """
    print("This is a template. Install Agents SDK and uncomment the MCP code to run it.")
    print(prompt)

    # Example shape only:
    # async with MCPServerStdio(params={"command": "codex", "args": ["mcp-server"]}) as codex_server:
    #     agent = Agent(
    #         name="Portfolio Orchestrator",
    #         instructions="Delegate coding work to Codex and return a concise implementation summary.",
    #         mcp_servers=[codex_server],
    #     )
    #     result = await Runner.run(agent, prompt)
    #     print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
