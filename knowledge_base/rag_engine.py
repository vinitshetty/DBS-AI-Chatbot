"""
RAG Engine - Retrieval Augmented Generation using LangChain
Handles: Document loading, chunking, retrieval, and response generation
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import hashlib

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document

from knowledge_base.vector_store import VectorStore
from knowledge_base.embeddings import MistralEmbeddings

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Complete RAG (Retrieval Augmented Generation) system
    
    Features:
    - Document ingestion (PDF, TXT)
    - Intelligent text chunking
    - Semantic search and retrieval
    - Context-aware document selection
    """
    
    def __init__(self):
        from config.settings import settings
        
        self.vector_store = VectorStore()
        self.embeddings = MistralEmbeddings()
        self.settings = settings
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Documents directory
        self.documents_path = Path("knowledge_base/documents")
        self.documents_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("RAG Engine initialized")
    
    async def ingest_documents(self, force_reingest: bool = False) -> Dict:
        """
        Ingest all documents from documents folder into vector store
        
        Process:
        1. Find all documents (PDF, TXT)
        2. Load and parse documents
        3. Chunk documents into smaller pieces
        4. Generate embeddings
        5. Store in vector database
        
        Args:
            force_reingest: If True, clear existing data and reingest
            
        Returns:
            Dict with ingestion statistics
        """
        try:
            await self.vector_store.initialize()
            
            # Check if we need to create sample documents
            existing_files = list(self.documents_path.glob("*.txt")) + list(self.documents_path.glob("*.pdf"))
            
            if not existing_files:
                logger.info("No documents found. Creating sample documents...")
                self._create_sample_documents()
                existing_files = list(self.documents_path.glob("*.txt"))
            
            # Find all supported documents
            pdf_files = list(self.documents_path.glob("*.pdf"))
            txt_files = list(self.documents_path.glob("*.txt"))
            all_files = pdf_files + txt_files
            
            logger.info(f"Found {len(all_files)} documents to ingest")
            
            # Process each document
            all_chunks = []
            all_metadatas = []
            all_ids = []
            
            for file_path in all_files:
                logger.info(f"Processing: {file_path.name}")
                
                # Load document
                documents = await self._load_document(file_path)
                
                if not documents:
                    logger.warning(f"No content loaded from {file_path.name}")
                    continue
                
                # Chunk documents
                chunks = self.text_splitter.split_documents(documents)
                logger.info(f"Created {len(chunks)} chunks from {file_path.name}")
                
                # Prepare data for storage
                for i, chunk in enumerate(chunks):
                    chunk_id = self._generate_chunk_id(file_path.name, i)
                    
                    all_chunks.append(chunk.page_content)
                    all_metadatas.append({
                        "source": file_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        **chunk.metadata
                    })
                    all_ids.append(chunk_id)
            
            # Generate embeddings in batch
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            embeddings = self.embeddings.embed_documents(all_chunks)
            
            # Add to vector store
            logger.info("Storing documents in vector database...")
            success = await self.vector_store.add_documents(
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_ids,
                embeddings=embeddings
            )
            
            if success:
                stats = await self.vector_store.get_collection_stats()
                logger.info(f"Ingestion complete: {stats}")
                
                return {
                    "status": "success",
                    "files_processed": len(all_files),
                    "chunks_created": len(all_chunks),
                    "files": [f.name for f in all_files],
                    "collection_stats": stats
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to store documents in vector database"
                }
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        filter_source: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User's question or query
            top_k: Number of documents to retrieve
            filter_source: Optional filter by source file
            
        Returns:
            List of relevant documents with content and metadata
        """
        try:
            if top_k is None:
                top_k = self.settings.RAG_TOP_K
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build metadata filter
            metadata_filter = {}
            if filter_source:
                metadata_filter["source"] = filter_source
            
            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=metadata_filter if metadata_filter else None
            )
            
            # Filter by relevance threshold
            threshold = 1 - self.settings.RAG_SCORE_THRESHOLD
            filtered_results = [
                doc for doc in results
                if doc['distance'] <= threshold
            ]
            
            logger.info(f"Retrieved {len(filtered_results)} relevant documents (from {len(results)} total)")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}", exc_info=True)
            return []
    
    async def _load_document(self, file_path: Path) -> List[Document]:
        """Load document based on file type"""
        try:
            file_extension = file_path.suffix.lower()
            
            if file_extension == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif file_extension == ".txt":
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return []
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {file_path.name}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {str(e)}")
            return []
    
    def _generate_chunk_id(self, filename: str, chunk_index: int) -> str:
        """Generate unique ID for document chunk"""
        content = f"{filename}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _create_sample_documents(self):
        """Create sample documents for demo purposes"""
        logger.info("Creating sample banking documents...")
        
        # Sample FAQ document
        faq_content = """DBS Bank Frequently Asked Questions

