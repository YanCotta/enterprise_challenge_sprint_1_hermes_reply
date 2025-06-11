# Smart Maintenance SaaS - API Documentation

🇧🇷 **[Clique aqui para ler em Português](#-smart-maintenance-saas---documentação-da-api-português)** | 🇺🇸 **English Version Below**

## 📚 Documentation Navigation

This document is part of the Smart Maintenance SaaS documentation suite. For complete system understanding, please also refer to:

- **[Backend README](../README.md)** - Docker deployment and getting started guide
- **[System Screenshots](./SYSTEM_SCREENSHOTS.md)** - Complete visual system walkthrough with screenshots
- **[System and Architecture](./SYSTEM_AND_ARCHITECTURE.md)** - Complete system architecture and component overview
- **[Future Roadmap](./FUTURE_ROADMAP.md)** - Strategic vision and planned enhancements
- **[Deployment Status](./DEPLOYMENT_STATUS.md)** - Current deployment status and container information
- **[Performance Baseline](./PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics baseline
- **[Load Testing Instructions](./LOAD_TESTING_INSTRUCTIONS.md)** - Comprehensive guide for running performance tests
- **[Original Architecture](./original_full_system_architecture.md)** - Complete Phase 1 documentation and initial system design
- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Logging Configuration](../core/logging_config.md)** - Structured JSON logging setup and configuration
- **[Configuration Management](../core/config/README.md)** - Centralized configuration system using Pydantic BaseSettings
- **[Project Overview](../../README.md)** - High-level project description and objectives

---

## Overview

The Smart Maintenance SaaS API provides a comprehensive RESTful interface for industrial predictive maintenance operations. The API is built with FastAPI and follows OpenAPI 3.0 standards, offering automatic documentation and validation.

**Base URL**: `http://localhost:8000` (Docker deployment)  
**API Version**: v1  
**Production Status**: ✅ Ready  
**Documentation**: 
- Interactive API Docs: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

## Quick Start with Docker

```bash
# Start the complete system
docker compose up -d

# Access points
# API: http://localhost:8000
# UI: http://localhost:8501
# Docs: http://localhost:8000/docs
```

## Control Panel UI

For easy interaction with the API, a Streamlit-based control panel is available at `http://localhost:8501`. The control panel provides:

- **Visual forms** for all API endpoints
- **Real-time validation** and error handling  
- **System health monitoring** and connectivity checks
- **Quick testing tools** for rapid API exploration

When using Docker: The UI is automatically available at `http://localhost:8501` when you run `docker compose up -d`.

See the [Backend README](../README.md#control-panel-ui-streamlit) for detailed usage instructions.

## Authentication

All API endpoints require authentication via API key. Include the API key in the request header:

```http
X-API-Key: your-api-key-here
```

### API Key Scopes

The API uses a scope-based permission system:

- `data:ingest` - Permission to ingest sensor data
- `reports:generate` - Permission to generate reports
- `tasks:update` - Permission to submit human decisions

## Core Endpoints

### Data Ingestion

#### POST /api/v1/data/ingest

Ingests sensor data into the Smart Maintenance system for processing and analysis.

**Request Body:**
```json
{
  "sensor_id": "TEMP_001",
  "value": 25.5,
  "sensor_type": "temperature",
  "unit": "celsius",
  "location": "Factory Floor A",
  "timestamp": "2025-06-11T10:30:00Z"
}
```

**Response (200 OK):**
```json
{
  "message": "Data ingested successfully",
  "timestamp": "2025-06-11T10:30:00Z",
  "sensor_id": "TEMP_001",
  "correlation_id": "req_123456789"
}
```

**Sensor Types Supported:**
- `temperature`
- `vibration` 
- `pressure`
- `humidity`
- `current`
- `voltage`

### Reports Generation

#### POST /api/v1/reports/generate

Generates various maintenance and system reports based on the specified report type.

**Request Body:**
```json
{
  "report_type": "anomaly_summary",
  "start_date": "2025-05-11",
  "end_date": "2025-06-11",
  "output_format": "json",
  "include_charts": false
}
```

**Response (200 OK):**
```json
{
  "report_id": "rpt_987654321",
  "report_type": "anomaly_summary",
  "generated_at": "2025-06-11T10:30:00Z",
  "report_data": {
    "summary": "Anomaly analysis for the past 30 days",
    "total_anomalies": 15,
    "critical_anomalies": 3,
    "anomalies_by_type": {
      "temperature": 8,
      "vibration": 5,
      "pressure": 2
    }
  },
  "metadata": {
    "date_range": "2025-05-11 to 2025-06-11",
    "total_sensors": 45,
    "data_points_analyzed": 12450
  }
}
```

**Report Types Available:**
- `anomaly_summary` - Summary of detected anomalies
- `system_health` - Overall system health report
- `maintenance_summary` - Maintenance activities summary
- `performance_summary` - System performance metrics

### Human Decision Submission

#### POST /api/v1/decisions/submit

Submits human feedback or decisions on system-prompted queries for maintenance approval/rejection.

**Request Body:**
```json
{
  "request_id": "req_maintenance_123",
  "decision": "approve",
  "justification": "Critical equipment requires immediate attention",
  "submitted_by": "operator_001"
}
```

**Response (200 OK):**
```json
{
  "message": "Decision submitted successfully",
  "request_id": "req_maintenance_123",
  "decision": "approve",
  "timestamp": "2025-06-11T10:30:00Z",
  "status": "processed"
}
```

**Decision Options:**
- `approve` - Approve the maintenance request
- `reject` - Reject the maintenance request
- `defer` - Defer the decision for later review

## Health Check Endpoints

### GET /health

Basic health check endpoint to verify API availability.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T10:30:00Z",
  "version": "v1.0.0"
}
```

### GET /health/detailed

Detailed health check including database and service status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T10:30:00Z",
  "services": {
    "database": "healthy",
    "event_bus": "healthy",
    "ml_services": "healthy"
  },
  "version": "v1.0.0"
}
```

## Error Handling

The API uses standard HTTP status codes and returns structured error responses:

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request body is invalid",
    "details": {
      "field": "sensor_id",
      "issue": "This field is required"
    }
  },
  "timestamp": "2025-06-11T10:30:00Z",
  "request_id": "req_error_123"
}
```

### Common Error Codes

- `400 Bad Request` - Invalid request format or missing required fields
- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Insufficient permissions for the requested operation
- `404 Not Found` - Requested resource not found
- `422 Unprocessable Entity` - Request validation failed
- `500 Internal Server Error` - Unexpected server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Data Ingestion**: 100 requests per minute per API key
- **Report Generation**: 10 requests per minute per API key
- **Decision Submission**: 50 requests per minute per API key

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623456789
```

