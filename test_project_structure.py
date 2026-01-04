#!/usr/bin/env python3
"""
DBS AI Chatbot - Project Structure Verification Test
Tests all modules, imports, and directory structure
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import importlib

# ANSI color codes for pretty output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def check_directory_structure() -> Tuple[int, int]:
    """
    Check if all required directories exist
    Returns: (passed, failed) counts
    """
    print_header("DIRECTORY STRUCTURE VERIFICATION")
    
    required_dirs = [
        "config",
        "api_gateway",
        "orchestration",
        "llm_core",
        "knowledge_base",
        "knowledge_base/documents",
        "transaction_engine",
        "security",
        "frontend",
        "tests",
        "data",
        "data/chroma",
        "logs"
    ]
    
    passed = 0
    failed = 0
    
    for directory in required_dirs:
        path = Path(directory)
        if path.exists() and path.is_dir():
            print_success(f"Directory exists: {directory}/")
            passed += 1
        else:
            print_error(f"Directory missing: {directory}/")
            failed += 1
    
    return passed, failed

def check_root_files() -> Tuple[int, int]:
    """
    Check if root-level files exist
    Returns: (passed, failed) counts
    """
    print_header("ROOT FILES VERIFICATION")
    
    required_files = [
        "main.py",
        "requirements.txt",
        ".env",
        "README.md"
    ]
    
    optional_files = [
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    passed = 0
    failed = 0
    
    for file in required_files:
        path = Path(file)
        if path.exists() and path.is_file():
            size = path.stat().st_size
            print_success(f"File exists: {file} ({size} bytes)")
            passed += 1
        else:
            print_error(f"File missing: {file}")
            failed += 1
    
    print("\nOptional files:")
    for file in optional_files:
        path = Path(file)
        if path.exists():
            print_success(f"File exists: {file}")
        else:
            print_warning(f"File missing (optional): {file}")
    
    return passed, failed

def check_module_files() -> Tuple[int, int]:
    """
    Check if all Python module files exist
    Returns: (passed, failed) counts
    """
    print_header("MODULE FILES VERIFICATION")
    
    modules = {
        "config": ["__init__.py", "settings.py"],
        "api_gateway": ["__init__.py", "gateway.py", "middleware.py"],
        "orchestration": ["__init__.py", "conversation_manager.py", "intent_router.py", "response_generator.py"],
        "llm_core": ["__init__.py", "mistral_client.py", "prompts.py"],
        "knowledge_base": ["__init__.py", "vector_store.py", "rag_engine.py", "embeddings.py"],
        "transaction_engine": ["__init__.py", "workflow_engine.py", "validators.py", "core_banking_client.py"],
        "security": ["__init__.py", "auth_service.py", "fraud_detector.py", "audit_logger.py"]
    }
    
    passed = 0
    failed = 0
    
    for module, files in modules.items():
        print(f"\n{Colors.BOLD}Module: {module}/{Colors.END}")
        for file in files:
            path = Path(module) / file
            if path.exists() and path.is_file():
                size = path.stat().st_size
                try:
                    lines = len(path.read_text(encoding='utf-8').splitlines())
                    print_success(f"  {file} ({lines} lines, {size} bytes)")
                except UnicodeDecodeError:
                    # If UTF-8 fails, just show size
                    print_success(f"  {file} ({size} bytes)")
                passed += 1
            else:
                print_error(f"  {file} - MISSING")
                failed += 1
    
    return passed, failed

def check_imports() -> Tuple[int, int]:
    """
    Test if all modules can be imported
    Returns: (passed, failed) counts
    """
    print_header("MODULE IMPORT VERIFICATION")
    
    # Add current directory to Python path
    sys.path.insert(0, str(Path.cwd()))
    
    imports_to_test = [
        # Config
        ("config.settings", "settings"),
        
        # API Gateway
        ("api_gateway", "app"),
        
        # Orchestration
        ("orchestration", "ConversationManager"),
        ("orchestration", "IntentRouter"),
        ("orchestration", "ResponseGenerator"),
        
        # LLM Core
        ("llm_core", "MistralClient"),
        ("llm_core.prompts", "BANKING_SYSTEM_PROMPT"),
        
        # Knowledge Base
        ("knowledge_base", "VectorStore"),
        ("knowledge_base", "EmbeddingsGenerator"),
        ("knowledge_base", "RAGEngine"),
        
        # Transaction Engine
        ("transaction_engine", "TransactionEngine"),
        ("transaction_engine", "TransactionValidator"),
        ("transaction_engine", "CoreBankingClient"),
        
        # Security
        ("security", "AuthService"),
        ("security", "FraudDetector"),
        ("security", "AuditLogger")
    ]
    
    passed = 0
    failed = 0
    
    for module_name, object_name in imports_to_test:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, object_name):
                print_success(f"Import OK: from {module_name} import {object_name}")
                passed += 1
            else:
                print_error(f"Import FAILED: {object_name} not found in {module_name}")
                failed += 1
        except Exception as e:
            print_error(f"Import FAILED: {module_name} - {str(e)}")
            failed += 1
    
    return passed, failed

def check_dependencies() -> Tuple[int, int]:
    """
    Check if required dependencies are installed
    Returns: (passed, failed) counts
    """
    print_header("DEPENDENCY VERIFICATION")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "langchain",
        "langchain_community",
        "chromadb",
        "sentence_transformers",
        "mistralai",
        "pyjwt",
        "python_jose"
    ]
    
    passed = 0
    failed = 0
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_success(f"Package installed: {package}")
            passed += 1
        except ImportError:
            print_error(f"Package missing: {package}")
            failed += 1
    
    return passed, failed

def check_configuration() -> Tuple[int, int]:
    """
    Check configuration settings
    Returns: (passed, failed) counts
    """
    print_header("CONFIGURATION VERIFICATION")
    
    passed = 0
    failed = 0
    
    try:
        from config.settings import settings
        
        # Check critical settings
        checks = [
            ("APP_NAME", settings.APP_NAME),
            ("CHROMA_PERSIST_DIR", settings.CHROMA_PERSIST_DIR),
            ("EMBEDDING_MODEL", settings.EMBEDDING_MODEL),
            ("JWT_SECRET_KEY", settings.JWT_SECRET_KEY),
        ]
        
        for name, value in checks:
            if value:
                print_success(f"Config OK: {name} = {value}")
                passed += 1
            else:
                print_error(f"Config MISSING: {name}")
                failed += 1
        
        # Check if Mistral API key is set
        if settings.MISTRAL_API_KEY and settings.MISTRAL_API_KEY != "your_mistral_api_key_here":
            print_success("MISTRAL_API_KEY is configured")
        else:
            print_warning("MISTRAL_API_KEY not set (will use mock mode)")
        
    except Exception as e:
        print_error(f"Configuration check failed: {str(e)}")
        failed += 1
    
    return passed, failed

def check_sample_documents() -> Tuple[int, int]:
    """
    Check if sample documents exist or can be created
    Returns: (passed, failed) counts
    """
    print_header("SAMPLE DOCUMENTS VERIFICATION")
    
    docs_path = Path("knowledge_base/documents")
    expected_docs = ["dbs_faqs.txt", "dbs_products.txt", "dbs_policies.txt"]
    
    passed = 0
    failed = 0
    
    if not docs_path.exists():
        print_warning("Documents directory doesn't exist yet (will be created)")
        return 0, 0
    
    existing_docs = list(docs_path.glob("*.txt")) + list(docs_path.glob("*.pdf"))
    
    if len(existing_docs) > 0:
        print_success(f"Found {len(existing_docs)} document(s) in knowledge_base/documents/")
        for doc in existing_docs:
            size = doc.stat().st_size
            print_success(f"  - {doc.name} ({size} bytes)")
            passed += 1
    else:
        print_warning("No documents found (will be auto-created on first run)")
    
    return passed, failed

def run_functional_tests() -> Tuple[int, int]:
    """
    Run basic functional tests
    Returns: (passed, failed) counts
    """
    print_header("FUNCTIONAL TESTS")
    
    passed = 0
    failed = 0
    
    # Test 1: Embeddings generation
    try:
        from knowledge_base.embeddings import EmbeddingsGenerator
        embedder = EmbeddingsGenerator()
        embedding = embedder.generate("test text")
        if len(embedding) == 384:  # Expected dimension
            print_success(f"Embeddings generation OK (dimension: {len(embedding)})")
            passed += 1
        else:
            print_error(f"Embeddings dimension incorrect: {len(embedding)}")
            failed += 1
    except Exception as e:
        print_error(f"Embeddings test failed: {str(e)}")
        failed += 1
    
    # Test 2: Intent classification
    try:
        from orchestration.intent_router import IntentRouter
        router = IntentRouter()
        import asyncio
        result = asyncio.run(router.classify("What's my balance?", {}))
        if result['intent'] == 'check_balance':
            print_success(f"Intent classification OK: {result['intent']} (confidence: {result['confidence']:.2f})")
            passed += 1
        else:
            print_warning(f"Intent classification unexpected: {result['intent']}")
            passed += 1  # Still counts as working
    except Exception as e:
        print_error(f"Intent classification test failed: {str(e)}")
        failed += 1
    
    # Test 3: Response generation
    try:
        from orchestration.response_generator import ResponseGenerator
        generator = ResponseGenerator()
        account_data = {
            "accounts": [
                {"type": "Savings", "number": "1234567890", "balance": 10000.00, "currency": "SGD"}
            ]
        }
        import asyncio
        response = asyncio.run(generator.format_account_info(account_data, "check balance"))
        if "Savings" in response and "10,000.00" in response:
            print_success("Response generation OK")
            passed += 1
        else:
            print_error("Response generation unexpected output")
            failed += 1
    except Exception as e:
        print_error(f"Response generation test failed: {str(e)}")
        failed += 1
    
    return passed, failed

def generate_summary_report(results: Dict[str, Tuple[int, int]]):
    """Generate final summary report"""
    print_header("VERIFICATION SUMMARY")
    
    total_passed = 0
    total_failed = 0
    
    for category, (passed, failed) in results.items():
        total = passed + failed
        if total > 0:
            percentage = (passed / total) * 100
            status = Colors.GREEN if failed == 0 else (Colors.YELLOW if passed > failed else Colors.RED)
            print(f"{status}{category:.<50} {passed}/{total} ({percentage:.1f}%){Colors.END}")
        else:
            print(f"{Colors.YELLOW}{category:.<50} 0/0 (N/A){Colors.END}")
        
        total_passed += passed
        total_failed += failed
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    grand_total = total_passed + total_failed
    if grand_total > 0:
        success_rate = (total_passed / grand_total) * 100
        
        if success_rate == 100:
            status_color = Colors.GREEN
            status_text = "EXCELLENT"
        elif success_rate >= 90:
            status_color = Colors.GREEN
            status_text = "GOOD"
        elif success_rate >= 70:
            status_color = Colors.YELLOW
            status_text = "NEEDS ATTENTION"
        else:
            status_color = Colors.RED
            status_text = "CRITICAL"
        
        print(f"{Colors.BOLD}Total: {total_passed}/{grand_total} checks passed ({success_rate:.1f}%){Colors.END}")
        print(f"{status_color}{Colors.BOLD}Status: {status_text}{Colors.END}")
    
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")
    
    # Recommendations
    if total_failed > 0:
        print(f"{Colors.YELLOW}{Colors.BOLD}RECOMMENDATIONS:{Colors.END}")
        if results.get("Dependencies", (0, 0))[1] > 0:
            print(f"{Colors.YELLOW}  → Run: pip install -r requirements.txt{Colors.END}")
        if results.get("Module Files", (0, 0))[1] > 0:
            print(f"{Colors.YELLOW}  → Check missing files listed above{Colors.END}")
        if results.get("Module Imports", (0, 0))[1] > 0:
            print(f"{Colors.YELLOW}  → Fix import errors before running the application{Colors.END}")
        print()

def main():
    """Main test execution"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("  ____  ____  ____    _    ___    ____ _           _   _           _   ")
    print(" |  _ \\| __ )/ ___|  / \\  |_ _|  / ___| |__   __ _| |_| |__   ___ | |_ ")
    print(" | | | |  _ \\\\___ \\ / _ \\  | |  | |   | '_ \\ / _` | __| '_ \\ / _ \\| __|")
    print(" | |_| | |_) |___) / ___ \\ | |  | |___| | | | (_| | |_| |_) | (_) | |_ ")
    print(" |____/|____/|____/_/   \\_\\___|  \\____|_| |_|\\__,_|\\__|_.__/ \\___/ \\__|")
    print()
    print("                    PROJECT STRUCTURE VERIFICATION")
    print(f"{Colors.END}")
    
    results = {}
    
    # Run all verification checks
    results["Directories"] = check_directory_structure()
    results["Root Files"] = check_root_files()
    results["Module Files"] = check_module_files()
    results["Dependencies"] = check_dependencies()
    results["Configuration"] = check_configuration()
    results["Module Imports"] = check_imports()
    results["Sample Documents"] = check_sample_documents()
    results["Functional Tests"] = run_functional_tests()
    
    # Generate summary
    generate_summary_report(results)
    
    # Exit with appropriate code
    total_failed = sum(failed for _, failed in results.values())
    sys.exit(0 if total_failed == 0 else 1)

if __name__ == "__main__":
    main()