# Malformed tool-call arguments: a pinned Python framework matrix

A model's tool call carries its arguments as a JSON string. Sometimes that string is not valid JSON: truncated, an extra brace, single quotes. We fed nine Python agent frameworks the same malformed arguments from a deterministic mock model, at default settings, to see what each one does with the call.

**Result.** On the two core variants (a truncated object and an extra closing brace):

- **3 of 9 ran the tool with arguments other than the intended ones:** Strands, LlamaIndex and smolagents.
- **2 of 9 ended the run without running the tool and without returning an error to the model or in the final text:** LangChain (`create_agent`) and Google ADK (LiteLlm path). Both expose the error in structured fields: `invalid_tool_calls` in LangChain and `MALFORMED_FUNCTION_CALL` in ADK.
- **4 of 9 returned the parse error:** to the model in OpenAI Agents, pydantic-ai and CrewAI, and to the caller in AutoGen.

Our frozen classification reads only text, so it counts **5 of 9** (the first two groups). If structured error fields count as visible, the count is **3 of 9**. The continuation threshold, frozen before the main run, was 3, so the frozen ruling (CONTINUE) holds under both counts. Under the 3-of-9 count it sits exactly at the threshold.

These are pinned versions on one API path with a scripted model. They show what the code does with a malformed call. They do not show how often real models produce one, or what it costs anyone.

## The matrix

Each cell ran twice, and both runs agreed in all 81 framework/scenario pairs (162 cells).

| framework | valid | `{}` | truncated* | extra brace* | single quotes | double-encoded | fenced | truncated, required | empty string† |
|---|---|---|---|---|---|---|---|---|---|
| strands | ran, intended | ran, defaults | ran, other args | ran, other args | ran, other args | error to model | ran, other args | error to model | ran, other args |
| llama-index | ran, intended | ran, defaults | ran, intended | ran, other args | ran, other args | ran, other args | ran, other args | ran, intended | ran, other args |
| smolagents | ran, intended | ran, defaults | ran, other args | ran, other args | ran, other args | ran, other args | ran, other args | ran, other args | ran, other args |
| langchain | ran, intended | ran, defaults | stopped, no text error | stopped, no text error | stopped, no text error | exception | stopped, no text error | stopped, no text error | ran, other args |
| google-adk | ran, intended | ran, defaults | stopped, no text error | stopped, no text error | ran, intended | stopped, no text error | stopped, no text error | stopped, no text error | ran, other args |
| openai-agents | ran, intended | ran, defaults | error to model | error to model | error to model | error to model | error to model | error to model | ran, other args |
| pydantic-ai | ran, intended | ran, defaults | error to model | error to model | error to model | error to model | error to model | error to model | ran, other args |
| crewai | ran, intended | ran, defaults | error to model | error to model | error to model | error to model | error to model | error to model | error to model |
| autogen | ran, intended | ran, defaults | error to caller | error to caller | error to caller | error to caller | error to caller | error to caller | error to caller |

\* Core variants used for the ruling. † Report-only: an empty string ran as `{}` in 7 of 9 frameworks. We report it but do not count it, because treating `""` as `{}` is a defensible convention.

The test tool `list_items(status=None)` has one optional argument: `None` lists all items, and `"archived"` lists archived items. The intended call is always `status="archived"`. "truncated, required" uses `get_weather(city)`, whose only argument is required.

## What each framework did

- **Strands 1.59.0** (`OpenAIModel`, streaming). Strands logs a WARNING under default logging, substitutes `{}` and runs the tool. It returns no error to the model. This fallback is already public: [issue #2051](https://github.com/strands-agents/harness-sdk/issues/2051), with a proposed fix in [pull request #4655](https://github.com/strands-agents/harness-sdk/pull/4655). In this matrix the test tool's only argument is optional, so `{}` is a valid call and the tool ran its broadest action ("all items" instead of "archived"). With a required argument ("truncated, required"), the error reaches the model.
- **LlamaIndex** (core 0.14.25, OpenAI-compatible integration). Truncated objects are repaired, and the tool gets the intended arguments. Extra-brace, single-quote, double-encoded and fenced arguments run the tool with `{}`. Upstream [pull request #16316](https://github.com/run-llama/llama_index/pull/16316) documents a `{}` fallback for JSON that parses but is not an object. That does not establish documented intent for invalid JSON.
- **smolagents 1.26.0** (`ToolCallingAgent` with `OpenAIServerModel`). On the five variants that are not valid JSON, the raw string became the value of the tool's single parameter, with no error. A double-encoded object arrived as the decoded inner string; an empty string ran with the default. We tested single-parameter tools only. The source suggests broader reach to a first parameter, but we did not test multi-parameter tools. The parser is [models.py L193-L200](https://github.com/huggingface/smolagents/blob/v1.26.0/src/smolagents/models.py#L193-L200).
- **LangChain 1.4.4** (`create_agent` with `ChatOpenAI`). The run ends after one model request with empty final text. The error stays in `invalid_tool_calls`. The double-encoded variant raised an exception to the caller.
- **Google ADK 2.11.0** (LiteLlm path, not native Gemini). The run ends with no tool call, and the error is in structured fields. Single quotes are repaired. An opt-in `ReflectAndRetryModelPlugin` exists but is not enabled by default.
- **OpenAI Agents 0.23.1, pydantic-ai-slim 2.55.0, CrewAI 1.15.27.** The parse error goes back to the model. OpenAI Agents and CrewAI advertise strict schemas, and a provider with strict decoding may never emit these inputs. The mock emits them anyway, so this matrix does not compare real-world exposure.
- **AutoGen 0.7.5.** The parse error goes back to the caller.

## How it was run

- Python 3.12.15, Chat Completions, one isolated virtual environment per framework in one container with no network. Versions were pinned on 2026-10-09 and the run executed on 2026-10-10. Full pins are in `source/req-*.txt`.
- The mock's first reply calls the tool with the scenario's raw arguments. Every later reply is `Done.`, whatever the tool returned. So the matrix measures what each framework does with the call and what it sends back. It does not measure model repair or what a user is told.
- `README.md` explains how to rebuild and rerun the grid.

**Evidence status: Artifact checked.** AI agents built and ran this experiment. A separate AI-agent rerun from the same container image, on the same machine, matched all 162 cells on tool invocations, outcomes, model request counts, schemas and returned text. This is not independent scientific reproduction or replication.

## Limits

- We did not measure how often real models produce malformed arguments, or how they repair them.
- We did not establish production effects, user harm, a vulnerability, a safety ranking or demand.
- We tested single-parameter synthetic tools only; multi-parameter tools are untested.
- We tested Python and Chat Completions only. We do not generalize to JavaScript or the Responses API.
- We tested pinned versions and the named provider paths only. Current releases may differ.
- The per-cell data is a derived export. It excludes full request bodies, prompts, framework prompt templates and stderr.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
