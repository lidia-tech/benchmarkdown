# benchmarkdown

Benchmark for text extracion from documents to Markdown format

## Project structure

- `/benchmarkdown` - Core package containing reusable extraction code
- `/data` -  Directory for project data (not versioned)
- `/notebooks` - Jupyter notebooks with examples and demos

## Installation and usage

Create a copy of `.env.template` as `.env` and fill out your credentials.

### uv (recommended)

1. [Get uv](https://github.com/astral-sh/uv).
2. `uv venv && uv sync --all-extras --all-groups`
3. Open the notebooks and set the kernel to the newly created `.venv/bin/python` interpreter.
4. Follow on the notebook for test and demo usage.

### Manual venv (deprecated)

```sh
$ python -venv .venv
$ source .venv/bin/activate
(.venv) $ pip install . -e
```
Open the notebooks and set the kernel to the newly created `.venv` virtual environment.
