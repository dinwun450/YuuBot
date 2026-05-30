import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd
import requests
import sseclient
import streamlit as st
import weave

from models import (
    ChartEventData,
    DataAgentRunRequest,
    ErrorEventData,
    Message,
    MessageContentItem,
    StatusEventData,
    TableEventData,
    TextContentItem,
    TextDeltaEventData,
    ThinkingDeltaEventData,
    ThinkingEventData,
    ToolResultEventData,
    ToolUseEventData,
)

PAT = "[YOUR PAT HERE]"
HOST = "[YOUR HOST HERE]"
DATABASE = "YUUBOT_DB"
SCHEMA = "GLOBAL"
AGENT = "YUUBOT_CHAT_V121"

wandb_api_key = os.getenv("WANDB_API_KEY")
client = weave.init("yuuchatV121-model-dev")

client.add_cost(
    llm_id="claude-3-5-sonnet", # Must match the 'model' key in your trace
    prompt_token_cost=0.000003,  # Adjusted for your Snowflake credit price
    completion_token_cost=0.000015 
)

@weave.op()
def agent_run_weave(messages: list) -> dict:
    request_body = DataAgentRunRequest(model="claude-4-sonnet", messages=messages)
    resp = requests.post(
        url=f"https://{HOST}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT}:run",
        data=request_body.to_json(),
        headers={
            "Authorization": f"Bearer {PAT}",
            "Content-Type": "application/json",
        },
        stream=True,
        verify=False,
    )

    # Try to parse JSON body; if not JSON, attempt to parse SSE-style payload
    events = []
    body = None
    try:
        body = resp.json()
        # If the body contains an explicit events list, use it
        if isinstance(body, dict) and "events" in body and isinstance(body["events"], list):
            events = body["events"]
    except Exception:
        # Not JSON. Attempt to parse SSE-style text payload into events.
        text = resp.text or ""
        # simple heuristic: treat as SSE if it contains `event:` lines
        if "event:" in text:
            def _parse_sse_text(s: str):
                out = []
                data_lines = []
                event_name = None
                for raw in s.splitlines():
                    line = raw.rstrip("\n")
                    if line == "":
                        if data_lines or event_name is not None:
                            out.append({"event": event_name or "message", "data": "\n".join(data_lines)})
                        data_lines = []
                        event_name = None
                        continue
                    if line.startswith(":"):
                        continue
                    if ":" in line:
                        field, value = line.split(":", 1)
                        value = value.lstrip()
                    else:
                        field, value = line, ""
                    if field == "event":
                        event_name = value
                    elif field == "data":
                        data_lines.append(value)
                if data_lines or event_name is not None:
                    out.append({"event": event_name or "message", "data": "\n".join(data_lines)})
                return out

            events = _parse_sse_text(text)
            body = {"text": text}
        else:
            body = {"text": resp.text}

    return {"status": resp.status_code, "body": body, "events": events, "headers": dict(resp.headers)}


