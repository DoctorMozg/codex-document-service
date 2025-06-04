# Document LLM/RAG Service

## Overview

### Design Philosophy

This system is designed as a document-based GPT implementation that provides intelligent answers from a collection of internal documents. The architecture prioritizes precision, transparency, and verifiability by ensuring users receive short, well-sourced answers with direct links to the relevant document sections.

### Key Design Choices

- **Source Attribution**: Every answer includes a direct link to the relevant document and specific paragraph, enabling users to verify information at its source. This design choice prioritizes transparency and trust.

- **Relevance Filtering**: The system is built to recognize when questions fall outside the scope of available documents, explicitly informing users when queries are not applicable to the document collection. This prevents hallucination and maintains accuracy.

- **Dynamic Content Management**: The architecture supports seamless addition of new documents, ensuring the knowledge base can grow and stay current without system redesign.

- **Built-in Guardrails**: Multiple layers of validation prevent inappropriate or irrelevant responses, maintaining system reliability and user trust.

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Start the service:

```bash
uv run python server.py
```

## CLI Usage

The service includes a beautiful and interactive CLI tool for working with all endpoints. The CLI provides both command-line and interactive modes.

### Installation

The CLI dependencies are already included in the project. After running `uv sync`, you can use the CLI immediately.

### Basic Usage

```bash
# Use default server (http://localhost:8000)
uv run python cli.py --help

# Specify custom server URL
uv run python cli.py --server https://your-server.com --help
```

### Available Commands

#### Health Check

```bash
uv run python cli.py health
```

#### Document Management

```bash
# Upload a PDF document
uv run python cli.py upload --file /path/to/document.pdf

# List all documents
uv run python cli.py list-docs

# Get document information
uv run python cli.py info <document-id>

# Download a document
uv run python cli.py download <document-id> --output downloaded.pdf

# Delete a document
uv run python cli.py delete <document-id>
```

#### Query Documents (RAG)

```bash
# Ask a question about your documents
uv run python cli.py query --question "What is the main topic of the documents?"

# Interactive query (prompts for question)
uv run python cli.py query
```

### Interactive Mode

For a more user-friendly experience, use the interactive mode:

```bash
uv run python cli.py interactive
```

In interactive mode, you can:

- Type commands without the full CLI syntax
- Get help with `help`
- Execute commands like `health`, `query`, `upload`, `list`, etc.
- Exit with `exit` or Ctrl+C

### CLI Features

- **Beautiful Output**: Rich formatting with colors, tables, and panels
- **Progress Indicators**: Visual feedback for long-running operations
- **Interactive Prompts**: Guided input for required parameters
- **Error Handling**: Clear error messages with context
- **File Validation**: Automatic PDF validation and size checks
- **Confirmation Prompts**: Safety checks for destructive operations

### Examples

```bash
# Complete workflow example
uv run python cli.py upload -f ~/documents/manual.pdf
uv run python cli.py list-docs
uv run python cli.py query -q "How do I configure the system?"
```

## Example Dataset

[PDF files](https://www.kaggle.com/datasets/manisha717/dataset-of-pdf-files)

```bash
curl -L -o ~/Downloads/dataset-of-pdf-files.zip https://www.kaggle.com/api/v1/datasets/download/manisha717/dataset-of-pdf-files
```