Q: What are the branch operating hours?
A: Most DBS branches are open Monday to Friday from 9:30 AM to 4:30 PM, and Saturday from 9:30 AM to 12:30 PM. Branches are closed on Sundays and public holidays. ATMs are available 24/7 for your convenience.

Q: What are the account fees?
A: DBS savings accounts have no fall-below fee if you maintain a minimum balance of SGD 3,000. For accounts below this balance, a monthly fee of SGD 2 applies. Credit card annual fees range from SGD 0 to SGD 642 depending on the card type. Many fees are waived for qualifying customers.

Q: What are the daily transfer limits?
A: For security, daily transfer limits are: SGD 50,000 for transfers to own accounts, SGD 30,000 for transfers to other DBS/POSB accounts, and SGD 20,000 for transfers to other banks. You can request higher limits by visiting a branch with proper identification.

Q: How do I lock my credit card?
A: You can temporarily lock your credit or debit card instantly through the DBS digibank mobile app, online banking, or by calling our 24-hour hotline at 1800-111-1111. Locking your card prevents unauthorized transactions while you search for it. You can unlock it anytime if you find it.

Q: What documents do I need to open an account?
A: To open a personal account, you need: (1) Valid identification (NRIC for Singapore citizens/PRs, passport for foreigners), (2) Proof of residential address (utility bill or bank statement not older than 3 months), (3) Minimum initial deposit of SGD 1,000 for savings accounts.

Q: How do I reset my digibank password?
A: You can reset your digibank password online by clicking "Forgot Password" on the login page. You'll need your username, account number, and ATM card PIN or OTP sent to your registered mobile number."""

        # Sample products document
        products_content = """DBS Banking Products and Services

SAVINGS ACCOUNTS

1. DBS Multiplier Account
- No minimum balance required
- Earn up to 3.5% p.a. on your savings
- Higher interest rates when you credit your salary and spend on your DBS credit card
- Free unlimited GIRO, local fund transfers, and withdrawal transactions

2. DBS Savings Account
- SGD 3,000 minimum balance to waive fall-below fee
- 0.05% p.a. interest on balances
- Access to nationwide ATM network
- Free first 3 withdrawals per month at non-DBS ATMs

CREDIT CARDS

1. DBS Altitude Card
- Annual fee: SGD 196.20 (waived for first year)
- Earn 3 miles per SGD 1 on foreign currency spending
- Complimentary airport lounge access (6 visits per year)
- Travel insurance coverage up to SGD 1 million

2. DBS Live Fresh Card
- Annual fee: SGD 0 (free for life)
- 5% cashback on online shopping and mobile payments
- 5% cashback on food delivery services
- Ideal for young professionals and digital natives

INVESTMENT PRODUCTS

1. DBS Vickers Online Trading
- Trade SGX stocks, ETFs, and bonds
- Commission rates from 0.08%
- Real-time market data and research reports
- Mobile and desktop trading platforms

2. DBS Unit Trusts
- Wide range of funds across asset classes
- Minimum investment from SGD 1,000
- Regular savings plan available from SGD 100 per month
- Access to global fund managers"""

        # Sample policies document
        policies_content = """DBS Bank Policies and Guidelines

ACCOUNT SECURITY POLICY

1. Password Requirements
- Minimum 8 characters with mix of uppercase, lowercase, numbers, and special characters
- Passwords expire every 90 days
- Cannot reuse last 5 passwords
- Maximum 3 failed login attempts before temporary lockout

2. Two-Factor Authentication
- OTP required for all online transactions above SGD 1,000
- SMS or hardware token authentication available
- Biometric authentication (fingerprint/face) available on mobile app

3. Fraud Monitoring
- Real-time transaction monitoring for suspicious activity
- Automatic card lock if fraud detected
- Customer notification via SMS and email for high-value transactions
- Zero liability protection for unauthorized transactions

TRANSACTION POLICIES

1. Fund Transfer Processing Times
- Internal transfers (DBS to DBS): Instant
- FAST transfers to other Singapore banks: Within 10 seconds
- Overseas transfers: 1-3 business days
- Standing instructions: Processed on scheduled date by 11:59 PM

2. Card Usage Limits
- Default daily ATM withdrawal limit: SGD 5,000
- Default daily card spending limit: SGD 20,000
- Limits can be customized through digibank
- Temporary limit increases available for travel"""

        # Write sample documents
        (self.documents_path / "dbs_faqs.txt").write_text(faq_content, encoding='utf-8')
        (self.documents_path / "dbs_products.txt").write_text(products_content, encoding='utf-8')
        (self.documents_path / "dbs_policies.txt").write_text(policies_content, encoding='utf-8')
        
        logger.info("Sample documents created successfully")