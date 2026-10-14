"""The agent as a service: an HTTP API around the system that was evaluated.

schemas.py    what a request and an answer look like — the API's contract
watch.py      an agent's model calls and tool calls, relayed as they happen
steps.py      those events in words, for a person watching
diagnoser.py  one request: the evaluated agent, or the no-model ranking when
              the model cannot be reached
app.py        the HTTP layer (FastAPI): routes, limits, the event stream
client.py     a typed client, for the demo page and for scripts
demo.py       the demo page (Streamlit), one client of the API among others
"""
