# ARVA: Animal Rescue Volunteer Assistant

## Overview
ARVA is an interactive assistant designed to support volunteers at animal welfare organizations. It allows volunteers to:

- Store and retrieve case details, including expenses and treatments.
- Search for cases within a date range using natural language queries.
- Generate comprehensive case reports for specified date ranges.

## RAG-based Architecture & Phase 1 Implementation
This phase leverages a Retrieval-Augmented Generation (RAG) architecture: the system retrieves relevant document chunks from the vector database based on the user’s query and selected date range, then augments the LLM’s prompt with this context to generate accurate, grounded responses.

Although structured metadata (e.g., dates, animal type, clinic names) could be filtered via a traditional relational database, we use a vector database to enable **semantic search** across free-text case summaries and expense notes. This ensures volunteers can find relevant information even if their query wording doesn’t exactly match stored fields.

In Phase 1, we've implemented the core search functionality using a vector database and an LLM:

### Phase 1: Implementation Steps

1. **Loading and Splitting the Data**
   - **Technique**: `RecursiveCharacterTextSplitter`
   - **Purpose**: Splits long case documents into semantically coherent chunks, ensuring each chunk stays within token limits while preserving context boundaries for more accurate retrieval.

2. **Loading the Embedding Model**
   - **Technique**: `all-MiniLM-L6-v2`
   - **Purpose**: Provides a lightweight, high-performance sentence transformer to generate 384-dimensional embeddings, balancing speed and semantic fidelity for real-time queries.

3. **Storing Embeddings in VectorDB**
   - **Technique**: Direct use of the `chromadb` library
   - **Purpose**: Offers native upsert/update operations and persistent storage for evolving case data—functionality not available in LangChain’s built‑in vector stores—preparing for future CRUD in Phase 2.

4. **Setting Up the Retriever**
   - **Technique**: **Hybrid Retriever** (Semantic + Metadata Filter)
   - **Purpose**: Combines metadata filters (animal type, date range, etc.) with semantic similarity search over case summaries, ensuring precise, contextually relevant results even when volunteer queries vary in wording.


1. **Data Preparation**
   - Split case documents into manageable chunks.
   - Generate embeddings for each chunk and store them with metadata (date, case ID, animal type, etc.) in a vector database.

2. **Interactive Search**
   - Volunteers select a date range and enter a natural language query (e.g., “taken to Blue Paw Clinic”).
   - The system encodes the query and applies a metadata filter based on the date range and other structured fields.
   - Relevant document chunks are retrieved from the vector DB via semantic similarity.
   - The retrieved chunks and the original query are sent to the LLM.
   - The LLM’s response, along with the source documents, is returned to the volunteer.

## Next Phases

- **Phase 2: Full CRUD & Hybrid Storage**
  - Volunteers will be able to add new cases, record expenses, and update existing case details at any time.
  - Case and expense records will be stored in a **relational database** for transactional integrity and straightforward reporting.
  - Summarized case narratives and expense summaries will be generated and stored as embeddings in the **vector database** to support ongoing semantic search and context-aware retrieval.

- **Phase 3: Case Report Generation & Export**
  - Implement dynamic report generation (PDF/CSV) combining relational data and semantic insights.

- **Phase 4: Access Control & Notifications**
  - Add user authentication with role-based permissions.
  - Implement real-time notifications for case updates and pending tasks.

## Getting Started

### Prerequisites
- Python 3.x
- An OpenAI API key (or other compatible embedding/LLM service credentials)
- Access to a vector database (e.g., Pinecone, Weaviate, or Chroma)
- A relational database (e.g., PostgreSQL, MySQL)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/arva.git
cd arva

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`.
2. Set your API keys and database credentials in `.env`:

```
OPENAI_API_KEY=your-openai-api-key
VECTOR_DB_API_KEY=your-vector-db-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### Running the App

```bash
python main.py
```

- Open the web UI at `http://localhost:8000`.
- Use the date picker to select a range and enter your query in the search bar.