## Examples

### Complete Data Ingestion Workflow

```bash
# 1. Ingest sensor data
curl -X POST "http://localhost:8000/api/v1/data/ingest" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "TEMP_001",
    "value": 85.5,
    "sensor_type": "temperature",
    "unit": "celsius",
    "location": "Factory Floor A"
  }'

# 2. Generate anomaly report
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "anomaly_summary",
    "start_date": "2025-05-11",
    "end_date": "2025-06-11"
  }'

# 3. Submit maintenance decision
curl -X POST "http://localhost:8000/api/v1/decisions/submit" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_maintenance_123",
    "decision": "approve",
    "justification": "Temperature anomaly requires immediate attention"
  }'
```

---

## 🇧🇷 Smart Maintenance SaaS - Documentação da API (Português)

### 📚 Navegação da Documentação

Este documento faz parte do conjunto de documentação do Smart Maintenance SaaS. Para compreensão completa do sistema, consulte também:

- **[README do Backend](../README.md)** - Implantação Docker e guia de primeiros passos
- **[Capturas de Tela do Sistema](./SYSTEM_SCREENSHOTS.md)** - Demonstração visual completa do sistema com capturas de tela
- **[Sistema e Arquitetura](./SYSTEM_AND_ARCHITECTURE.md)** - Visão geral completa da arquitetura e componentes do sistema
- **[Roadmap Futuro](./FUTURE_ROADMAP.md)** - Visão estratégica e melhorias planejadas
- **[Status de Implantação](./DEPLOYMENT_STATUS.md)** - Status atual de implantação e informações do container
- **[Baseline de Performance](./PERFORMANCE_BASELINE.md)** - Resultados de testes de carga e métricas de performance
- **[Instruções de Teste de Carga](./LOAD_TESTING_INSTRUCTIONS.md)** - Guia abrangente para execução de testes de performance
- **[Arquitetura Original](./original_full_system_architecture.md)** - Documentação completa da Fase 1 e design inicial do sistema
- **[Documentação de Testes](../tests/README.md)** - Organização e guia de execução de testes
- **[Configuração de Logging](../core/logging_config.md)** - Configuração de logging JSON estruturado
- **[Gerenciamento de Configuração](../core/config/README.md)** - Sistema centralizado de configuração usando Pydantic BaseSettings
- **[Visão Geral do Projeto](../../README.md)** - Descrição de alto nível e objetivos do projeto

