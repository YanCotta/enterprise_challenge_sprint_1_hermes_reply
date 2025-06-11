# Configuration Management

🇧🇷 **[Clique aqui para ler em Português](#-gerenciamento-de-configuração-português)** | 🇺🇸 **English Version Below**

## 📚 Documentation Links

- **[Backend README](../../README.md)** - Main documentation and Docker deployment
- **[System Screenshots](../../docs/SYSTEM_SCREENSHOTS.md)** - Complete visual system walkthrough with screenshots
- **[System Architecture](../../docs/SYSTEM_AND_ARCHITECTURE.md)** - Complete system overview
- **[Future Roadmap](../../docs/FUTURE_ROADMAP.md)** - Strategic vision and planned enhancements
- **[Deployment Status](../../docs/DEPLOYMENT_STATUS.md)** - Current system status
- **[Performance Baseline](../../docs/PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics
- **[Load Testing Instructions](../../docs/LOAD_TESTING_INSTRUCTIONS.md)** - Comprehensive guide for running performance tests
- **[API Documentation](../../docs/api.md)** - Complete REST API reference and usage examples
- **[Test Documentation](../../tests/README.md)** - Test organization and execution guide
- **[Logging Configuration](../logging_config.md)** - Structured JSON logging setup and configuration
- **[Project Overview](../../../README.md)** - High-level project information

---

This module provides a centralized configuration system for the Smart Maintenance SaaS application using Pydantic's `BaseSettings`.

## Usage

### Basic Import

```python
from core.config import settings

# Use settings directly
database_url = settings.database_url
api_port = settings.api_port
```

### Dependency Injection (FastAPI)

```python
from fastapi import Depends
from core.config import get_settings, Settings

@app.get("/items")
def read_items(settings: Settings = Depends(get_settings)):
    return {"database": settings.database_url, "debug": settings.debug}
```

### Class-based Usage

```python
from core.config import settings

class DatabaseService:
    def __init__(self):
        self.connection_string = settings.database_url
        # Use other settings as needed
```

## Environment Variables

Configuration can be set via environment variables or a `.env` file. The `.env.example` file in the project root shows all available configuration options.

For Docker Compose setups, use service names (e.g., `db`) instead of `localhost`.

## Available Settings

### Database Configuration

- `DATABASE_URL`: PostgreSQL connection string
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Database username (default: smart_user)
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name (default: smart_maintenance_db)
- `TEST_DATABASE_URL`: Test database connection string

### Cache & Message Queue

- `REDIS_URL`: Redis connection string (for future use)
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers (for future use)

### API Configuration

- `API_HOST`: Host to bind the API server (default: 0.0.0.0)
- `API_PORT`: Port for the API server (default: 8000)
- `DEBUG`: Debug mode flag (default: false)

### Security

- `SECRET_KEY`: Secret key for security features
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 60)
- `API_KEY`: Static API Key for basic authentication

### Agent System

- `AGENT_COMMUNICATION_TIMEOUT`: Timeout for agent communication (default: 30)

### Scheduling

- `USE_OR_TOOLS_SCHEDULER`: Enable advanced OR-Tools constraint programming scheduler (default: false)

### Machine Learning

- `MODEL_REGISTRY_PATH`: Path to ML model storage (default: ./models)

### Notification Services

- `WHATSAPP_API_KEY`: WhatsApp API key for notifications
- `EMAIL_SMTP_HOST`: SMTP server host
- `EMAIL_SMTP_PORT`: SMTP server port (default: 587)
- `EMAIL_SMTP_USER`: SMTP username
- `EMAIL_SMTP_PASSWORD`: SMTP password

### Logging

- `LOG_LEVEL`: Logging level (default: INFO)

### Event Bus & Dead Letter Queue

- `EVENT_HANDLER_MAX_RETRIES`: Maximum retry attempts for event handlers (default: 3)
- `EVENT_HANDLER_RETRY_DELAY_SECONDS`: Delay between retries (default: 1.0)
- `DLQ_ENABLED`: Enable Dead Letter Queue for failed events (default: true)
- `DLQ_LOG_FILE`: Path to DLQ log file (default: logs/dlq_events.log)

### Orchestrator Settings

- `ORCHESTRATOR_URGENT_MAINTENANCE_DAYS`: Threshold for urgent maintenance (default: 30)
- `ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD`: High confidence level (default: 0.90)
- `ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD`: Moderate confidence level (default: 0.75)
- `ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE`: Auto-approval threshold (default: 15)
- `ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR`: Very urgent factor (default: 0.5)

## Adding New Settings

To add new settings:

1. Add the setting to the `Settings` class in `settings.py`
2. Add a default value
3. Update the `.env.example` file
4. Use the setting in your application via `settings.your_new_setting`

---

## 🇧🇷 Gerenciamento de Configuração (Português)

Este módulo fornece um sistema centralizado de configuração para a aplicação Smart Maintenance SaaS usando `BaseSettings` do Pydantic.

## Uso

### Importação Básica

```python
from core.config import settings

# Use as configurações diretamente
database_url = settings.database_url
api_port = settings.api_port
```

### Injeção de Dependência (FastAPI)

```python
from fastapi import Depends
from core.config import get_settings, Settings

@app.get("/items")
def read_items(settings: Settings = Depends(get_settings)):
    return {"database": settings.database_url, "debug": settings.debug}
```

### Uso Baseado em Classe

```python
from core.config import settings

class DatabaseService:
    def __init__(self):
        self.connection_string = settings.database_url
        # Use outras configurações conforme necessário
```

## Variáveis de Ambiente

A configuração pode ser definida via variáveis de ambiente ou um arquivo `.env`. O arquivo `.env.example` na raiz do projeto mostra todas as opções de configuração disponíveis.

Para configurações do Docker Compose, use nomes de serviços (ex: `db`) ao invés de `localhost`.

## Configurações Disponíveis

### Configuração do Banco de Dados

- `DATABASE_URL`: String de conexão PostgreSQL
- `DB_HOST`: Host do banco de dados (padrão: localhost)
- `DB_PORT`: Porta do banco de dados (padrão: 5432)
- `DB_USER`: Nome de usuário do banco (padrão: smart_user)
- `DB_PASSWORD`: Senha do banco de dados
- `DB_NAME`: Nome do banco de dados (padrão: smart_maintenance_db)
- `TEST_DATABASE_URL`: String de conexão do banco de testes

### Cache e Fila de Mensagens

- `REDIS_URL`: String de conexão Redis (para uso futuro)
- `KAFKA_BOOTSTRAP_SERVERS`: Servidores bootstrap Kafka (para uso futuro)

### Configuração da API

- `API_HOST`: Host para vincular o servidor da API (padrão: 0.0.0.0)
- `API_PORT`: Porta para o servidor da API (padrão: 8000)
- `DEBUG`: Flag do modo debug (padrão: false)

### Segurança

- `SECRET_KEY`: Chave secreta para recursos de segurança
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tempo de expiração do token (padrão: 60)
- `API_KEY`: Chave API estática para autenticação básica

### Sistema de Agentes

- `AGENT_COMMUNICATION_TIMEOUT`: Timeout para comunicação entre agentes (padrão: 30)

### Agendamento

- `USE_OR_TOOLS_SCHEDULER`: Habilitar agendador avançado OR-Tools (padrão: false)

### Aprendizado de Máquina

- `MODEL_REGISTRY_PATH`: Caminho para armazenamento de modelos ML (padrão: ./models)

### Serviços de Notificação

- `WHATSAPP_API_KEY`: Chave API WhatsApp para notificações
- `EMAIL_SMTP_HOST`: Host do servidor SMTP
- `EMAIL_SMTP_PORT`: Porta do servidor SMTP (padrão: 587)
- `EMAIL_SMTP_USER`: Nome de usuário SMTP
- `EMAIL_SMTP_PASSWORD`: Senha SMTP

### Sistema de Logs

- `LOG_LEVEL`: Nível de logging (padrão: INFO)

### Event Bus e Dead Letter Queue

- `EVENT_HANDLER_MAX_RETRIES`: Máximo de tentativas para handlers de eventos (padrão: 3)
- `EVENT_HANDLER_RETRY_DELAY_SECONDS`: Delay entre tentativas (padrão: 1.0)
- `DLQ_ENABLED`: Habilitar Dead Letter Queue para eventos falhados (padrão: true)
- `DLQ_LOG_FILE`: Caminho para arquivo de log DLQ (padrão: logs/dlq_events.log)

### Configurações do Orquestrador

- `ORCHESTRATOR_URGENT_MAINTENANCE_DAYS`: Limite para manutenção urgente (padrão: 30)
- `ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD`: Nível de alta confiança (padrão: 0.90)
- `ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD`: Nível de confiança moderada (padrão: 0.75)
- `ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE`: Limite para aprovação automática (padrão: 15)
- `ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR`: Fator para urgência muito alta (padrão: 0.5)

## Adicionando Novas Configurações

Para adicionar novas configurações:

1. Adicione a configuração à classe `Settings` em `settings.py`
2. Adicione um valor padrão
3. Atualize o arquivo `.env.example`
4. Use a configuração em sua aplicação via `settings.sua_nova_configuracao`
