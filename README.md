# Document LLM/RAG Service

## Overview

### Design Philosophy

This system is designed as a document-based GPT implementation that provides intelligent answers from a collection of internal documents. The architecture prioritizes precision, transparency, and verifiability by ensuring users receive short, well-sourced answers with direct links to the relevant document sections.

### Key Design Choices

- **Source Attribution**: Every answer includes a direct link to the relevant document and specific paragraph, enabling users to verify information at its source. This design choice prioritizes transparency and trust.

- **Relevance Filtering**: The system is built to recognize when questions fall outside the scope of available documents, explicitly informing users when queries are not applicable to the document collection. This prevents hallucination and maintains accuracy.

- **Dynamic Content Management**: The architecture supports seamless addition of new documents, ensuring the knowledge base can grow and stay current without system redesign.

- **Built-in Guardrails**: Multiple layers of validation prevent inappropriate or irrelevant responses, maintaining system reliability and user trust.

## Base setup

## Example dataset

[PDF files](https://www.kaggle.com/datasets/manisha717/dataset-of-pdf-files)

```bash
curl -L -o ~/Downloads/dataset-of-pdf-files.zip https://www.kaggle.com/api/v1/datasets/download/manisha717/dataset-of-pdf-files
```
