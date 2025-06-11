# Structured JSON Logging

🇧🇷 **[Clique aqui para ler em Português](#-logging-json-estruturado-português)** | 🇺🇸 **English Version Below**

## 📚 Documentation Links

- **[Backend README](../README.md)** - Main documentation and Docker deployment
- **[System Screenshots](../docs/SYSTEM_SCREENSHOTS.md)** - Complete visual system walkthrough with screenshots
- **[System Architecture](../docs/SYSTEM_AND_ARCHITECTURE.md)** - Complete system overview
- **[Future Roadmap](../docs/FUTURE_ROADMAP.md)** - Strategic vision and planned enhancements
- **[Deployment Status](../docs/DEPLOYMENT_STATUS.md)** - Current system status
- **[Performance Baseline](../docs/PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics
- **[Load Testing Instructions](../docs/LOAD_TESTING_INSTRUCTIONS.md)** - Comprehensive guide for running performance tests
- **[API Documentation](../docs/api.md)** - Complete REST API reference and usage examples
- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Configuration Management](config/README.md)** - Centralized configuration system using Pydantic BaseSettings
- **[Project Overview](../../README.md)** - High-level project information

---

This module provides structured JSON logging for the Smart Maintenance SaaS application. It configures the Python standard logging system to output logs in JSON format with consistent fields, making them easier to parse and analyze with log management systems.

## Key Features

- **JSON Format**: All logs are formatted as JSON objects for easier parsing and indexing
- **Standard Fields**: Every log entry includes timestamp, level, message, logger name, file, line number
- **Service Information**: Service name and hostname are included in each log entry
- **Request Tracking**: Support for correlation IDs to track requests across services
- **Extra Fields**: Support for adding custom fields to log entries
- **Async Support**: Works well with FastAPI and other async frameworks

## Usage

### Basic Setup

```python
from core.logging_config import setup_logging, get_logger

# Initialize logging at application startup
setup_logging()

# Get a module-level logger
logger = get_logger(__name__)

# Log messages
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
```

### Logging with Extra Fields

```python
logger.info(
    "User performed action",
    extra={
        "user_id": 123,
        "action": "login",
        "duration_ms": 120,
    },
)
```

### Class-based Logging

```python
class UserService:
    def __init__(self):
        self.logger = get_logger(f"{__name__}.UserService")

    def authenticate(self, username):
        self.logger.info("Authenticating user", extra={"username": username})
        # ...
```

### Exception Logging

```python
try:
    result = 1 / 0  # This will raise a ZeroDivisionError
except Exception as e:
    logger.exception(
        "Error during calculation",
        extra={
            "operation": "division",
            "error_type": type(e).__name__,
        },
    )
```

### Request Context Logging

The `RequestContextFilter` class can be used to add request context (like request IDs) to all logs during a request:

```python
@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_filter = RequestContextFilter(request_id)
    logger.addFilter(request_filter)

    try:
        # Process request
        response = await call_next(request)
        return response
    finally:
        # Always remove the filter
        logger.removeFilter(request_filter)
```

## Examples

The project includes practical examples of using the logging system:

- **[Basic Logging Example](../examples/logging_example.py)** - Demonstrates basic logging functionality and best practices
- **[FastAPI Logging Example](../examples/fastapi_logging_example.py)** - Shows integration with FastAPI including request context tracking

These examples show real-world usage patterns and can serve as templates for implementing logging in your modules.

## Production Usage

The logging system is actively used throughout the application:

- **API Layer**: FastAPI application logs requests and responses with correlation IDs
- **Agent System**: Decision agents use structured logging for traceability
- **Service Layer**: Business logic components log operations with contextual information
- **Error Handling**: Comprehensive exception logging with stack traces and context

## Log Format

Each log entry includes:

- `timestamp`: ISO8601 format timestamp (UTC)
- `level`: Log level (INFO, WARNING, ERROR, etc.)
- `name`: Logger name
- `message`: Log message
- `service`: Service name
- `hostname`: Host identifier
- `file`: Source file
- `line`: Line number
- `process` and `process_name`: Process info
- `thread` and `thread_name`: Thread info
- `correlation_id`: Request ID (when available)
- Any additional fields passed via `extra`

## Example Output

```json
{
  "timestamp": "2025-05-28T12:30:38.161550Z",
  "level": "INFO",
  "name": "api",
  "message": "User authenticated successfully",
  "service": "smart-maintenance-saas",
  "hostname": "server-01",
  "file": "user_service.py",
  "line": 56,
  "process": 123456,
  "process_name": "MainProcess",
  "thread": 140123456789,
  "thread_name": "MainThread",
  "correlation_id": "44f05c3e-6723-4b97-a208-3d874a3c50c7",
  "username": "john.doe",
  "roles": ["user", "admin"],
  "auth_method": "password"
}
```

## 🇧🇷 Logging JSON Estruturado (Português)

Este módulo fornece logging JSON estruturado para a aplicação Smart Maintenance SaaS. Configura o sistema de logging padrão do Python para produzir logs em formato JSON com campos consistentes, facilitando a análise e parsing com sistemas de gerenciamento de logs.

## Características Principais

- **Formato JSON**: Todos os logs são formatados como objetos JSON para facilitar parsing e indexação
- **Campos Padrão**: Cada entrada de log inclui timestamp, nível, mensagem, nome do logger, arquivo, número da linha
- **Informações do Serviço**: Nome do serviço e hostname são incluídos em cada entrada de log
- **Rastreamento de Requisições**: Suporte para IDs de correlação para rastrear requisições entre serviços
- **Campos Extras**: Suporte para adicionar campos personalizados às entradas de log
- **Suporte Assíncrono**: Funciona bem com FastAPI e outros frameworks assíncronos

## Uso

### Configuração Básica

```python
from core.logging_config import setup_logging, get_logger

# Inicializar logging na inicialização da aplicação
setup_logging()

# Obter um logger no nível do módulo
logger = get_logger(__name__)

# Registrar mensagens
logger.info("Esta é uma mensagem de info")
logger.warning("Esta é uma mensagem de aviso")
logger.error("Esta é uma mensagem de erro")
```

### Logging com Campos Extras

```python
logger.info(
    "Usuário realizou ação",
    extra={
        "user_id": 123,
        "action": "login",
        "duration_ms": 120,
    },
)
```

### Logging Baseado em Classe

```python
class UserService:
    def __init__(self):
        self.logger = get_logger(f"{__name__}.UserService")

    def authenticate(self, username):
        self.logger.info("Autenticando usuário", extra={"username": username})
        # ...
```

### Logging de Exceções

```python
try:
    result = 1 / 0  # Isso irá gerar um ZeroDivisionError
except Exception as e:
    logger.exception(
        "Erro durante cálculo",
        extra={
            "operation": "division",
            "error_type": type(e).__name__,
        },
    )
```

### Logging de Contexto de Requisição

A classe `RequestContextFilter` pode ser usada para adicionar contexto de requisição (como IDs de requisição) a todos os logs durante uma requisição:

```python
@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_filter = RequestContextFilter(request_id)
    logger.addFilter(request_filter)

    try:
        # Processar requisição
        response = await call_next(request)
        return response
    finally:
        # Sempre remover o filtro
        logger.removeFilter(request_filter)
```

## Exemplos

O projeto inclui exemplos práticos de uso do sistema de logging:

- **[Exemplo de Logging Básico](../examples/logging_example.py)** - Demonstra funcionalidade básica de logging e melhores práticas
- **[Exemplo de Logging FastAPI](../examples/fastapi_logging_example.py)** - Mostra integração com FastAPI incluindo rastreamento de contexto de requisição

Estes exemplos mostram padrões de uso do mundo real e podem servir como templates para implementar logging em seus módulos.

## Uso em Produção

O sistema de logging é usado ativamente em toda a aplicação:

- **Camada API**: Aplicação FastAPI registra requisições e respostas com IDs de correlação
- **Sistema de Agentes**: Agentes de decisão usam logging estruturado para rastreabilidade
- **Camada de Serviço**: Componentes de lógica de negócio registram operações com informações contextuais
- **Tratamento de Erros**: Logging abrangente de exceções com stack traces e contexto

## Formato do Log

Cada entrada de log inclui:

- `timestamp`: Timestamp em formato ISO8601 (UTC)
- `level`: Nível do log (INFO, WARNING, ERROR, etc.)
- `name`: Nome do logger
- `message`: Mensagem do log
- `service`: Nome do serviço
- `hostname`: Identificador do host
- `file`: Arquivo fonte
- `line`: Número da linha
- `process` e `process_name`: Informações do processo
- `thread` e `thread_name`: Informações da thread
- `correlation_id`: ID da requisição (quando disponível)
- Quaisquer campos adicionais passados via `extra`

## Exemplo de Saída

```json
{
  "timestamp": "2025-06-11T12:30:38.161550Z",
  "level": "INFO",
  "name": "api",
  "message": "Usuário autenticado com sucesso",
  "service": "smart-maintenance-saas",
  "hostname": "server-01",
  "file": "user_service.py",
  "line": 56,
  "process": 123456,
  "process_name": "MainProcess",
  "thread": 140123456789,
  "thread_name": "MainThread",
  "correlation_id": "44f05c3e-6723-4b97-a208-3d874a3c50c7",
  "username": "john.doe",
  "roles": ["user", "admin"],
  "auth_method": "password"
}
```
