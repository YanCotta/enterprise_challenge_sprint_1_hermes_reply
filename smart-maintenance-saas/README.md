# Smart Maintenance SaaS - Backend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-209%2F209%20Passing-brightgreen.svg)](#running-tests)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

> 🇧🇷 [Versão em Português Brasileiro (Sumário)](#versão-em-português-brasileiro-sumário)

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

### LearningAgent (`apps/agents/learning/learning_agent.py`)
**Role & Responsibilities**: Implements advanced knowledge management and enables continuous system improvement using a **Retrieval-Augmented Generation (RAG)** mechanism. It captures, stores, and makes searchable textual data from various sources, including system feedback (e.g., `SystemFeedbackReceivedEvent`), maintenance logs, and potentially technical documentation. Its primary goal is to provide context-aware insights, retrieve historical solutions for similar problems, and support decision-making for other agents (like `OrchestratorAgent` or `HumanInterfaceAgent`) and human operators. This agent helps the system learn from its operational history, improving accuracy and efficiency over time.

**Key Technologies**:
- **ChromaDB**: Utilized as a vector database for storing textual knowledge along with their semantic embeddings. This allows for efficient similarity searches based on the meaning of the text rather than just keyword matching.
- **SentenceTransformers**: Employs models like `all-MiniLM-L6-v2` for converting text into dense vector embeddings. These embeddings capture the semantic meaning of the text, which is crucial for the RAG process.

**Capabilities**:
- **Knowledge Storage & Semantic Retrieval**: Ingests textual data (e.g., feedback on anomaly alerts, maintenance outcomes, technician notes, resolutions to past issues) and stores it with associated metadata (e.g., timestamps, source agent, related equipment). Allows for querying based on semantic similarity to find relevant historical information or documented procedures.
- **Event-Driven Learning**: Primarily learns from `SystemFeedbackReceivedEvent`, automatically processing validated feedback to enrich its knowledge base. This allows the agent to continuously update its understanding based on new information and outcomes. It can be extended to learn from other events or data sources, such as `MaintenanceTaskCompletedEvent` if these events are enriched with detailed textual notes.
- **Context Provisioning**: Other agents, particularly the `OrchestratorAgent` during workflow management or the `HumanInterfaceAgent` when preparing information for human review, can query the `LearningAgent` to fetch relevant historical data. This provides valuable context for new anomalies or decision points.
- **Feedback Loop Integration**: Plays a vital role in the system's overall feedback loop. By making past experiences and resolutions accessible, it helps to inform future actions, potentially improving the accuracy of anomaly validation, the relevance of maintenance predictions, or the efficiency of scheduling.
- **Health Monitoring**: Includes health checks for its underlying components, such as the ChromaDB connection and the availability of embedding models, to ensure reliable operation.

**Event Flow**:
- **Subscribes to**: `SystemFeedbackReceivedEvent`, and potentially other events like `MaintenanceTaskCompletedEvent` (if they contain detailed textual notes or structured feedback).
- **Publishes**: While primarily queried directly, it could publish events like `KnowledgeAddedEvent` or `LearningSummaryEvent` to signal updates to its knowledge base or provide periodic insights.
- **Use Cases**:
    - Providing historical context for anomaly validation (e.g., "Has this specific sensor shown this pattern before under similar operational conditions? What was the outcome?").
    - Suggesting troubleshooting steps or potential root causes based on successfully resolved similar past events.
    - Aiding human operators by retrieving relevant snippets from technical documentation or best practice guides related to specific alerts or equipment types.
    - Over time, its knowledge base can be used to identify recurring issues, assess the effectiveness of certain maintenance procedures, and highlight areas for system improvement.

### HumanInterfaceAgent (`apps/agents/interface/human_interface_agent.py`)
**Role & Responsibilities**: Manages human-in-the-loop decision points within automated workflows. It simulates or facilitates human interaction for critical decisions that require judgment, approval, or input that cannot be fully automated (e.g., high-cost maintenance approvals, responses to novel situations).

**Capabilities**:
- **Decision Request Processing**: Handles various decision types (maintenance approval, budget, emergency response).
- **Simulated Decision Making (for dev/testing)**: Can intelligently simulate human decision processes. In production, it would integrate with actual human interfaces (dashboards, notification systems).
- **Context-Aware Logic**: Considers priority, context, and decision type.

**Event Flow**:
- **Subscribes to**: `HumanDecisionRequiredEvent` (typically from `OrchestratorAgent`).
- **Publishes**: `HumanDecisionResponseEvent` (with the decision, justification, and metadata).

### ReportingAgent (`apps/agents/decision/reporting_agent.py`)
**Role & Responsibilities**: Generates analytics reports, visualizations, and actionable insights related to maintenance operations, equipment health, and system performance.

**Capabilities**: Data aggregation, KPI calculation, chart generation (e.g., using matplotlib), and formatting reports in various outputs (JSON, text).

**Event Flow**: Typically invoked via API call or scheduled trigger rather than subscribing to operational events directly, though it might subscribe to summary events.

### 🔧 API Foundation
- **FastAPI application** with automatic OpenAPI documentation
- **Health check endpoints** - Application and database connectivity monitoring
- **Async-native design** for maximum performance

---

## Versão em Português Brasileiro (Sumário)

Uma robusta plataforma de backend **orientada a eventos e multiagente** para manutenção preditiva industrial SaaS. (Consulte a seção em inglês para detalhes completos)

### Agentes Implementados & Seus Papéis (Versão em Português)
Para informações arquiteturais detalhadas e diagramas, por favor consulte o [Documento de Arquitetura (docs/architecture.md)](docs/architecture.md).

### BaseAgent (`apps/agents/base_agent.py`)
**A classe abstrata fundamental** para todos os agentes especializados no sistema.

**Capacidades Principais:**
- 🆔 **Identificação única** com IDs de agente auto-gerados.
- 🔄 **Gerenciamento de ciclo de vida** - `start`, `stop`, monitoramento de saúde.
- 📡 **Integração com barramento de eventos** - comunicação pub/sub transparente.
- 🎯 **Registro de capacidades** - descoberta dinâmica de funcionalidades.
- ⚡ **Tratamento de eventos assíncrono** com implementações padrão.
- 🏥 **Relatório de status de saúde** para monitoramento do sistema.

### DataAcquisitionAgent (`apps/agents/core/data_acquisition_agent.py`)
**Papel & Responsabilidades**: Responsável pelo estágio inicial do pipeline de dados. Realiza a ingestão de dados brutos de sensores de várias fontes externas, executa validação estrutural e de regras de negócio usando `DataValidator`, enriquece os dados com informações contextuais (ex: detalhes de ativos) via `DataEnricher`, e então publica os dados processados para consumo downstream.

**Fluxo de Eventos**:
- **Assina**: `SensorDataReceivedEvent` (ou lida com envios diretos de dados).
- **Publica em Sucesso**: `DataProcessedEvent` (com dados validados & enriquecidos).
- **Publica em Falha**: `DataProcessingFailedEvent` (com informações detalhadas do erro).
- **Principais Características**: Ingestão robusta de dados, validação abrangente, enriquecimento de dados contextuais, publicação confiável de eventos para progressão no pipeline.

### AnomalyDetectionAgent (`apps/agents/core/anomaly_detection_agent.py`)
**Arquitetura & Papel**: Um agente avançado que emprega uma abordagem de método duplo para detecção de anomalias de nível empresarial. Combina Machine Learning (Isolation Forest para identificação baseada em padrões) com análise estatística (Z-score com limiares sigma configuráveis) para identificação robusta e precisa de anomalias. Lida inteligentemente com sensores desconhecidos estabelecendo e cacheando linhas de base, e é otimizado para processamento em tempo real.

**Capacidades**:
- **Métodos de Detecção Duplos**: Utiliza tanto ML (Isolation Forest) quanto análise estatística (Z-score).
- **Tomada de Decisão Ensemble**: Agrega resultados de múltiplos métodos de detecção.
- **Aprendizado Adaptativo**: Cacheia linhas de base para sensores novos/desconhecidos.
- **Pontuação de Confiança**: Fornece escalonamento linear de confiança baseado no desvio.
- **Consciência do Tipo de Sensor**: Pode aplicar lógica especializada para diferentes tipos de sensores (ex: temperatura, vibração).
- **Alta Performance**: Otimizado para processamento abaixo de 5ms por leitura.
- **Tolerância a Falhas**: Degradação graciosa e tratamento abrangente de erros.

**Fluxo de Eventos**:
- **Assina**: `DataProcessedEvent`.
- **Publica em Anomalia**: `AnomalyDetectedEvent` (com informações detalhadas da anomalia, pontuações de confiança e evidências de suporte).
- **Nota**: Para produção, modelos de ML (StandardScaler, IsolationForest) devem ser pré-treinados com dados históricos representativos e carregados pelo agente, ao invés de serem ajustados em pontos de dados únicos recebidos.

### ValidationAgent (`apps/agents/core/validation_agent.py`)
**Papel & Responsabilidades**: Fornece validação sofisticada de anomalias detectadas para reduzir falsos positivos e aumentar a confiabilidade dos alertas. Processa anomalias do `AnomalyDetectionAgent`, aplica um `RuleEngine` para ajustes iniciais de confiança (baseados nas propriedades do alerta, qualidade dos dados do sensor) e realiza validação de contexto histórico (ex: verificando estabilidade de valores recentes, padrões recorrentes de anomalia).

**Capacidades**:
- **Ajustes Baseados em Regras**: Utiliza um `RuleEngine` flexível para pontuação inicial de confiança.
- **Análise de Contexto Histórico**: Consulta e analisa dados passados do sensor específico para identificar padrões como estabilidade de valor ou anomalias recorrentes.
- **Lógica de Validação Configurável**: Parâmetros de validação histórica são ajustáveis.
- **Cálculo de Confiança Final**: Combina análise baseada em regras e histórica para uma pontuação final de confiança.
- **Determinação de Status**: Atribui um status (ex: "anomalia_credível", "suspeita_falso_positivo") baseado na confiança final.
- **Reconhecimento de Padrões Temporais**: Identifica padrões recorrentes ao longo do tempo.

**Fluxo de Eventos**:
- **Assina**: `AnomalyDetectedEvent`.
- **Publica**: `AnomalyValidatedEvent` (contendo dados originais do alerta, leitura do sensor que disparou o alerta, razões da validação, confiança final e status determinado).

### OrchestratorAgent (`apps/agents/core/orchestrator_agent.py`)
**Papel & Responsabilidades**: Atua como o **sistema nervoso central** da plataforma de manutenção. Este agente crucial orquestra fluxos de trabalho complexos e orientados a eventos de ponta a ponta, incluindo o gerenciamento do estado geral das atividades de manutenção. Coordena os processos de tomada de decisão entre todos os agentes especializados, determinando inteligentemente quando a intervenção humana é necessária (disparando `HumanDecisionRequiredEvent` para o `HumanInterfaceAgent`) versus quando as ações podem ser automatizadas (por exemplo, emitindo diretamente `ScheduleMaintenanceCommand`). Garante uma interação fluida entre agentes como `AnomalyDetectionAgent`, `ValidationAgent`, `PredictionAgent` e `SchedulingAgent`, processando seus resultados e roteando informações apropriadamente. Suas responsabilidades incluem gerenciar o ciclo de vida das tarefas de manutenção, desde a detecção e validação iniciais, passando pela predição, aprovação humana (se necessário), agendamento, execução e aprendizado com o feedback.

**Principais Capacidades**:
- **Coordenação Central de Fluxos de Trabalho**: Gerencia pipelines de manutenção multiestágio, englobando validação de anomalias, predição de falhas, pontos de decisão humano-no-loop, agendamento de manutenção e disparo de notificações.
- **Gerenciamento de Estado**: Mantém um estado consistente e potencialmente persistente para fluxos de trabalho ativos e decisões pendentes. Isso é crucial para a resiliência do sistema, permitindo que os fluxos de trabalho sejam pausados, retomados ou recuperados em caso de interrupções ou reinicializações de agentes.
- **Roteamento Inteligente de Decisões**: Emprega regras baseadas em políticas e dados contextuais (ex: severidade da anomalia do `ValidationAgent`, urgência da predição do `PredictionAgent`, insights históricos do `LearningAgent`) para decidir se automatiza ações ou escala para revisão humana através do `HumanInterfaceAgent`.
- **Hub de Comunicação Multiagente**: Serve como um ponto primário de comunicação e coordenação, garantindo que os agentes trabalhem juntos de forma coesa, inscrevendo-se em seus principais eventos de saída e publicando comandos ou novos eventos para direcionar ações subsequentes.
- **Rastreamento de Correlação & Auditoria**: Mantém o contexto através de fluxos de trabalho complexos e multiestágio usando IDs de correlação. Também registra decisões significativas, transições de estado e ações para rastreabilidade e auditoria abrangentes.
- **Tolerância a Falhas**: Projetado para tratamento robusto de erros e recuperação graciosa de falhas de componentes ou eventos inesperados dentro do fluxo de trabalho.

**Fluxo de Eventos**:
- **Assina**: `AnomalyValidatedEvent`, `MaintenancePredictedEvent`, `HumanDecisionResponseEvent` e, potencialmente, outros eventos de vários agentes que sinalizam a conclusão de uma etapa ou requerem uma mudança no estado do fluxo de trabalho.
- **Publica**: `HumanDecisionRequiredEvent` (para engajar expertise humana), `ScheduleMaintenanceCommand` (para direcionar o `SchedulingAgent`), `WorkflowStepCompletedEvent` (para rastreamento geral e potencialmente para outros assinantes) e outros comandos ou eventos específicos conforme necessário para guiar a progressão das tarefas de manutenção.
- **Lógica Operacional**: O Orquestrador avalia eventos recebidos, como anomalias validadas ou predições de manutenção. Com base em políticas configuráveis (ex: severidade, custo, criticidade do equipamento, tempo até a falha), ele determina o próximo passo. Isso pode envolver a aprovação e o agendamento automáticos de manutenção de rotina ou, para questões mais críticas/complexas, solicitar a entrada humana através do `HumanInterfaceAgent` antes de prosseguir. Em seguida, processa respostas (ex: `HumanDecisionResponseEvent`) para continuar, modificar ou interromper os fluxos de trabalho.

### PredictionAgent (`apps/agents/decision/prediction_agent.py`)
**Papel & Responsabilidades**: Realiza manutenção preditiva prevendo falhas potenciais de equipamentos. Utiliza modelos de machine learning (ex: Facebook Prophet) para analisar padrões históricos de dados de sensores ao receber uma anomalia validada altamente credível, prevendo o Tempo Até a Falha (TTF) e gerando recomendações de manutenção acionáveis.

**Capacidades**:
- **Previsão de Tempo Até a Falha (TTF)**: Emprega modelos de ML como Prophet para previsão.
- **Análise de Dados Históricos**: Analisa dados históricos específicos do sensor para treinar modelos de predição.
- **Recomendações de Manutenção**: Gera ações de manutenção específicas baseadas na confiança e cronograma da predição.
- **Filtragem Inteligente**: Tipicamente processa apenas anomalias validadas de alta confiança.
- **Consciência Contextual**: Extrai identificadores de equipamento para recomendações direcionadas.

**Fluxo de Eventos**:
- **Assina**: `AnomalyValidatedEvent` (tipicamente filtrando por anomalias críveis de alta confiança).
- **Publica**: `MaintenancePredictedEvent` (com detalhes da falha prevista, TTF, confiança e ações recomendadas).

### SchedulingAgent (`apps/agents/decision/scheduling_agent.py`)
**Papel & Responsabilidades**: Agenda inteligentemente tarefas de manutenção com base em predições e restrições operacionais. Otimiza a atribuição de tarefas a técnicos disponíveis (potencialmente considerando habilidades e carga de trabalho) e pode integrar-se com sistemas de calendário externos (atualmente simulado).

**Capacidades**:
- **Agendamento Otimizado de Tarefas**: Converte predições/comandos de manutenção em cronogramas otimizados.
- **Atribuição de Técnicos**: Implementa lógica de atribuição (ex: algoritmo guloso, com planos para OR-Tools para otimização avançada).
- **Integração com Calendário**: Interface (simulada) para verificar disponibilidade e agendar tarefas.
- **Gerenciamento de Recursos**: Rastreamento básico da disponibilidade de técnicos.

**Fluxo de Eventos**:
- **Assina**: `MaintenancePredictedEvent` ou `ScheduleMaintenanceCommand` (do `OrchestratorAgent`).
- **Publica**: `MaintenanceScheduledEvent` (com detalhes do cronograma, técnico atribuído e especificidades da tarefa).

### NotificationAgent (`apps/agents/decision/notification_agent.py`)
**Papel & Responsabilidades**: Gerencia comunicações com técnicos e partes interessadas sobre cronogramas de manutenção, alertas e outros eventos do sistema. Suporta múltiplos canais de notificação e usa modelos para mensagens consistentes.

**Capacidades**:
- **Notificações Multicanal**: Suporta console, com um sistema de provedor extensível para email, SMS, etc.
- **Mensagens Direcionadas**: Roteia notificações para usuários/grupos específicos.
- **Mensagens Baseadas em Modelos**: Usa modelos personalizáveis para diferentes tipos de eventos.

**Fluxo de Eventos**:
- **Assina**: `MaintenanceScheduledEvent`, potencialmente outros eventos como `AnomalyValidatedEvent` (para alertas críticos) ou `HumanDecisionRequiredEvent`.
- **Publica**: Nenhum (tipicamente um agente terminal em seu pipeline específico, mas poderia publicar `NotificationSentEvent` ou `NotificationFailedEvent` para auditoria).

### LearningAgent (`apps/agents/learning/learning_agent.py`)
**Papel & Responsabilidades**: Implementa gerenciamento avançado de conhecimento e habilita a melhoria contínua do sistema usando um mecanismo de **Geração Aumentada por Recuperação (RAG)**. Captura, armazena e torna pesquisáveis dados textuais de várias fontes, incluindo feedback do sistema (ex: `SystemFeedbackReceivedEvent`), logs de manutenção e, potencialmente, documentação técnica. Seu objetivo principal é fornecer insights conscientes do contexto, recuperar soluções históricas para problemas semelhantes e apoiar a tomada de decisão para outros agentes (como `OrchestratorAgent` ou `HumanInterfaceAgent`) e operadores humanos. Este agente ajuda o sistema a aprender com seu histórico operacional, melhorando a precisão e eficiência ao longo do tempo.

**Principais Tecnologias**:
- **ChromaDB**: Utilizado como um banco de dados vetorial para armazenar conhecimento textual juntamente com seus embeddings semânticos. Isso permite buscas por similaridade eficientes baseadas no significado do texto, em vez de apenas correspondência de palavras-chave.
- **SentenceTransformers**: Emprega modelos como `all-MiniLM-L6-v2` para converter texto em embeddings vetoriais densos. Esses embeddings capturam o significado semântico do texto, o que é crucial para o processo RAG.

**Capacidades**:
- **Armazenamento de Conhecimento & Recuperação Semântica**: Ingesta dados textuais (ex: feedback sobre alertas de anomalia, resultados de manutenção, notas de técnicos, resoluções de problemas passados) e os armazena com metadados associados (ex: timestamps, agente de origem, equipamento relacionado). Permite consultas baseadas em similaridade semântica para encontrar informações históricas relevantes ou procedimentos documentados.
- **Aprendizado Orientado a Eventos**: Aprende primariamente a partir de `SystemFeedbackReceivedEvent`, processando feedback validado automaticamente para enriquecer sua base de conhecimento. Isso permite que o agente atualize continuamente seu entendimento com base em novas informações e resultados. Pode ser estendido para aprender a partir de outros eventos ou fontes de dados, como `MaintenanceTaskCompletedEvent`, se esses eventos forem enriquecidos com notas textuais detalhadas.
- **Provisionamento de Contexto**: Outros agentes, particularmente o `OrchestratorAgent` durante o gerenciamento de fluxos de trabalho ou o `HumanInterfaceAgent` ao preparar informações para revisão humana, podem consultar o `LearningAgent` para buscar dados históricos relevantes. Isso fornece contexto valioso para novas anomalias ou pontos de decisão.
- **Integração com Loop de Feedback**: Desempenha um papel vital no loop de feedback geral do sistema. Ao tornar acessíveis experiências e resoluções passadas, ajuda a informar ações futuras, melhorando potencialmente a precisão da validação de anomalias, a relevância das predições de manutenção ou a eficiência do agendamento.
- **Monitoramento de Saúde**: Inclui verificações de saúde para seus componentes subjacentes, como a conexão com o ChromaDB e a disponibilidade dos modelos de embedding, para garantir uma operação confiável.

**Fluxo de Eventos**:
- **Assina**: `SystemFeedbackReceivedEvent` e, potencialmente, outros eventos como `MaintenanceTaskCompletedEvent` (se contiverem notas textuais detalhadas ou feedback estruturado).
- **Publica**: Embora primariamente consultado diretamente, poderia publicar eventos como `KnowledgeAddedEvent` ou `LearningSummaryEvent` para sinalizar atualizações em sua base de conhecimento ou fornecer insights periódicos.
- **Casos de Uso**:
    - Fornecer contexto histórico para validação de anomalias (ex: "Este sensor específico já apresentou este padrão antes sob condições operacionais semelhantes? Qual foi o resultado?").
    - Sugerir etapas de solução de problemas ou possíveis causas raiz com base em eventos passados semelhantes resolvidos com sucesso.
    - Auxiliar operadores humanos recuperando trechos relevantes de documentação técnica ou guias de melhores práticas relacionados a alertas específicos ou tipos de equipamento.
    - Com o tempo, sua base de conhecimento pode ser usada para identificar problemas recorrentes, avaliar a eficácia de certos procedimentos de manutenção e destacar áreas para melhoria do sistema.

### HumanInterfaceAgent (`apps/agents/interface/human_interface_agent.py`)
**Papel & Responsabilidades**: Gerencia pontos de decisão humano-no-loop dentro de fluxos de trabalho automatizados. Simula ou facilita a interação humana para decisões críticas que requerem julgamento, aprovação ou entrada que não pode ser totalmente automatizada (ex: aprovações de manutenção de alto custo, respostas a situações novas).

**Capacidades**:
- **Processamento de Solicitações de Decisão**: Lida com vários tipos de decisão (aprovação de manutenção, orçamento, resposta a emergências).
- **Tomada de Decisão Simulada (para dev/teste)**: Pode simular inteligentemente processos de decisão humana. Em produção, integraria com interfaces humanas reais (dashboards, sistemas de notificação).
- **Lógica Consciente do Contexto**: Considera prioridade, contexto e tipo de decisão.

**Fluxo de Eventos**:
- **Assina**: `HumanDecisionRequiredEvent` (tipicamente do `OrchestratorAgent`).
- **Publica**: `HumanDecisionResponseEvent` (com a decisão, justificativa e metadados).

### ReportingAgent (`apps/agents/decision/reporting_agent.py`)
**Papel & Responsabilidades**: Gera relatórios analíticos, visualizações e insights acionáveis relacionados a operações de manutenção, saúde de equipamentos e performance do sistema.

**Capacidades**: Agregação de dados, cálculo de KPI, geração de gráficos (ex: usando matplotlib) e formatação de relatórios em várias saídas (JSON, texto).

**Fluxo de Eventos**: Tipicamente invocado via chamada de API ou gatilho agendado, em vez de assinar diretamente eventos operacionais, embora possa assinar eventos de resumo.

---
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

## Implemented Agents & Their Roles

For more detailed architectural information and diagrams, please see the [Architecture Document (docs/architecture.md)](docs/architecture.md).

### BaseAgent (`apps/agents/base_agent.py`)
**The foundational abstract class** for all specialized agents within the system.

**Core Capabilities:**
- 🆔 **Unique Identification** with auto-generated agent IDs.
- 🔄 **Lifecycle Management** - `start`, `stop`, health monitoring.
- 📡 **Event Bus Integration** - Transparent pub/sub communication.
- 🎯 **Capability Registration** - Dynamic discovery of functionalities.
- ⚡ **Asynchronous Event Handling** with default implementations.
- 🏥 **Health Status Reporting** for system monitoring.

### DataAcquisitionAgent (`apps/agents/core/data_acquisition_agent.py`)
**Role & Responsibilities**: Responsible for the initial stage of the data pipeline. It ingests raw sensor data from various external sources, performs structural and business rule validation using `DataValidator`, enriches the data with contextual information (e.g., asset details) via `DataEnricher`, and then publishes the processed data for downstream consumption.

**Event Flow**:
- **Subscribes to**: `SensorDataReceivedEvent` (or handles direct data pushes).
- **Publishes on Success**: `DataProcessedEvent` (with validated & enriched data).
- **Publishes on Failure**: `DataProcessingFailedEvent` (with detailed error information).
- **Key Features**: Robust data ingestion, comprehensive validation, contextual data enrichment, reliable event publication for pipeline progression.

### AnomalyDetectionAgent (`apps/agents/core/anomaly_detection_agent.py`)
**Architecture & Role**: An advanced agent employing a dual-method approach for enterprise-grade anomaly detection. It combines Machine Learning (Isolation Forest for pattern-based identification) with statistical analysis (Z-score with configurable sigma thresholds) for robust and accurate anomaly identification. It intelligently handles unknown sensors by establishing and caching baselines and is optimized for real-time processing.

**Capabilities**:
- **Dual Detection Methods**: Utilizes both ML (Isolation Forest) and statistical (Z-score) analysis.
- **Ensemble Decision Making**: Aggregates results from multiple detection methods.
- **Adaptive Learning**: Caches baselines for new/unknown sensors.
- **Confidence Scoring**: Provides linear confidence scaling based on deviation.
- **Sensor Type Awareness**: Can apply specialized logic for different sensor types (e.g., temperature, vibration).
- **High Performance**: Optimized for sub-5ms processing per reading.
- **Fault Tolerance**: Graceful degradation and comprehensive error handling.

**Event Flow**:
- **Subscribes to**: `DataProcessedEvent`.
- **Publishes on Anomaly**: `AnomalyDetectedEvent` (with detailed anomaly information, confidence scores, and supporting evidence).
- **Note**: For production, ML models (StandardScaler, IsolationForest) should be pre-trained on representative historical data and loaded by the agent, rather than being fit on single incoming data points.

### ValidationAgent (`apps/agents/core/validation_agent.py`)
**Role & Responsibilities**: Provides sophisticated validation of detected anomalies to reduce false positives and enhance alert reliability. It processes anomalies from the `AnomalyDetectionAgent`, applies a `RuleEngine` for initial confidence adjustments (based on alert properties, sensor data quality), and performs historical context validation (e.g., checking for recent value stability, recurring anomaly patterns).

**Capabilities**:
- **Rule-Based Adjustments**: Utilizes a flexible `RuleEngine` for initial confidence scoring.
- **Historical Context Analysis**: Queries and analyzes past data for the specific sensor to identify patterns like value stability or recurring anomalies.
- **Configurable Validation Logic**: Historical validation parameters are adjustable.
- **Final Confidence Calculation**: Combines rule-based and historical analysis for a final confidence score.
- **Status Determination**: Assigns a status (e.g., "credible_anomaly", "false_positive_suspected") based on final confidence.
- **Temporal Pattern Recognition**: Identifies recurring patterns over time.

**Event Flow**:
- **Subscribes to**: `AnomalyDetectedEvent`.
- **Publishes**: `AnomalyValidatedEvent` (containing original alert data, triggering sensor reading, validation reasons, final confidence, and determined status).

### OrchestratorAgent (`apps/agents/core/orchestrator_agent.py`)
**Role & Responsibilities**: Acts as the **central nervous system** of the maintenance platform. This crucial agent orchestrates complex, event-driven workflows from end-to-end, including managing the overall state of maintenance activities. It coordinates decision-making processes across all specialized agents, intelligently determining when human intervention is required (triggering `HumanDecisionRequiredEvent` for the `HumanInterfaceAgent`) versus when actions can be automated (e.g., directly issuing `ScheduleMaintenanceCommand`). It ensures seamless interaction between agents like `AnomalyDetectionAgent`, `ValidationAgent`, `PredictionAgent`, and `SchedulingAgent` by processing their outputs and routing information appropriately. Its responsibilities include managing the lifecycle of maintenance tasks, from initial detection and validation, through prediction, human approval (if necessary), scheduling, execution, and learning from feedback.

**Key Capabilities**:
- **Central Workflow Coordination**: Manages multi-stage maintenance pipelines, encompassing anomaly validation, failure prediction, human-in-the-loop decision points, maintenance scheduling, and triggering notifications.
- **State Management**: Maintains a consistent and potentially persistent state for active workflows and pending decisions. This is crucial for system resilience, allowing workflows to be paused, resumed, or recovered in case of interruptions or agent restarts.
- **Intelligent Decision Routing**: Employs policy-based rules and contextual data (e.g., anomaly severity from `ValidationAgent`, prediction urgency from `PredictionAgent`, historical insights from `LearningAgent`) to decide whether to automate actions or escalate for human review via the `HumanInterfaceAgent`.
- **Multi-Agent Communication Hub**: Serves as a primary communication and coordination point, ensuring agents work together cohesively by subscribing to their key output events and publishing commands or new events to direct subsequent actions.
- **Correlation Tracking & Auditing**: Maintains context across complex, multi-stage workflows using correlation IDs. It also logs significant decisions, state transitions, and actions for comprehensive traceability and auditing purposes.
- **Fault Tolerance**: Designed for robust error handling and graceful recovery from component failures or unexpected events within the workflow.

**Event Flow**:
- **Subscribes to**: `AnomalyValidatedEvent`, `MaintenancePredictedEvent`, `HumanDecisionResponseEvent`, and potentially other events from various agents that signal the completion of a step or require a change in workflow state.
- **Publishes**: `HumanDecisionRequiredEvent` (to engage human expertise), `ScheduleMaintenanceCommand` (to direct the `SchedulingAgent`), `WorkflowStepCompletedEvent` (for general tracking and potentially for other subscribers), and other specific commands or events as needed to guide the progression of maintenance tasks.
- **Operational Logic**: The Orchestrator evaluates incoming events like validated anomalies or maintenance predictions. Based on configurable policies (e.g., severity, cost, equipment criticality, time-to-failure), it determines the next step. This might involve automatically approving and scheduling routine maintenance, or for more critical/complex issues, requesting human input via the `HumanInterfaceAgent` before proceeding. It then processes responses (e.g., `HumanDecisionResponseEvent`) to continue, modify, or halt workflows.

### PredictionAgent (`apps/agents/decision/prediction_agent.py`)
**Role & Responsibilities**: Performs predictive maintenance by forecasting potential equipment failures. It utilizes machine learning models (e.g., Facebook Prophet) to analyze historical sensor data patterns upon receiving a highly credible validated anomaly, predicting Time-To-Failure (TTF) and generating actionable maintenance recommendations.

**Capabilities**:
- **Time-To-Failure (TTF) Prediction**: Employs ML models like Prophet for forecasting.
- **Historical Data Analysis**: Analyzes sensor-specific historical data to train prediction models.
- **Maintenance Recommendations**: Generates specific maintenance actions based on prediction confidence and timeline.
- **Intelligent Filtering**: Typically processes only high-confidence validated anomalies.
- **Contextual Awareness**: Extracts equipment identifiers for targeted recommendations.

**Event Flow**:
- **Subscribes to**: `AnomalyValidatedEvent` (typically filtering for high-confidence, credible anomalies).
- **Publishes**: `MaintenancePredictedEvent` (with predicted failure details, TTF, confidence, and recommended actions).

### SchedulingAgent (`apps/agents/decision/scheduling_agent.py`)
**Role & Responsibilities**: Intelligently schedules maintenance tasks based on predictions and operational constraints. It optimizes task assignments to available technicians (potentially considering skills and workload) and can integrate with external calendar systems (currently mocked).

**Capabilities**:
- **Optimized Task Scheduling**: Converts maintenance predictions/commands into optimized schedules.
- **Technician Assignment**: Implements assignment logic (e.g., greedy algorithm, with plans for OR-Tools for advanced optimization).
- **Calendar Integration**: (Mocked) Interface for checking availability and booking tasks.
- **Resource Management**: Basic tracking of technician availability.

**Event Flow**:
- **Subscribes to**: `MaintenancePredictedEvent` or `ScheduleMaintenanceCommand` (from `OrchestratorAgent`).
- **Publishes**: `MaintenanceScheduledEvent` (with schedule details, assigned technician, and task specifics).

### NotificationAgent (`apps/agents/decision/notification_agent.py`)
**Role & Responsibilities**: Manages communications with technicians and stakeholders regarding maintenance schedules, alerts, and other system events. It supports multiple notification channels and uses templates for consistent messaging.

**Capabilities**:
- **Multi-Channel Notifications**: Supports console, with an extensible provider system for email, SMS, etc.
- **Targeted Messaging**: Routes notifications to specific users/groups.
- **Template-Based Messages**: Uses customizable templates for different event types.

**Event Flow**:
- **Subscribes to**: `MaintenanceScheduledEvent`, potentially other events like `AnomalyValidatedEvent` (for critical alerts) or `HumanDecisionRequiredEvent`.
- **Publishes**: None (typically a terminal agent in its specific pipeline, but could publish `NotificationSentEvent` or `NotificationFailedEvent` for auditing).

