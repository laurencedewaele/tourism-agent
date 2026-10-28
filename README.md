# Tourism Agent

A conversational LangGraph agent that helps customers find a stay in a catalogue:
it understands their wishes expressed in natural language, searches for matching stays
and makes a reasoned proposal.

## Features

- **Preference analysis** (`analyze_preferences`): using structured output, the LLM extracts
  an opinion (wanted / to avoid / not mentioned) and a short justification for each stay
  type: beach, countryside, mountains, city, sport, relaxation, accessibility for people
  with disabilities or reduced mobility. It also records, as free text, the period or
  months the client has in mind for the stay (`travel_period`).
- **Multi-turn conversation**: criteria already identified are sent to the LLM with each
  new message, which enriches or corrects them instead of starting from scratch.
- **Request for details** (`ask_for_details`): if no positive preference is detected,
  the agent lists the available stay types (static answer, no LLM call).
- **Catalogue filtering** (`filter_matching_stays`): deterministic search (no LLM) in
  `data/data.json`, with a score per stay (`2/3`…) and a match level
  (`parfait` = full / `partiel` = partial), sorted by relevance.
- **Stay proposal** (`respond_with_proposal`): the LLM writes the answer based on the
  conversation, the criteria and the selected stays. When the client has given a period,
  the LLM can call the `check_stays_availability` tool (months available per stay, from
  `data/dispo.json`), then says whether the stay is available, suggests other matching
  stays that are available, or states that no availability information exists yet.
  Today's date is added to the prompt so the LLM can interpret the requested period.
- **Tool execution** (`tools`): a LangGraph `ToolNode` runs the tool calls requested by
  `respond_with_proposal`, then the flow goes back to it to write the answer. Only one
  tool round is allowed per turn: on the second pass the tools are bound with
  `tool_choice="none"`, and if the model still requests a tool, a fallback answer is
  used instead (no infinite loop). Tool calls and results stay in the message history.
