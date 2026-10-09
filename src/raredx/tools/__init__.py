"""The tools the agent calls.

Each tool is one function with typed, described inputs and a typed output: the
descriptions are what a model reads to decide when and how to call it. Each is
tested on its own and traced in MLflow as a TOOL span, so a recorded answer
shows every tool call made for it.
"""