@weave.op()
def analyze_events(events: list) -> dict:
    """Weave-op: summarize events and extract assistant text where possible."""
    counts: dict = {}
    samples: list = []
    assistant_texts: list = []
    tokens = 0

    for ev in events or []:
        name = ev.get("event") if isinstance(ev, dict) else None
        if not name:
            name = "message"
        counts[name] = counts.get(name, 0) + 1
        # keep a small preview
        try:
            data = ev.get("data") if isinstance(ev, dict) else str(ev)
        except Exception:
            data = str(ev)
        if isinstance(data, str):
            samples.append(data[:300])
            # Try to parse assistant message JSON inside data
            # Try to extract structured assistant text. Prefer Message.from_json,
            # but fall back to extracting any `text` fields when parsing fails
            extracted = []
            if isinstance(data, str):
                try:
                    m = Message.from_json(data)
                    extracted.append("\n".join([c.actual_instance.text for c in m.content if getattr(c.actual_instance, 'type', '') == 'text']))
                except Exception as e:
                    # If parsing fails (e.g. server-side validation like "Last message must be from user"),
                    # try to parse JSON and recursively extract `text` fields; otherwise fall back to raw data.
                    try:
                        parsed = json.loads(data)
                    except Exception:
                        if name == "response":
                            extracted.append(data)
                    else:
                        def _extract_texts(obj):
                            texts = []
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    if k == "text" and isinstance(v, str):
                                        texts.append(v)
                                    else:
                                        texts.extend(_extract_texts(v))
                            elif isinstance(obj, list):
                                for it in obj:
                                    texts.extend(_extract_texts(it))
                            return texts

                        extracted.extend([t for t in _extract_texts(parsed) if t])
            # Append any extracted texts
            assistant_texts.extend(extracted)
        
        if name == "response":
            m = Message.from_json(data)
            # extract tokens_consumed from metadata if present
            try:
                meta = getattr(m, "metadata", None)
                if isinstance(meta, str):
                    meta = json.loads(meta)
                if isinstance(meta, dict):
                    usage = meta.get("usage", {})
                    tokens_consumed = usage.get("tokens_consumed")

                    if tokens_consumed:
                        # add the raw tokens_consumed structure to assistant_texts for inspection
                        assistant_texts.append(json.dumps(tokens_consumed))

            except Exception as e:
                # ignore metadata parsing errors
                print("Failed to parse tokens_consumed from metadata ", e)
                pass

            extracted.append("\n".join([c.actual_instance.text for c in m.content if getattr(c.actual_instance, 'type', '') == 'text']))
            tokens += sum(len(t.split()) for t in extracted)
                
    # Build output and token usage summary
    prompt_tokens = sum(len(s.split()) for s in samples)
    completion_tokens = tokens

    return {
        "output": {
            "counts": counts,
            "samples": samples[:10],
            "assistant_texts": assistant_texts[:10],
            "tokens": tokens,
        },
        "model": "claude-3-5-sonnet",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def agent_run() -> requests.Response:
    """Calls the REST API and returns a streaming client."""
    request_body = DataAgentRunRequest(
        model="claude-4-sonnet",
        messages=st.session_state.messages,
    )
    resp = requests.post(
        url=f"https://{HOST}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT}:run",
        data=request_body.to_json(),
        headers={
            "Authorization": f"Bearer {PAT}",
            "Content-Type": "application/json",
        },
        stream=True,
        verify=False,
    )
    if resp.status_code < 400:
        return resp  # type: ignore
    else:
        raise Exception(f"Failed request with status {resp.status_code}: {resp.text}")


def stream_events(response: requests.Response):
    content = st.container()
    # Content index to container section mapping
    content_map = defaultdict(content.empty)
    # Content index to text buffer
    buffers = defaultdict(str)
    spinner = st.spinner("Waiting for response...")
    spinner.__enter__()

    # Some versions of the `sseclient` library expect a URL string and will
    # try to open it with requests (which led to InvalidURL / MissingSchema
    # when we passed non-URL objects). To avoid depending on the library's
    # constructor behavior, parse the Server-Sent Events ourselves from the
    # streaming response.iter_lines(). This yields lightweight objects with
    # `.event` and `.data` which the rest of this function expects.

    class _SSEEvent:
        def __init__(self, event: str | None, data: str):
            self.event = event or "message"
            self.data = data

    def _iter_sse_events(resp: requests.Response):
        data_lines: list[str] = []
        event_name = None

        for raw in resp.iter_lines(decode_unicode=True):
            if raw is None:
                continue
            line = raw.rstrip("\n")
            # blank line -> dispatch event
            if line == "":
                if data_lines or event_name is not None:
                    data = "\n".join(data_lines)
                    yield _SSEEvent(event_name, data)
                data_lines = []
                event_name = None
                continue

            # comments start with ':'
            if line.startswith(":"):
                continue

            if ":" in line:
                field, value = line.split(":", 1)
                value = value.lstrip()
            else:
                field, value = line, ""

            if field == "event":
                event_name = value
            elif field == "data":
                data_lines.append(value)
            # ignore other fields (id, retry)

        # end of stream: flush any pending event
        if data_lines or event_name is not None:
            data = "\n".join(data_lines)
            yield _SSEEvent(event_name, data)

    events = _iter_sse_events(response)
    for event in events:
        match event.event:
            case "response.status":
                spinner.__exit__(None, None, None)
                data = StatusEventData.from_json(event.data)
                spinner = st.spinner(data.message)
                spinner.__enter__()
            case "response.text.delta":
                data = TextDeltaEventData.from_json(event.data)
                buffers[data.content_index] += data.text
                content_map[data.content_index].write(buffers[data.content_index])
            case "response.thinking.delta":
                data = ThinkingDeltaEventData.from_json(event.data)
                buffers[data.content_index] += data.text
                content_map[data.content_index].expander(
                    "Thinking", expanded=True
                ).write(buffers[data.content_index])
            case "response.thinking":
                # Thinking done, close the expander
                data = ThinkingEventData.from_json(event.data)
                content_map[data.content_index].expander("Thinking").write(data.text)
            case "response.tool_use":
                data = ToolUseEventData.from_json(event.data)
                content_map[data.content_index].expander("Tool use").json(data)
            case "response.tool_result":
                try:
                    data = ToolResultEventData.from_json(event.data)
                    content_map[data.content_index].expander("Tool result").json(data)
                except json.JSONDecodeError:
                    # If the event data is not valid JSON, show an error and surface the raw payload
                    st.error("Failed to decode tool result JSON; showing raw data instead.")
                    # Use a safe default container index when parsing failed
                    content_map[0].expander("Tool result (raw)").text(event.data)
                except Exception as e:
                    # Catch other unexpected parsing errors and show raw payload for debugging
                    st.error(f"Error parsing tool result: {e}")
                    content_map[0].expander("Tool result (raw)").text(event.data)
            case "response.chart":
                data = ChartEventData.from_json(event.data)
                spec = json.loads(data.chart_spec)
                content_map[data.content_index].vega_lite_chart(
                    spec,
                    use_container_width=True,
                )
            case "response.table":
                data = TableEventData.from_json(event.data)
                data_array = np.array(data.result_set.data)
                column_names = [
                    col.name for col in data.result_set.result_set_meta_data.row_type
                ]
                content_map[data.content_index].dataframe(
                    pd.DataFrame(data_array, columns=column_names)
                )
            case "error":
                data = ErrorEventData.from_json(event.data)
                st.error(f"Error: {data.message} (code: {data.code})")
                # Remove last user message, so we can retry from last successful response.
                st.session_state.messages.pop()
                return
            case "response":
                try:
                    data = Message.from_json(event.data)
                except json.JSONDecodeError:
                    st.error("Failed to decode response JSON; showing raw text instead.")
                    data = Message(
                        role="assistant",
                        content=[MessageContentItem(TextContentItem(type="text", text=event.data))],
                    )
                except Exception as e:
                    st.error(f"Error parsing response: {e}")
                    data = Message(
                        role="assistant",
                        content=[MessageContentItem(TextContentItem(type="text", text=event.data))],
                    )
                st.session_state.messages.append(data)
    spinner.__exit__(None, None, None)


def process_new_message(prompt: str) -> None:
    message = Message(
        role="user",
        content=[MessageContentItem(TextContentItem(type="text", text=prompt))],
    )
    render_message(message)
    st.session_state.messages.append(message)

    with st.chat_message("assistant"):
        with st.spinner("Sending request..."):
            response = agent_run()

        st.markdown(
            f"```request_id: {response.headers.get('X-Snowflake-Request-Id')}```"
        )
        stream_events(response)

        # After streaming completes, fetch a non-streaming event dump and analyze it.
        try:
            with st.spinner("Analyzing event trace..."):
                # Ensure the last message is from the user when calling non-streaming run,
                # otherwise the API may reject (e.g., "Last message must be from user").
                msgs = list(st.session_state.messages)
                while msgs and getattr(msgs[-1], "role", None) != "user":
                    msgs.pop()
                if not msgs:
                    st.info("No user message available for event fetch; using full history.")
                    resp = agent_run_weave(st.session_state.messages)
                else:
                    resp = agent_run_weave(msgs)
                events = resp.get("events") or []
                print(events)
                summary = analyze_events(events)
        except Exception as e:
            st.sidebar.error(f"Event analysis failed: {e}")
        else:
            with st.sidebar.expander("Last event analysis (auto)", expanded=False):
                out = summary.get("output", {})
                st.write("**Event counts**")
                st.json(out.get("counts", {}))
                st.write("**Sample event data**")
                for s in out.get("samples", []):
                    st.code(s)
                st.write("**Tokens**")
                st.write(out.get("tokens", 0))


def render_message(msg: Message):
    with st.chat_message(msg.role):
        for content_item in msg.content:
            match content_item.actual_instance.type:
                case "text":
                    st.markdown(content_item.actual_instance.text)
                case "chart":
                    spec = json.loads(content_item.actual_instance.chart.chart_spec)
                    st.vega_lite_chart(spec, use_container_width=True)
                case "table":
                    data_array = np.array(
                        content_item.actual_instance.table.result_set.data
                    )
                    column_names = [
                        col.name
                        for col in content_item.actual_instance.table.result_set.result_set_meta_data.row_type
                    ]
                    st.dataframe(pd.DataFrame(data_array, columns=column_names))
                case _:
                    st.expander(content_item.actual_instance.type).json(
                        content_item.actual_instance.to_json()
                    )


st.title("YuuBot Chat v.1.2.1 (BETA)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    render_message(message)

# Sidebar UI: on-demand event trace & analysis using non-streaming Weave op
with st.sidebar.expander("Event trace & analysis", expanded=False):
    if st.button("Fetch events and analyze"):
        with st.spinner("Fetching events..."):
            try:
                resp = agent_run_weave(st.session_state.messages)
            except Exception as e:
                st.error(f"Failed to fetch events: {e}")
            else:
                events = resp.get("events") or []
                if not events:
                    st.info("No events found in non-streaming response; showing body instead.")
                    st.json(resp.get("body"))
                else:
                    summary = analyze_events(events)
                    st.write("**Event counts**")
                    st.json(summary.get("counts"))
                    st.write("**Sample event data**")
                    for s in summary.get("samples", []):
                        st.code(s)
                    st.write("**Extracted assistant texts**")
                    for t in summary.get("assistant_texts", []):
                        st.markdown(t)

if user_input := st.chat_input("What is your question?"):
    process_new_message(prompt=user_input)
