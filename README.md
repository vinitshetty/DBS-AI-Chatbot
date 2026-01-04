Project Structure:
dbs-chatbot/
├── main.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configuration management
├── frontend/
│   └── index.html                   # React-based UI
├── api_gateway/
│   ├── __init__.py
│   ├── gateway.py                   # API Gateway with rate limiting
│   └── middleware.py                # Auth, CORS, logging middleware
├── orchestration/
│   ├── __init__.py
│   ├── conversation_manager.py      # Session & context management
│   ├── intent_router.py             # Intent classification & routing
│   └── response_generator.py        # Response composition
├── llm_core/
│   ├── __init__.py
│   ├── mistral_client.py            # Mistral API integration
│   └── prompts.py                   # System prompts & templates
├── knowledge_base/
│   ├── __init__.py
│   ├── vector_store.py              # ChromaDB integration
│   ├── rag_engine.py                # LangChain RAG workflow
│   ├── embeddings.py                # Embedding generation
│   └── documents/                   # Sample PDFs for ingestion
│       ├── dbs_products.pdf
│       ├── dbs_policies.pdf
│       └── dbs_faqs.pdf
├── transaction_engine/
│   ├── __init__.py
│   ├── workflow_engine.py           # State machine for transactions
│   ├── validators.py                # Business rule validation
│   └── core_banking_client.py       # Mock/Real banking API client
├── security/
│   ├── __init__.py
│   ├── auth_service.py              # Authentication & sessions
│   ├── fraud_detector.py            # Anomaly detection
│   └── audit_logger.py              # Compliance logging
└── tests/
    ├── test_intent_routing.py
    ├── test_rag.py
    └── test_transactions.py