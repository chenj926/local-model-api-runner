# Local Model API Runner

A small local pipeline for running prompts against OpenAI-compatible chat APIs. It reads your API key from `.env`, loads a prompt from `prompt.txt`, attaches readable files from `inputs/`, and saves each response in `outputs/`.

## Project Structure

```text
.
|-- api_call.py          # Run one model call
|-- switch_model.py      # Show, list, or switch the default model
|-- prompt.txt           # Write your prompt here
|-- model_config.json    # Model profiles and API key env matching
|-- .env.example         # Example local env file
|-- data/                # Optional source/reference files
|-- inputs/              # Drop files here to attach them to the call
|-- outputs/             # Generated responses
`-- llm_pipeline/        # Pipeline implementation
```

## Setup

Use Python 3.10 or newer.

Create your private `.env` file:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
DEEP_SEEK_API_KEY=your_real_api_key_here
```

The repo ignores `.env`, so your key will not be committed.

## Basic Usage

Write your prompt in `prompt.txt`.

Optionally copy text files, Markdown, JSON, JSONL, CSV, code files, or PDFs into `inputs/`. Text-like files are included automatically. PDFs are supported if `pypdf` is installed:

```powershell
pip install pypdf
```

Run the pipeline:

```powershell
python .\api_call.py
```

By default, every run starts a new chat. This matches opening a new conversation in a web UI.

Continue from the latest saved chat:

```powershell
python .\api_call.py --continue-last
```

Continue from a specific saved chat:

```powershell
python .\api_call.py --continue-from outputs\20260530_012511_deepseek-v4-pro.json
```

You can update `prompt.txt` and change files in `inputs/` before continuing. The new prompt and attachments become the next user turn, while the previous conversation is sent as context.

The script prints the answer and saves two files in `outputs/`:

- `.md`: human-readable response with metadata, token usage, reasoning content when returned, and the original prompt
- `.json`: raw API response plus request/conversation history for continuation, debugging, exact usage details, or later processing

Markdown is the default reading format because it is easy to open, search, copy, and archive. Keeping the raw JSON beside it is useful when you need provider metadata or exact response details.

## Switch Models

List configured models:

```powershell
python .\switch_model.py list
```

Show the current default:

```powershell
python .\switch_model.py show
```

Set non-thinking mode:

```powershell
python .\switch_model.py set deepseek-v4-pro-nonthinking
```

Set thinking mode back:

```powershell
python .\switch_model.py set deepseek-v4-pro
```

Choose a model for one run without changing the default:

```powershell
python .\api_call.py --model deepseek-v4-pro-nonthinking
```

## DeepSeek Thinking Mode

The default profile is `deepseek-v4-pro`:

- Provider model: `deepseek-v4-pro`
- Thinking: `enabled`
- Reasoning effort: `max`
- Max tokens: provider default

Add `max_tokens` to a model profile in `model_config.json` only when you want to explicitly cap generated output. Without it, the request uses the provider default; your full request still has to fit inside the provider context window.

DeepSeek chat completions are stateless: the server does not remember earlier turns. This runner handles continuation locally by loading a previous output JSON and sending its saved conversation history with your new prompt.

## GitHub Safety

Generated outputs, private inputs, local data files, and `.env` are ignored by default. The tracked folders keep only `.gitkeep` placeholders so the structure is preserved.