---

## Visão Geral

A API Smart Maintenance SaaS fornece uma interface RESTful abrangente para operações de manutenção preditiva industrial. A API é construída com FastAPI e segue os padrões OpenAPI 3.0, oferecendo documentação e validação automáticas.

**URL Base**: `http://localhost:8000` (implantação Docker)  
**Versão da API**: v1  
**Status de Produção**: ✅ Pronto  
**Documentação**: 
- Documentação Interativa da API: `http://localhost:8000/docs`
- Documentação ReDoc: `http://localhost:8000/redoc`

## Início Rápido com Docker

```bash
# Inicie o sistema completo
docker compose up -d

# Pontos de acesso
# API: http://localhost:8000
# UI: http://localhost:8501
# Docs: http://localhost:8000/docs
```

## Interface do Painel de Controle

Para interação fácil com a API, um painel de controle baseado em Streamlit está disponível em `http://localhost:8501`. O painel de controle fornece:

- **Formulários visuais** para todos os endpoints da API
- **Validação em tempo real** e tratamento de erros
- **Monitoramento de saúde do sistema** e verificações de conectividade
- **Ferramentas de teste rápido** para exploração rápida da API

Ao usar Docker: A UI fica automaticamente disponível em `http://localhost:8501` quando você executa `docker compose up -d`.

