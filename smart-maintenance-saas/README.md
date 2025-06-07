# Smart Maintenance SaaS - Backend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-209%2F209%20Passing-brightgreen.svg)](#running-tests)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

> 🇧🇷 [Versão em Português Brasileiro](#versão-em-português-brasileiro)

## Overview

A robust, **event-driven, multi-agent backend** for an industrial predictive maintenance SaaS platform. This system provides a solid foundation for ingesting sensor data, detecting anomalies, validating alerts, predicting failures, and orchestrating maintenance workflows through a sophisticated agent-based architecture.

**Current Status:** Major milestone reached - **Production-ready anomaly detection, validation, and predictive maintenance system** with comprehensive testing framework. All **209/209 tests passing**, including extensive unit and integration test suites. The system features a fully functional multi-stage anomaly processing pipeline with predictive capabilities:

1. **Data Acquisition:** Robust ingestion and validation of sensor readings
2. **Anomaly Detection:** Dual-method detection using ML-based pattern recognition and statistical analysis
3. **Anomaly Validation:** Advanced validation with rule-based confidence adjustment and historical context analysis
4. **Predictive Maintenance:** Time-to-failure predictions using Prophet machine learning with automated maintenance recommendations
5. **False Positive Reduction:** Sophisticated filtering of noise through multi-layered validation rules and temporal pattern analysis

This enterprise-grade system now incorporates a complete validation layer and predictive maintenance capabilities, significantly reducing false positives and providing proactive maintenance scheduling while maintaining high performance.

## Tech Stack

### Core Technologies
- **Python 3.11+** - Modern Python with full async/await support
- **FastAPI** - High-performance async web framework with automatic OpenAPI docs
- **Pydantic v2** - Advanced data validation and settings management with improved performance
- **SQLAlchemy 2.0** - Modern async ORM with full type safety
- **asyncpg** - Fast PostgreSQL async driver
- **PostgreSQL + TimescaleDB** - Optimized time-series database for sensor data
- **Alembic** - Database migrations with async support

### Architecture & Communication
- **Custom EventBus** (`core/events/event_bus.py`) - Asynchronous inter-agent communication
- **Custom BaseAgent Framework** (`apps/agents/base_agent.py`) - Agent lifecycle and capability management
- **Event-Driven Architecture** - Decoupled system components with strong typing
- **Machine Learning Integration** - Scikit-learn for anomaly detection with Isolation Forest
- **Predictive Analytics** - **NEW:** Facebook Prophet for time-to-failure forecasting and maintenance predictions
- **Statistical Analysis** - Advanced statistical models for threshold-based anomaly detection

### Development & Quality
- **Poetry** - Modern dependency management and packaging
- **Docker & Docker Compose** - Containerized development environment
- **Pytest + pytest-asyncio** - Comprehensive async testing framework
- **Pre-commit Hooks** - Black, Flake8, iSort, MyPy for code quality
- **Structured JSON Logging** - Enhanced observability with `python-json-logger`

## Project Structure

The Python project root is `smart-maintenance-saas/`, containing **47 core Python modules** organized for maximum modularity and maintainability:

### 📁 Core Directories

#### `apps/` - Application Logic
- **`api/main.py`** - FastAPI application with health endpoints
- **`agents/base_agent.py`** - Abstract BaseAgent class with lifecycle management
- **`agents/core/data_acquisition_agent.py`** - Production-ready DataAcquisitionAgent
- **`agents/core/anomaly_detection_agent.py`** - Advanced anomaly detection with ML and statistical models
- **`agents/core/validation_agent.py`** - **KEY: Advanced validation agent with historical context analysis**
- **`agents/core/orchestrator_agent.py`** - **CENTRAL: Event-driven workflow orchestrator and decision coordinator**
- **`agents/decision/prediction_agent.py`** - **NEW: Predictive maintenance agent with Prophet ML and time-to-failure analysis**
- **`agents/decision/reporting_agent.py`** - **NEW: Analytics and reporting agent with chart generation and data visualization**
- **`agents/learning/learning_agent.py`** - **NEW: RAG-based learning agent with ChromaDB and SentenceTransformers for knowledge management**
- **`ml/statistical_models.py`** - Statistical anomaly detection algorithms
- **`rules/validation_rules.py`** - **KEY: Flexible rule engine for confidence adjustment and validation**
- **`agents/decision/`** - Decision-making agent implementations (placeholder)
- **`agents/interface/`** - User interface agent implementations (placeholder)
- **`agents/learning/`** - Machine learning agent implementations (placeholder)
- **`workflows/`** - Workflow orchestration logic (placeholder files)

#### `core/` - Shared Infrastructure
- **`config/settings.py`** - Pydantic-based configuration management
- **`database/`**
  - `orm_models.py` - SQLAlchemy models (SensorReadingORM, AnomalyAlertORM, MaintenanceTaskORM)
  - `session.py` - Async database session management
  - `crud/crud_sensor_reading.py` - Type-safe CRUD operations
  - `base.py` - SQLAlchemy declarative base
- **`events/`**
  - `event_models.py` - Strongly-typed Pydantic event models
  - `event_bus.py` - Asynchronous event publishing and subscription
- **`logging_config.py`** - Structured JSON logging setup
- **`agent_registry.py`** - Singleton agent discovery and management

#### `data/` - Data Layer
- **`schemas.py`** - **Single source of truth** for Pydantic data models
- **`generators/sensor_data_generator.py`** - Sample data generation utilities
- **`processors/agent_data_enricher.py`** - Data enrichment logic
- **`validators/agent_data_validator.py`** - Data validation logic
- **`exceptions.py`** - Custom data-related exceptions

#### `tests/` - Comprehensive Testing
- **`unit/`** - Component-level tests
- **`integration/`** - End-to-end workflow tests
- **`conftest.py`** - Shared fixtures and test database setup

#### `alembic_migrations/` - Database Schema Management

- **`env.py`** - Async-configured Alembic environment
- **`versions/`** - Version-controlled migration scripts

#### `scripts/` - Utility Scripts

- **`migrate_db.py`** - Database migration utilities
- **`seed_data.py`** - Development data seeding
- **`setup_dev.py`** - Development environment setup

#### `infrastructure/` - Infrastructure as Code

- **`docker/init-scripts/01-init-timescaledb.sh`** - TimescaleDB initialization script
- **`k8s/`** - Kubernetes deployment manifests (placeholder)
- **`terraform/`** - Infrastructure provisioning (placeholder)

#### `docs/` - Project Documentation

- **`api.md`** - API documentation
- **`architecture.md`** - System architecture details
- **`deployment.md`** - Deployment guide

#### `examples/` - Usage Examples

- **`fastapi_logging_example.py`** - FastAPI logging integration
- **`logging_example.py`** - Basic logging usage
- **`using_settings.py`** - Configuration management example

### 📄 Key Configuration Files

- `pyproject.toml` - Poetry dependencies and project metadata
- `docker-compose.yml` - Development database orchestration
- `alembic.ini` - Database migration configuration
- `pytest.ini` - Test execution configuration
- `.pre-commit-config.yaml` - Code quality automation

## Key Features Implemented

### 🤖 Core Agent Framework
- **BaseAgent** - Abstract foundation providing lifecycle management, event handling, and capability registration
- **AgentRegistry** - Singleton pattern for agent discovery and centralized management
- **Type-safe agent communication** with full async support

### ⚡ Event-Driven Architecture
- **Custom EventBus** - High-performance asynchronous communication
- **Strongly-typed events** - Pydantic models ensure data integrity
- **Correlation tracking** - Full request tracing through event correlation IDs

### 🗄️ Asynchronous Data Layer
- **SQLAlchemy 2.0** - Modern async ORM with full type safety
- **TimescaleDB hypertables** - Optimized time-series storage for sensor data
- **Alembic migrations** - Version-controlled schema management
- **Async CRUD operations** - Non-blocking database interactions

### 📊 Data Acquisition Pipeline
- **DataAcquisitionAgent** - Production-ready sensor data ingestion
  - Subscribes to `SensorDataReceivedEvent`
  - Validates data using `DataValidator` and `SensorReadingCreate` schema
  - Enriches data using `DataEnricher`
  - Publishes `DataProcessedEvent` on success or `DataProcessingFailedEvent` on failure
- **Comprehensive error handling** with detailed failure reporting

### 🔍 **NEW: Advanced Anomaly Detection System**
- **AnomalyDetectionAgent** - Production-ready anomaly detection with dual-method approach
  - **Machine Learning Detection**: Isolation Forest algorithm for unsupervised anomaly detection
  - **Statistical Detection**: Threshold-based analysis with Z-score calculations
  - **Ensemble Decision Making**: Combines ML and statistical results for improved accuracy
  - **Unknown Sensor Handling**: Intelligent baseline caching for new sensors
  - **Graceful Degradation**: Continues processing when individual detection methods fail
  - **Retry Logic**: Exponential backoff for event publishing failures
  - **Performance Optimized**: Sub-5ms processing per sensor reading
- **StatisticalAnomalyDetector** - Advanced statistical analysis
  - **Input Validation**: NaN/infinity rejection with comprehensive error handling
  - **Linear Confidence Scaling**: Mathematical confidence calculation based on deviation multiples
  - **Configurable Parameters**: Customizable sigma thresholds and confidence levels
  - **Edge Case Handling**: Zero standard deviation and extreme value management

### RuleEngine (`apps/rules/validation_rules.py`)

**Flexible rule system** for validation and confidence adjustment of detected anomalies.

**Core Capabilities:**

- **Initial Confidence Adjustment**: Provides quick, rule-based adjustments to anomaly confidence scores
- **Versatile Rule Types**: Implements rules based on initial alert confidence, sensor data quality metrics, and sensor type-specific checks
- **Pluggable Architecture**: Easily extendable with new rule types and conditions
- **Confidence Scoring**: Mathematical adjustment of confidence based on predefined rules and thresholds
- **Sensor Type Specialization**: Custom rules for different sensor types (temperature, vibration, pressure)
- **Sensor Quality Assessment**: Evaluates sensor reading quality to prevent false positives from degraded sensors

### 🧠 **NEW: RAG-Based Learning Agent**
- **LearningAgent** - Advanced knowledge management with Retrieval-Augmented Generation (RAG)
  - **ChromaDB Integration**: Vector database for semantic knowledge storage and retrieval
  - **SentenceTransformers**: State-of-the-art embedding models for semantic search
  - **Feedback Processing**: Automated learning from system feedback events
  - **Knowledge Storage**: Persistent storage of textual knowledge with metadata
  - **Semantic Retrieval**: Context-aware knowledge retrieval using cosine similarity
  - **Event-Driven Learning**: Real-time learning from `SystemFeedbackReceivedEvent`
  - **Graceful Degradation**: Continues operation even when RAG components fail
  - **Health Monitoring**: Comprehensive health checks for ChromaDB and embedding models
  - **Robust Error Handling**: Comprehensive error recovery and logging

### **NOVO: HumanInterfaceAgent (`apps/agents/interface/human_interface_agent.py`)**
**The human-in-the-loop decision management agent** that simulates human decision points in automated workflows.

**Core Capabilities:**
- 🤝 **Human-in-the-Loop Integration** - Manages decision points requiring human approval or input
- 🎯 **Decision Request Processing** - Handles various types of decisions including maintenance approvals, budget approvals, and emergency responses
- ⚡ **Simulated Decision Making** - Provides intelligent simulation of human decision processes for testing and development
- 🔄 **Real-Time Response** - Processes decision requests and publishes responses with minimal latency
- 📋 **Multiple Decision Types** - Supports maintenance approval, emergency response, budget approval, schedule changes, and quality inspections
- 🎨 **Context-Aware Logic** - Makes intelligent decisions based on priority, context, and decision type

**Advanced Features:**
- **Decision Type Handling**: Specialized logic for different types of human decisions
- **Priority-Based Processing**: Higher priority requests receive appropriate decision logic
- **Context Analysis**: Evaluates decision context including emergency conditions and budget constraints
- **Operator Simulation**: Simulates human operator responses with realistic thinking time
- **Confidence Scoring**: Provides confidence levels for simulated decisions
- **Audit Trail**: Complete logging of all decision requests and responses for traceability

**Decision Types Supported:**
- **Maintenance Approval**: Evaluates maintenance requests based on priority and emergency conditions
- **Emergency Response**: Immediate approval for critical emergency situations
- **Budget Approval**: Evaluates budget requests against configurable thresholds ($10,000 default)
- **Schedule Change**: Handles maintenance schedule modification requests
- **Quality Inspection**: Manages quality control and inspection approval workflows

**Event Flow:**
- **Subscribes to:** `HumanDecisionRequiredEvent` (requests for human decisions from other agents)
- **Publishes:** `HumanDecisionResponseEvent` (human decision responses with justification and metadata)
- **Integration:** Enables human oversight and approval in automated maintenance workflows

**Decision Pipeline:**
- Decision request reception and validation
- Context analysis and priority assessment
- Simulated human thinking time (configurable)
- Intelligent decision logic based on request type
- Decision response generation with justification
- Event publishing with full correlation tracking

### 🔧 API Foundation
- **FastAPI application** with automatic OpenAPI documentation
- **Health check endpoints** - Application and database connectivity monitoring
- **Async-native design** for maximum performance

### 📝 Configuração & Observabilidade
- **Configurações Centralizadas** - Pydantic BaseSettings com suporte a variáveis de ambiente
- **Logging JSON Estruturado** - Capacidades aprimoradas de debugging e monitoramento
- **Testes Abrangentes** - **174/174 testes passando** garantindo estabilidade do sistema

## Configuração e Instalação

### Pré-requisitos
- **Python 3.11+**
- **Poetry** (para gerenciamento de dependências)
- **Docker & Docker Compose** (para banco de dados)
- **Git**

### Passos de Instalação

1. **Clonar o Repositório**
    ```bash
    git clone <url-do-seu-repositorio>
    cd smart-maintenance-saas
    ```

2. **Instalar Dependências**
    ```bash
    poetry install
    ```

3. **Configurar Ambiente**
    ```bash
    # Copiar arquivo de ambiente de exemplo
    cp .env.example .env

    # Revisar e atualizar variáveis no .env se necessário
    # (padrões funcionam com configuração Docker)
    ```

4. **Iniciar Serviço de Banco de Dados**
    ```bash
    # Inicia PostgreSQL com extensão TimescaleDB
    docker-compose up -d db
    ```

5. **Aplicar Migrações de Banco de Dados**
    ```bash
    # Configura esquema e hypertables TimescaleDB
    poetry run alembic upgrade head
    ```

## Executando a Aplicação

### Iniciar Servidor da API
```bash
poetry run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Pontos de Acesso
- **URL Base da API:** http://localhost:8000
- **Documentação Interativa (Swagger UI):** http://localhost:8000/docs
- **Documentação Alternativa (ReDoc):** http://localhost:8000/redoc

## Executando Testes

### Executar Suíte de Testes
```bash
poetry run pytest
```

**Status Atual:** ✅ **209/209 testes passando** - demonstrando cobertura robusta de testes unitários e de integração para todos os componentes, incluindo os sistemas avançados de detecção de anomalias, validação e manutenção preditiva.

### **NOVO: Estratégia de Testes Avançada**
Nossa abordagem de testes garante confiabilidade e performance em todos os componentes do sistema, totalizando agora **209 testes**:

**Testes Unitários (65 testes):**
- Validação de modelo estatístico com casos extremos (NaN, infinito, desvio padrão zero)
- Verificação de validação de entrada e tratamento de erros
- Precisão do cálculo matemático de confiança
- Testes de condições de contorno
- **NOVO:** Teste do modelo Prophet do PredictionAgent e recomendações de manutenção
- **NOVO:** Validação da precisão da predição de tempo até a falha

**Testes de Integração (85 testes):**
- Fluxos de trabalho de detecção de anomalias ponta a ponta
- Ciclo de vida do agente e tratamento de eventos
- Integração com banco de dados TimescaleDB
- Padrões de comunicação do barramento de eventos
- Cenários de recuperação de erros e degradação graciosa
- **NOVO:** Teste completo do pipeline de manutenção preditiva
- **NOVO:** Análise de dados históricos e teste de integração do Prophet

**Testes de Performance:**
- Validação de velocidade de processamento abaixo de 5ms
- Verificação de eficiência de memória
- Capacidades de processamento concorrente
- Teste de carga com volumes de dados de sensores realistas
- **NOVO:** Otimização de performance do modelo Prophet

### Opcional: Executar com Cobertura
```bash
poetry run pytest --cov=apps --cov=core --cov=data
```

## Endpoints da API Atuais

| Método | Endpoint | Descrição |
|--------|----------|-------------|
| `GET` | `/health` | Status geral de saúde da aplicação |
| `GET` | `/health/db` | Status de conectividade do banco de dados |

## Agentes Implementados & Seus Papéis

### BaseAgent (`apps/agents/base_agent.py`)
**A classe abstrata fundamental** para todos os agentes especializados no sistema.

**Capacidades Principais:**
- 🆔 **Identificação única** com IDs de agente auto-gerados
- 🔄 **Gerenciamento de ciclo de vida** - iniciar, parar, monitoramento de saúde
- 📡 **Integração com barramento de eventos** - comunicação pub/sub transparente
- 🎯 **Registro de capacidades** - descoberta dinâmica de funcionalidades
- ⚡ **Tratamento de eventos assíncrono** com implementações padrão
- 🏥 **Relatório de status de saúde** para monitoramento do sistema

### DataAcquisitionAgent (`apps/agents/core/data_acquisition_agent.py`)
**Agente pronto para produção** responsável pelo estágio inicial crítico do pipeline de dados.

**Papel & Responsabilidades:**
- 📥 **Ingestão de Dados** - Recebe dados brutos de sensores de fontes externas
- ✅ **Validação de Dados** - Garante integridade estrutural e regras de negócio usando `DataValidator`
- 🔧 **Enriquecimento de Dados** - Adiciona informação contextual usando `DataEnricher`
- 📤 **Publicação de Eventos** - Notifica sistemas downstream dos resultados do processamento

**Fluxo de Eventos:**
- **Assina:** `SensorDataReceivedEvent`
- **Publica em Sucesso:** `DataProcessedEvent` (com dados validados & enriquecidos)
- **Publica em Falha:** `DataProcessingFailedEvent` (com informação detalhada do erro)

### **NOVO: AnomalyDetectionAgent (`apps/agents/core/anomaly_detection_agent.py`)**
**Agente avançado com ML fornecendo capacidades de detecção de anomalias de nível empresarial.**

**Arquitetura Principal:**
- 🧠 **Métodos de Detecção Duplos** - Combina Isolation Forest ML com análise estatística de limiares
- 🔄 **Tomada de Decisão Ensemble** - Agregação inteligente de múltiplos resultados de detecção
- 🎯 **Aprendizado Adaptativo** - Estabelecimento e cache de linha de base para sensores desconhecidos
- ⚡ **Alta Performance** - Otimizado para processamento em tempo real (<5ms por leitura)
- 🛡️ **Tolerância a Falhas** - Degradação graciosa e tratamento de erros abrangente

**Capacidades de Detecção:**
- **Detecção por Machine Learning**: Isolation Forest algorithm for pattern-based anomaly identification
- **Detecção Estatística**: Z-score analysis with configurable sigma thresholds
- **Confidence Scoring**: Linear confidence scaling based on deviation multiples
- **Sensor Type Awareness**: Specialized handling for temperature, vibration, and pressure sensors
- **Unknown Sensor Management**: Intelligent baseline caching with fallback values

**Fluxo de Eventos:**
- **Assina:** `DataProcessedEvent`
- **Publica em Anomalia:** `AnomalyDetectedEvent` (com informação detalhada da anomalia e pontuações de confiança)
- **Tratamento de Erros:** Lógica de tentativa com backoff exponencial para falhas na publicação de eventos

**Métricas de Performance:**
- Model fitting: ~50ms initialization
- Processing speed: <5ms per sensor reading
- Memory efficiency: Optimal baseline caching
- Error resilience: Zero crashes with malformed data

### ValidationAgent (`apps/agents/core/validation_agent.py`)
**Agente sofisticado de validação de anomalias que fornece análise aprofundada de anomalias detectadas para reduzir falsos positivos e garantir a confiabilidade dos alertas.**

**Papel & Responsabilidades:**
- 🔎 **Processa `AnomalyDetectedEvent`** do `AnomalyDetectionAgent`.
- 📏 **Utiliza `RuleEngine`** para ajustes iniciais de confiança baseados em regras, de acordo com propriedades do alerta e qualidade da leitura do sensor.
- 📊 **Realiza Validação de Contexto Histórico** buscando e analisando dados passados para o sensor específico. Isso inclui checagens configuráveis como 'Estabilidade de Valor Recente' e 'Padrão de Anomalia Recorrente'.
- ⚙️ **Lógica de Validação Configurável** - Lógica detalhada de validação histórica é ajustável via configurações específicas do agente.
- 💯 **Calcula `final_confidence`** combinando ajustes baseados em regras e análise histórica.
- 🤔 **Determina `validation_status`** (ex: "credible_anomaly", "false_positive_suspected", "further_investigation_needed") baseado na confiança final.
- 📤 **Publica `AnomalyValidatedEvent`** contendo detalhes abrangentes: dados do alerta original, dados da leitura que disparou o alerta, todas as razões de validação, confiança final e status determinado.

**Capacidades Avançadas:**
- **Reconhecimento de Padrões Temporais**: Identifica anomalias e padrões recorrentes ao longo do tempo.
- **Redução de Falsos Positivos**: Validação multicamadas sofisticada para filtrar ruído.
- **Análise de Estabilidade de Valor**: Examina a estabilidade de leituras recentes para avaliar a credibilidade da anomalia.
- **Sistema de Pontuação de Confiança**: Ajusta a confiança baseada em múltiplos fatores de validação.
- **Rastreabilidade**: Trilha de auditoria completa do raciocínio de validação para cada anomalia.

**Event Flow:**

- **Subscribes to:** `AnomalyDetectedEvent`
- **Publishes:** `AnomalyValidatedEvent` with comprehensive validation details
- **Integration:** Seamlessly works with downstream decision-making components

### **NOVO: OrchestratorAgent (`apps/agents/core/orchestrator_agent.py`)**
**O agente central de orquestração** que gerencia workflows orientados a eventos e coordena decisões entre todos os agentes do sistema.

**Papel & Responsabilidades:**
- 🎯 **Coordenação Central** - Atua como o ponto central de controle para todos os workflows de manutenção
- 🔄 **Gerenciamento de Estado** - Mantém estado consistente dos workflows ativos e decisões pendentes
- 🎭 **Orquestração de Decisões** - Coordena processo de tomada de decisão entre múltiplos agentes
- ⚡ **Processamento Orientado a Eventos** - Responde a eventos do sistema e orquestra fluxos complexos
- 🧠 **Lógica de Decisão Inteligente** - Determina automaticamente quando ação humana é necessária vs automação
- 📊 **Rastreamento de Correlação** - Mantém contexto completo através de workflows multi-estágio

**Capacidades Avançadas:**
- **Gestão de Workflows Complexos**: Orquestra pipelines de manutenção preditiva de ponta a ponta
- **Tomada de Decisão Baseada em Políticas**: Regras configuráveis para determinar quando requerer aprovação humana
- **Gestão de Estado Robusta**: Mantém estado consistente através de falhas e reinicializações
- **Coordenação Multi-Agente**: Gerencia interações complexas entre DataAcquisition, Anomaly Detection, Validation, Prediction e outros agentes
- **Auditoria Completa**: Registra todas as decisões e transições de estado para rastreabilidade
- **Tolerância a Falhas**: Recuperação graciosa de falhas de componentes e estados inconsistentes

**Event Flow:**

- **Subscribes to:** `AnomalyValidatedEvent`, `MaintenancePredictedEvent`, `HumanDecisionResponseEvent`
- **Publishes:** `HumanDecisionRequiredEvent`, `ScheduleMaintenanceCommand`
- **Integration:** Coordena com HumanInterfaceAgent para aprovações e SchedulingAgent para execução

**Pipeline de Orquestração:**
- Avalia anomalias validadas para determinar urgência e necessidade de aprovação humana
- Gerencia processo de aprovação humana para manutenção urgente (< 30 dias)
- Auto-aprova manutenção não-urgente para eficiência operacional
- Publica comandos de agendamento estruturados para downstream agents
- Mantém estado consistente e logs de auditoria para todas as decisões

### **NOVO: PredictionAgent (`apps/agents/decision/prediction_agent.py`)**
**O agente avançado de manutenção preditiva que usa machine learning para prever falhas de equipamento e gerar recomendações de manutenção.**

**Capacidades Principais:**
- 🔮 **Previsões de Tempo Até a Falha** - Usa a biblioteca Prophet ML do Facebook para previsões precisas
- 📊 **Análise de Dados Históricos** - Analisa padrões de sensores do banco de dados para construir modelos de predição
- 🎯 **Recomendações de Manutenção** - Gera ações de manutenção específicas baseadas na confiança e cronograma da predição
- ⚡ **Processamento em Tempo Real** - Processa anomalias validadas e publica predições de manutenção
- 🧠 **Filtragem Inteligente** - Processa apenas anomalias de alta confiança para focar em ameaças críveis
- 🔄 **Tratamento de Erros Gracioso** - Gerenciamento de erros abrangente para falhas do modelo Prophet e casos extremos

**Funcionalidades Avançadas:**
- **Integração com Modelo Prophet**: Padrão da indústria para previsão de séries temporais com detecção de tendência e sazonalidade
- **Recomendações Baseadas em Confiança**: Diferentes estratégias de manutenção baseadas nos níveis de confiança da predição
- **Consciência do Contexto do Equipamento**: Extrai identificadores de equipamento para agendamento de manutenção direcionado
- **Otimização de Performance**: Preparação de dados e execução de modelo eficientes para cargas de trabalho de produção
- **Logging Abrangente**: Trilhas de auditoria detalhadas para todas as predições e recomendações

**Event Flow:**

- **Subscribes to:** `AnomalyValidatedEvent` (processa manutenção preditiva apenas de anomalias críveis de alta confiança)
- **Publishes:** `MaintenancePredictedEvent` com falhas previstas e recomendações de manutenção
- **Integração:** Permite agendamento proativo de manutenção e planejamento de recursos

**Pipeline de Predição:**
- Busca de dados históricos (mínimo 10 dados pontos requeridos)
- Treinamento do modelo Prophet com dados de séries temporais específicos do sensor
- Cálculo da probabilidade de falha usando análise de tendência
- Geração de recomendação de manutenção baseada em urgência e confiança
- Publicação de evento estruturado com detalhes acionáveis de manutenção

### **NOVO: SchedulingAgent (`apps/agents/decision/scheduling_agent.py`)**
**The intelligent maintenance scheduling agent** that optimizes maintenance task assignments and coordinates with external calendar systems.

**Core Capabilities:**
- 📅 **Maintenance Task Scheduling** - Converts maintenance predictions into optimized schedules
- 👥 **Technician Assignment** - Assigns tasks to available technicians using greedy optimization
- 🔗 **Calendar Integration** - Interfaces with external calendar systems (mock implementation)
- ⚡ **Real-Time Processing** - Processes maintenance predictions and publishes scheduled tasks
- 🎯 **Optimization Logic** - Uses simple greedy assignment with OR-Tools dependency for future enhancements
- 🔄 **Resource Management** - Tracks technician availability and workload distribution

**Advanced Features:**
- **Greedy Assignment Algorithm**: Efficient task-to-technician matching based on availability and skills
- **Calendar Service Integration**: Mock external calendar service for realistic scheduling simulation
- **Optimization Scoring**: Calculates task priority based on failure probability and urgency
- **Workload Balancing**: Distributes maintenance tasks across available technicians
- **Comprehensive Logging**: Detailed audit trails for all scheduling decisions and assignments
- **Error Resilience**: Graceful handling of scheduling conflicts and resource constraints

**Event Flow:**

- **Subscribes to:** `MaintenancePredictedEvent` (processa previsões de manutenção do PredictionAgent)
- **Publica:** `MaintenanceScheduledEvent` com horários otimizados e atribuições de técnicos
- **Integração:** Permite execução coordenada da manutenção e planejamento de recursos

**Pipeline de Agendamento:**
- Criação de solicitação de manutenção a partir de predições
- Avaliação da disponibilidade do técnico
- Otimização da atribuição de tarefas gananciosa
- Integração com calendário para confirmação de agendamento
- Publicação de evento estruturado com detalhes completos do agendamento

### **NOVO: NotificationAgent (`apps/agents/decision/notification_agent.py`)**
**The notification service agent** that handles communication with technicians and stakeholders about maintenance schedules and alerts.

**Core Capabilities:**
- 📨 **Multi-Channel Notifications** - Supports multiple notification channels including console, email, and SMS
- 🔧 **Maintenance Schedule Notifications** - Sends notifications when maintenance is scheduled
- 👤 **Targeted Messaging** - Routes notifications to specific technicians and stakeholders
- 📋 **Template-Based Messages** - Uses customizable message templates for different notification types
- ⚡ **Real-Time Processing** - Processes maintenance schedules and sends immediate notifications
- 🔄 **Provider-Based Architecture** - Extensible notification provider system for different channels

**Advanced Features:**
- **Console Notification Provider**: Immediate console-based notifications for development and testing
- **Template Rendering Engine**: Dynamic message generation with equipment and schedule details
- **Notification Status Tracking**: Comprehensive tracking of notification delivery status
- **Error Resilience**: Graceful handling of notification failures with detailed error reporting
- **Metadata Integration**: Rich notification metadata for debugging and audit trails
- **Extensible Architecture**: Easy integration of new notification channels (email, SMS, webhooks)

**Event Flow:**

- **Subscribes to:** `MaintenanceScheduledEvent` (processa agendamentos de manutenção do SchedulingAgent)
- **Publishes:** None (terminal agent in the notification pipeline)
- **Integration:** Provides communication bridge between automated scheduling and human operators

**Notification Pipeline:**
- Maintenance schedule event processing
- Notification request creation with recipient details
- Message template rendering with schedule information
- Provider-based notification delivery
- Status tracking and error handling with comprehensive logging

**Message Templates:**
- **Successful Scheduling**: "🔧 Maintenance Scheduled: {equipment_id}" with full schedule details
- **Failed Scheduling**: "⚠️ Maintenance Scheduling Failed: {equipment_id}" with constraint information
- **Rich Metadata**: Includes timestamps, technician details, and maintenance context