- **Input check** (`reject_input`): invalid messages are rejected before any LLM call
  (see [Safeguards](#safeguards)).
- **Configurable model**: the model name is read from `MODEL_NAME` and can be overridden
  per run through the context (`context={"model_name": ...}`), with a dedicated system
  prompt per model. Models are called through OpenRouter.

## Graph

```mermaid
flowchart TD
    START([START]) -->|valid_input| analyze_preferences
    START -->|invalid_input| reject_input
    analyze_preferences -->|criteria_detected| filter_matching_stays
    analyze_preferences -->|need_details| ask_for_details
    filter_matching_stays --> respond_with_proposal
    respond_with_proposal -->|tool call| tools
    tools --> respond_with_proposal
    respond_with_proposal -->|final answer| END([END])
    ask_for_details --> END
    reject_input --> END
```

## Repository architecture

```
src/tourism_agent/
├── graph.py                                Builds and compiles the LangGraph graph
├── llm.py                                  Initialises the chat models and lists the handled LLM errors
├── exceptions.py                           Defines the agent errors (configuration, catalogue)
├── utils.py                                Displays the state and the message history
├── conditions/
│   ├── input_condition.py                  Routes the flow according to the validity of the incoming message
│   └── staytype_condition.py               Routes the flow according to the identified criteria
├── schemas/
│   ├── context.py                          Defines the run context (model name)
│   ├── criteria.py                         Defines the stay types and the criteria models
│   └── state.py                            Defines the graph state (messages, criteria, matching stays, travel period)
├── nodes/
│   ├── reject_input_node.py                Rejects an invalid message and removes it from the history
│   ├── analyze_preferences_node.py         Analyses and merges the preferences
│   ├── ask_for_details_node.py             Asks for more details
│   ├── filter_matching_stays_node.py       Filters the catalogue according to the criteria (no LLM)
│   ├── respond_with_proposal_node.py       Writes the answer with the proposed stays
│   ├── proposal_tools_node.py              Runs the tools requested by the proposal (ToolNode)
│   └── respond_with_confirmation_node.py   Confirms the detected preferences (not used in the graph)
├── services/
│   ├── input_validation.py                 Checks the user message before any LLM call
│   ├── filter_matching_stays.py            Loads the catalogue and selects the matching stays
│   └── availability.py                     Loads the availabilities and gives the available months per stay
├── tools/
│   └── availability_tool.py                Availability tool the LLM can call when proposing stays
├── data/
│   ├── data.json                           Stay catalogue
│   └── dispo.json                          Available months per stay (YYYYMM format)
└── prompts/
    └── prompts.py                          Contains the system prompts per model

tests/
├── unit_tests/                             Unit tests (no network call)
└── integration_tests/                      Integration tests (real LLM calls)
```

## Safeguards

### Input validation

A conditional edge at the graph entry (`conditions/input_condition.py`,
`services/input_validation.py`) only routes valid messages to the LLM. The following are rejected:

- no message at all;
- a last message that is not a user message (forged system or AI message,
  to limit prompt injection);
- a message longer than 300 characters.

The `reject_input` node answers with an explicit message and **removes the rejected
message from the history**, so that it is not sent back to the LLM in later turns. The
justification produced by the LLM is also limited to 100 characters by the schema.

### Exception handling

- **Dedicated exceptions** (`exceptions.py`): `TourismAgentError`, from which
  `ConfigurationError` and `CatalogError` derive.
- **Configuration errors** (missing prompt for the model, missing environment variable):
  not caught, the agent fails immediately with an explicit message.
- **LLM errors** (`llm.py`): 3 automatic retries and a 60 s timeout per request.
  Expected errors (network, quota, model refusal, structured output not matching the
  schema) are grouped in `LLM_ERRORS` and handled in **degraded mode**:
  - preference analysis: the known criteria are kept (or, failing that, the agent asks
    for more details);
  - proposal: a fallback answer, built without the LLM, lists the stays found.
- **Catalogue**: missing file or invalid JSON → `CatalogError`, caught by the filtering
  node, which continues without any stay; malformed entries are skipped and logged.
- **Availabilities**: missing file or invalid JSON in `dispo.json` → `CatalogError`;
  malformed entries and months not in `YYYYMM` format are skipped and logged. A tool
  failure (`CatalogError` or invalid tool arguments) is sent back to the model as an
  error `ToolMessage` ("Vérification impossible pour le moment."), and the model still
  writes its proposal, stating that availability could not be checked.

## Automated tests

Unit tests (`tests/unit_tests`, no network call: the model is mocked):

- `test_configuration.py`: graph compilation.
- `test_criteria.py`: stay type labels.
- `test_prompts.py`: prompts exist for the configured model.
- `test_input_validation.py`: valid messages, length limit, non-user message,
  no message, removal of the rejected message, justification length.
- `test_error_handling.py`: model without prompt, routing without criteria, missing /
  invalid / partially malformed catalogue, failing LLM (criteria kept, fallback answer).
- `test_availability.py`: loading `dispo.json` (missing file, invalid JSON, malformed
  entries and months), readable months and unknown stays, the path through the `tools`
  node with messages kept in the history, tool failure reported to the model, and the
  one-tool-round-per-turn guard.

Integration tests (`tests/integration_tests`, actually call the LLM):

- `test_graph.py`: criteria enrichment over two conversation turns; travel period
  extraction and availability check (a sporty mountain stay in July 2027 leads to the
  available Lozère stay).

Run the tests with pytest:

```bash
uv run pytest tests/unit_tests          # unit tests
uv run pytest tests/integration_tests   # integration tests (requires OPENROUTER_API_KEY and MODEL_NAME)
uv run pytest                           # all tests
```

## Quickstart

1. Install the dependencies with `uv`:

```bash
uv sync --dev
```

2. Configure the environment (`OPENROUTER_API_KEY`, `MODEL_NAME`, and optionally
   `LANGSMITH_API_KEY` for tracing):

```bash
cp .env.example .env
```

3. Run locally:

```bash
uv run langgraph dev --studio-url https://eu.api.smith.langchain.com
```

## Deploying to LangSmith Studio

1. Push the project to a Git repository.
2. In LangSmith, create a new Deployment from this repository.
3. Set the environment variables (`OPENROUTER_API_KEY`, `MODEL_NAME`, optionally `LANGSMITH_API_KEY`).
4. Deploy using the `langgraph.json` configuration (`tourism_agent` graph).

## Reference docs

- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- LangChain deployment: https://docs.langchain.com/oss/python/langchain/deploy