Consulte o [README do Backend](../README.md#control-panel-ui-streamlit) para instruções detalhadas de uso.

## Autenticação

Todos os endpoints da API requerem autenticação via chave API. Inclua a chave API no cabeçalho da requisição:

```http
X-API-Key: sua-chave-api-aqui
```

### Escopos da Chave API

A API usa um sistema de permissões baseado em escopo:

- `data:ingest` - Permissão para ingerir dados de sensores
- `reports:generate` - Permissão para gerar relatórios
- `tasks:update` - Permissão para submeter decisões humanas

## Endpoints Principais

### Ingestão de Dados

#### POST /api/v1/data/ingest

Ingere dados de sensores no sistema Smart Maintenance para processamento e análise.

**Corpo da Requisição:**
```json
{
  "sensor_id": "TEMP_001",
  "value": 25.5,
  "sensor_type": "temperature",
  "unit": "celsius",
  "location": "Piso da Fábrica A",
  "timestamp": "2025-06-11T10:30:00Z"
}
```

**Resposta (200 OK):**
```json
{
  "message": "Dados ingeridos com sucesso",
  "timestamp": "2025-06-11T10:30:00Z",
  "sensor_id": "TEMP_001",
  "correlation_id": "req_123456789"
}
```

**Tipos de Sensor Suportados:**
- `temperature` (temperatura)
- `vibration` (vibração)
- `pressure` (pressão)
- `humidity` (umidade)
- `current` (corrente)
- `voltage` (voltagem)

### Geração de Relatórios

#### POST /api/v1/reports/generate

Gera vários relatórios de manutenção e sistema baseados no tipo de relatório especificado.

**Corpo da Requisição:**
```json
{
  "report_type": "anomaly_summary",
  "start_date": "2025-05-11",
  "end_date": "2025-06-11",
  "output_format": "json",
  "include_charts": false
}
```

**Resposta (200 OK):**
```json
{
  "report_id": "rpt_987654321",
  "report_type": "anomaly_summary",
  "generated_at": "2025-06-11T10:30:00Z",
  "report_data": {
    "summary": "Análise de anomalias dos últimos 30 dias",
    "total_anomalies": 15,
    "critical_anomalies": 3,
    "anomalies_by_type": {
      "temperature": 8,
      "vibration": 5,
      "pressure": 2
    }
  },
  "metadata": {
    "date_range": "2025-05-11 to 2025-06-11",
    "total_sensors": 45,
    "data_points_analyzed": 12450
  }
}
```

**Tipos de Relatório Disponíveis:**
- `anomaly_summary` - Resumo de anomalias detectadas
- `system_health` - Relatório geral de saúde do sistema
- `maintenance_summary` - Resumo de atividades de manutenção
- `performance_summary` - Métricas de performance do sistema

### Submissão de Decisão Humana

#### POST /api/v1/decisions/submit

Submete feedback humano ou decisões sobre consultas solicitadas pelo sistema para aprovação/rejeição de manutenção.

**Corpo da Requisição:**
```json
{
  "request_id": "req_maintenance_123",
  "decision": "approve",
  "justification": "Equipamento crítico requer atenção imediata",
  "submitted_by": "operator_001"
}
```

**Resposta (200 OK):**
```json
{
  "message": "Decisão submetida com sucesso",
  "request_id": "req_maintenance_123",
  "decision": "approve",
  "timestamp": "2025-06-11T10:30:00Z",
  "status": "processed"
}
```

**Opções de Decisão:**
- `approve` - Aprovar a solicitação de manutenção
- `reject` - Rejeitar a solicitação de manutenção
- `defer` - Adiar a decisão para revisão posterior

## Endpoints de Verificação de Saúde

### GET /health

Endpoint básico de verificação de saúde para verificar disponibilidade da API.

**Resposta (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T10:30:00Z",
  "version": "v1.0.0"
}
```

### GET /health/detailed

Verificação detalhada de saúde incluindo status do banco de dados e serviços.

**Resposta (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T10:30:00Z",
  "services": {
    "database": "healthy",
    "event_bus": "healthy",
    "ml_services": "healthy"
  },
  "version": "v1.0.0"
}
```

## Tratamento de Erros

A API usa códigos de status HTTP padrão e retorna respostas de erro estruturadas:

### Formato de Resposta de Erro

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "O corpo da requisição é inválido",
    "details": {
      "field": "sensor_id",
      "issue": "Este campo é obrigatório"
    }
  },
  "timestamp": "2025-06-11T10:30:00Z",
  "request_id": "req_error_123"
}
```

### Códigos de Erro Comuns

- `400 Bad Request` - Formato de requisição inválido ou campos obrigatórios ausentes
- `401 Unauthorized` - Chave API ausente ou inválida
- `403 Forbidden` - Permissões insuficientes para a operação solicitada
- `404 Not Found` - Recurso solicitado não encontrado
- `422 Unprocessable Entity` - Falha na validação da requisição
- `500 Internal Server Error` - Erro inesperado do servidor

## Limitação de Taxa

A API implementa limitação de taxa para garantir uso justo:

- **Ingestão de Dados**: 100 requisições por minuto por chave API
- **Geração de Relatórios**: 10 requisições por minuto por chave API
- **Submissão de Decisões**: 50 requisições por minuto por chave API

Cabeçalhos de limite de taxa são incluídos em todas as respostas:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623456789
```

## Exemplos

### Fluxo de Trabalho Completo de Ingestão de Dados

```bash
# 1. Ingerir dados de sensor
curl -X POST "http://localhost:8000/api/v1/data/ingest" \
  -H "X-API-Key: sua-chave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "TEMP_001",
    "value": 85.5,
    "sensor_type": "temperature",
    "unit": "celsius",
    "location": "Piso da Fábrica A"
  }'

# 2. Gerar relatório de anomalias
curl -X POST "http://localhost:8000/api/v1/data/ingest" \
  -H "X-API-Key: sua-chave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "anomaly_summary",
    "start_date": "2025-05-11",
    "end_date": "2025-06-11"
  }'

# 3. Submeter decisão de manutenção
curl -X POST "http://localhost:8000/api/v1/decisions/submit" \
  -H "X-API-Key: sua-chave-api" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_maintenance_123",
    "decision": "approve",
    "justification": "Anomalia de temperatura requer atenção imediata"
  }'
```
