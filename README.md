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

### Local Development

1. Install dependencies:

    ```bash
    uv sync
    ```

2. Start the service:

    ```bash
    uv run python server.py
    ```

### Docker Compose (Recommended for Production)

The service can be run using Docker Compose, which includes all required dependencies:

1. **Prerequisites**: Ensure you have Docker and Docker Compose installed on your system.

2. **Environment Setup**: Create a `.env` file in the project root with your OpenAI API key:

    ```bash
    echo "OPEN_AI_KEY=your-openai-api-key-here" > .env
    ```

3. **Build and Run**: Start all services using Docker Compose:

    ```bash
    docker compose -f doc-service.compose.yaml up --build
    ```

    This will start:

    - **Document Service** (port 8000): The main FastAPI application
    - **Qdrant** (port 6333): Vector database for document embeddings
    - **MinIO** (port 9000): Object storage for document files

4. **Access the Service**: The API will be available at `http://localhost:8000`

5. **Stop the Services**:

    ```bash
    docker compose -f doc-service.compose.yaml down
    ```

6. **Clean Up** (removes volumes and data):

    ```bash
    docker compose -f doc-service.compose.yaml down -v
    ```

### Environment Variables

When running with Docker Compose, the following environment variables are automatically configured:

- `MINIO_HOST=minio`
- `MINIO_PORT=9000`
- `MINIO_ACCESS_KEY=drm-document-service`
- `MINIO_SECRET_KEY=drm-document-service-secret-key`
- `QDRANT_HOST=qdrant`
- `QDRANT_PORT=6333`
- `SERVICE_PORT=8000`
- `SERVICE_HOST=0.0.0.0`

You only need to provide your `OPEN_AI_KEY` in the `.env` file.

## Architecture Overview

### Processing Steps

1. **Query Reception**: FastAPI endpoint receives the user's question via `/query`
2. **Pipeline Orchestration**: DocumentPipeline initializes and coordinates the multi-agent workflow
3. **Safety Validation**: GuardrailAgent validates the query for appropriateness and safety
4. **Document Retrieval**: RetrievalAgent performs semantic search to find relevant document parts
5. **Embedding Generation**: EmbeddingsService converts the query into a vector using OpenAI's embedding model
6. **Similarity Search**: EmbeddingsRepository searches Qdrant vector database for semantically similar content
7. **Answer Synthesis**: OrchestratorAgent combines retrieved context with LLM reasoning to generate the final answer
8. **Response Delivery**: Structured response includes the answer, sources, confidence score, and relevance flags

### Key Components

- **🎭 Agent Layer**: Pydantic-AI agents that handle orchestration, safety, and retrieval
- **🧠 Logic Layer**: Business logic services for embeddings and document processing
- **💾 Storage Layer**: Repositories managing Qdrant vector database and MinIO object storage
- **🏗️ Infrastructure**: External services (OpenAI, Qdrant, MinIO) supporting the RAG pipeline

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

### Examples

```bash
# Complete workflow example
uv run python cli.py upload -f ~/documents/manual.pdf
uv run python cli.py list-docs
uv run python cli.py query -q "How do I configure the system?"
```
