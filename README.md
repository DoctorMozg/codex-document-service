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

2. Create environment file:

    ```bash
    cp .env.example .env
    ```

    Then edit `.env` to add your OpenAI API key and other required variables.

3. Start the service:

    ```bash
    uv run uvicorn drm_document_service.app:app --host 127.0.0.1 --port 8000 --reload
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

    - **doc-service-backend** (port 8000): The main FastAPI application
    - **qdrant** (ports 6333, 6334): Vector database for document embeddings
    - **minio** (port 9000): Object storage for document files
    - **minio console** (port 9001): MinIO web console for storage management

4. **Access the Service**:
    - **API**: `http://localhost:8000`
    - **MinIO Console**: `http://localhost:9001` (admin interface for file storage)

5. **Stop the Services**:

    ```bash
    docker compose -f doc-service.compose.yaml down
    ```

6. **Clean Up** (removes volumes and data):

    ```bash
    docker compose -f doc-service.compose.yaml down -v
    ```

#### Docker Compose Architecture

The Docker Compose setup creates:

- **Network**: `doc-service-network` (bridge driver) for inter-service communication
- **Volumes**:
  - `minio_data`: Persistent storage for uploaded documents
  - `qdrant_data`: Persistent storage for vector embeddings
- **Services**: All services run on the same network and can communicate using service names

### Environment Variables

The service can be configured using the following environment variables:

#### Required Variables

- `OPEN_AI_KEY`: Your OpenAI API key for LLM and embedding services
- `MINIO_ACCESS_KEY`: MinIO access key for object storage
- `MINIO_SECRET_KEY`: MinIO secret key for object storage

#### Service Configuration

- `LOG_LEVEL`: Logging level (default: `DEBUG`)
- `SERVICE_HOST`: Service host address (default: `127.0.0.1`)
- `SERVICE_PORT`: Service port (default: `8000`)

#### Storage Configuration

- `MINIO_HOST`: MinIO server host (default: `minio`)
- `MINIO_PORT`: MinIO server port (default: `9000`)
- `QDRANT_HOST`: Qdrant vector database host (default: `qdrant`)
- `QDRANT_PORT`: Qdrant vector database port (default: `6333`, Docker Compose uses `6334`)

#### RAG Configuration

- `MAX_RETRIEVAL_RESULTS`: Maximum number of document chunks to retrieve (default: `5`)
- `MAX_DOCUMENT_TEXT_LENGTH`: Maximum length of document text for processing (default: `3000`)

#### Docker Compose Setup

When running with Docker Compose, most variables are automatically configured:

```env
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_ACCESS_KEY=drm-document-service
MINIO_SECRET_KEY=drm-document-service-secret-key
QDRANT_HOST=qdrant
QDRANT_PORT=6334
SERVICE_PORT=8000
SERVICE_HOST=0.0.0.0
SERVICE_DEBUG=true
LOG_LEVEL=DEBUG
```

**Note**: The Qdrant service exposes both ports 6333 and 6334, but the application is configured to use port 6334.

**MinIO Credentials**: The MinIO service uses `MINIO_ROOT_USER=drm-document-service` and `MINIO_ROOT_PASSWORD=drm-document-service-secret-key` internally, which map to the application's `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` environment variables.

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

The service includes a beautiful CLI tool built with Rich formatting for working with all endpoints. The CLI provides comprehensive document management and querying capabilities.

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
# Upload a single PDF document
uv run python cli.py upload --file /path/to/document.pdf
uv run python cli.py upload -f /path/to/document.pdf

# Upload all PDFs from a folder
uv run python cli.py upload --folder /path/to/folder
uv run python cli.py upload -d /path/to/folder

# Upload PDFs recursively from folder and subfolders
uv run python cli.py upload --folder /path/to/folder --recursive
uv run python cli.py upload -d /path/to/folder -r

# List all documents
uv run python cli.py list-docs

# Get detailed document information
uv run python cli.py info <document-id>

# Download a document
uv run python cli.py download <document-id> --output downloaded.pdf
uv run python cli.py download <document-id> -o downloaded.pdf

# Delete a document (with confirmation prompt)
uv run python cli.py delete <document-id>

# Delete a document (skip confirmation)
uv run python cli.py delete <document-id> --yes
uv run python cli.py delete <document-id> -y
```

#### Query Documents (RAG)

```bash
# Ask a question about your documents
uv run python cli.py query --question "What is the main topic of the documents?"
uv run python cli.py query -q "What is the main topic of the documents?"

# Interactive query (prompts for question)
uv run python cli.py query
```

### Examples

```bash
# Complete workflow example
uv run python cli.py upload -f ~/documents/manual.pdf
uv run python cli.py list-docs
uv run python cli.py query -q "How do I configure the system?"

# Batch upload example
uv run python cli.py upload -d ~/documents -r
uv run python cli.py query -q "What are the main features?"
```
