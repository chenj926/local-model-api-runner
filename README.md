# Local Model API Runner

A small local pipeline for running prompts against OpenAI-compatible chat APIs. It reads your API key from `.env`, loads a prompt from `prompt.txt`, attaches readable files from `inputs/`, and saves each response in `outputs/`.

## Project Structure

```text
.
├── api_call.py          # Run one model call
├── switch_model.py      # Show, list, or switch the default model
├── prompt.txt           # Write your prompt here
├── model_config.json    # Model profiles and API key env matching
├── .env.example         # Example local env file
├── data/                # Optional source/reference files
├── inputs/              # Drop files here to attach them to the call
├── outputs/             # Generated responses
└── llm_pipeline/        # Pipeline implementation
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

Optionally copy text files, Markdown, JSON, CSV, code files, or PDFs into `inputs/`. Text-like files are included automatically. PDFs are supported if `pypdf` is installed:

```powershell
pip install pypdf
```

Run the pipeline:

```powershell
python .\api_call.py
```

The script prints the answer and saves two files in `outputs/`:

- `.md`: human-readable response with metadata and the original prompt
- `.json`: raw API response for debugging or later processing

Markdown is the default reading format because it is easy to open, search, copy, and archive. Keeping the raw JSON beside it is useful when you need token usage, provider metadata, or exact response details.

## Switch Models

List configured models:

```powershell
python .\switch_model.py list
```

Show the current default:

```powershell
python .\switch_model.py show
```

Set a new default:

```powershell
python .\switch_model.py set deepseek-reasoner
```

You can also choose a model for one run without changing the default:

```powershell
python .\api_call.py --model deepseek-reasoner
```

## DeepSeek Model Override

The default profile is named `deepseek-v4-pro`, and it uses the provider model value from `model_config.json`.

If your DeepSeek account expects a different model string, add this to `.env`:

```env
DEEP_SEEK_MODEL=deepseek-chat
```

## GitHub Safety

Generated outputs, private inputs, local data files, and `.env` are ignored by default. The tracked folders keep only `.gitkeep` placeholders so the structure is preserved.
