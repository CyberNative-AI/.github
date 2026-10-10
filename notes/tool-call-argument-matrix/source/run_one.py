"""Run one agent framework, at its default settings, against the tool-call argument matrix mock model.

usage: python run_one.py <framework> <scenario> <base_url>
Tools record every invocation (the exact keyword arguments they received) to $TOOL_LOG.
Prints one line: RESULT {"outcome": "final"|"exception", "type": ..., "message": ...}
Only the endpoint, a dummy key and the model name are configured; everything else is default.
"""

import asyncio
import json
import os
import sys
from typing import Optional

PROMPT = "List my archived items. Use the tools."
SYSTEM = "You are a helpful assistant. Use tools when useful."
MODEL = "mock-model"
KEY = "sk-mock"
RUN_ID = os.environ.get("RUN_ID", "")


def _record(tool: str, kwargs: dict) -> None:
    with open(os.environ["TOOL_LOG"], "a", encoding="utf-8") as f:
        f.write(json.dumps({"run_id": RUN_ID, "tool": tool, "kwargs": kwargs}, sort_keys=True, default=repr) + "\n")


def list_items(status: Optional[str] = None) -> str:
    """List the user's items, optionally only those with a given status (default: all items)."""
    _record("list_items", {"status": status})
    return f"Listed items with status={status or 'all'}: item-1, item-2."


def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    _record("get_weather", {"city": city})
    return f"It is sunny in {city}."


# ---------------------------------------------------------------- frameworks

def run_openai_agents(scenario, base_url):
    from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
    from openai import AsyncOpenAI

    set_tracing_disabled(True)
    model = OpenAIChatCompletionsModel(model=MODEL, openai_client=AsyncOpenAI(base_url=base_url, api_key=KEY))
    kw = {}
    agent = Agent(name="assistant", instructions=SYSTEM, model=model,
                  tools=[function_tool(get_weather), function_tool(list_items)], **kw)
    return str(Runner.run_sync(agent, PROMPT).final_output)


def run_langchain(scenario, base_url):
    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=MODEL, base_url=base_url, api_key=KEY)
    kw = {}
    agent = create_agent(llm, tools=[get_weather, list_items], system_prompt=SYSTEM, **kw)
    out = agent.invoke({"messages": [{"role": "user", "content": PROMPT}]})
    return str(out.get("structured_response") or out["messages"][-1].content)


def run_crewai(scenario, base_url):
    from crewai import LLM, Agent, Crew, Task
    from crewai.tools import tool

    gw = tool("get_weather")(get_weather)
    ft = tool("list_items")(list_items)
    llm = LLM(model=f"openai/{MODEL}", base_url=base_url, api_key=KEY)
    agent = Agent(role="Assistant", goal="Answer the user's request", backstory=SYSTEM,
                  tools=[gw, ft], llm=llm, verbose=False)
    kw = {}
    task = Task(description=PROMPT, expected_output="The answer to the request.", agent=agent, **kw)
    return str(Crew(agents=[agent], tasks=[task], verbose=False).kickoff())


def run_smolagents(scenario, base_url):
    from smolagents import OpenAIServerModel, ToolCallingAgent, tool

    @tool
    def get_weather_t(city: str) -> str:
        """Return the current weather for a city.

        Args:
            city: the city name
        """
        return get_weather(city)

    @tool
    def list_items_t(status: Optional[str] = None) -> str:
        """List the user's items, optionally only those with a given status (default: all items).

        Args:
            status: only items with this status; omit for all items
        """
        return list_items(status)

    get_weather_t.name = "get_weather"
    list_items_t.name = "list_items"
    model = OpenAIServerModel(model_id=MODEL, api_base=base_url, api_key=KEY)
    agent = ToolCallingAgent(tools=[get_weather_t, list_items_t], model=model, verbosity_level=0)
    return str(agent.run(PROMPT))


def run_pydantic_ai(scenario, base_url):
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    model = OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=base_url, api_key=KEY))
    kw = {}
    agent = Agent(model, system_prompt=SYSTEM, tools=[get_weather, list_items], **kw)
    return str(agent.run_sync(PROMPT).output)


def run_llama_index(scenario, base_url):
    from llama_index.core.agent.workflow import FunctionAgent
    from llama_index.core.tools import FunctionTool
    from llama_index.llms.openai_like import OpenAILike

    llm = OpenAILike(model=MODEL, api_base=base_url, api_key=KEY, is_chat_model=True,
                     is_function_calling_model=True, context_window=128000)
    kw = {}
    agent = FunctionAgent(tools=[FunctionTool.from_defaults(get_weather), FunctionTool.from_defaults(list_items)],
                          llm=llm, system_prompt=SYSTEM, **kw)

    async def go():
        return await agent.run(user_msg=PROMPT)

    return str(asyncio.run(go()))


def run_autogen(scenario, base_url):
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    client = OpenAIChatCompletionClient(
        model=MODEL, base_url=base_url, api_key=KEY,
        model_info={"vision": False, "function_calling": True, "json_output": True,
                    "family": "unknown", "structured_output": True},
    )
    kw = {}
    tools = [] if kw else [get_weather, list_items]  # structured output requires strict tools; keep defaults
    agent = AssistantAgent("assistant", model_client=client, tools=tools,
                           system_message=SYSTEM, **kw)

    async def go():
        r = await agent.run(task=PROMPT)
        return r.messages[-1].to_text() if r.messages else ""

    return asyncio.run(go())


def run_strands(scenario, base_url):
    from strands import Agent, tool
    from strands.models.openai import OpenAIModel

    model = OpenAIModel(client_args={"api_key": KEY, "base_url": base_url}, model_id=MODEL)
    agent = Agent(model=model, tools=[tool(get_weather), tool(list_items)], system_prompt=SYSTEM,
                  callback_handler=None)
    return str(agent(PROMPT))


def run_google_adk(scenario, base_url):
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    kw = {}
    tools = [get_weather, list_items]
    agent = LlmAgent(name="assistant", model=LiteLlm(model=f"openai/{MODEL}", api_base=base_url, api_key=KEY),
                     instruction=SYSTEM, tools=tools, **kw)
    svc = InMemorySessionService()

    async def go():
        await svc.create_session(app_name="toolcall_matrix", user_id="u", session_id="s")
        runner = Runner(agent=agent, app_name="toolcall_matrix", session_service=svc)
        last = ""
        async for ev in runner.run_async(user_id="u", session_id="s",
                                         new_message=types.Content(role="user", parts=[types.Part(text=PROMPT)])):
            if ev.content and ev.content.parts:
                for p in ev.content.parts:
                    if getattr(p, "text", None):
                        last = p.text
        return last

    return asyncio.run(go())


RUNNERS = {
    "openai-agents": run_openai_agents,
    "langchain": run_langchain,
    "crewai": run_crewai,
    "smolagents": run_smolagents,
    "pydantic-ai": run_pydantic_ai,
    "llama-index": run_llama_index,
    "autogen": run_autogen,
    "strands": run_strands,
    "google-adk": run_google_adk,
}


def main() -> None:
    fw, scenario, base_url = sys.argv[1:4]
    try:
        out = RUNNERS[fw](scenario, base_url)
        res = {"outcome": "final", "type": None, "message": str(out)[:300]}
    except BaseException as e:  # noqa: BLE001 - record every terminal cause
        res = {"outcome": "exception", "type": f"{type(e).__module__}.{type(e).__name__}", "message": str(e)[:300]}
    sys.stdout.flush()
    os.write(1, ("\nRESULT " + json.dumps(res, sort_keys=True) + "\n").encode())


if __name__ == "__main__":
    main()
