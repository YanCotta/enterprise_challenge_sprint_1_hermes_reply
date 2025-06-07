<div align="center">

# Smart Maintenance SaaS

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-Prototype-orange)](.)
[![FIAP](https://img.shields.io/badge/FIAP-Challenge-red)](https://www.fiap.com.br)
[![Hermes Reply](https://img.shields.io/badge/Partner-Hermes%20Reply-blue)](https://www.reply.com/hermes-reply/en/)

<h3>
    Uma Solução Vanguardista de Manutenção Preditiva Industrial Potencializada por Multi-Agentic AI Systems, MCP & A2A
</h3>

[Relatório Técnico](./system_documentation_and_architecture.md)

</div>

## 🎯 Sobre o Projeto

O **Smart Maintenance SaaS** é uma solução inovadora de manutenção preditiva para o setor industrial, desenvolvida como parte do desafio FIAP SP em parceria com a Hermes Reply. O projeto utiliza tecnologias avançadas de IoT, IA e análise de dados em tempo real para transformar a gestão de ativos industriais.

### 🚀 Backend Multi-Agente: Fundação Concluída

O core do projeto é um robusto **sistema multi-agente orientado a eventos** que fornece uma base sólida para ingestão de dados de sensores, detecção de anomalias, validação de alertas, previsão de falhas e orquestração de fluxos de trabalho de manutenção. A fase inicial de desenvolvimento (Fase 1) foi concluída com:

- **Arquitetura Completa**: Sistema orientado a eventos com comunicação assíncrona entre agentes
- **Agentes Core Implementados**: Aquisição de Dados, Detecção de Anomalias (ML + Estatística), Validação (Regras + Contexto Histórico), Predição (Prophet ML)
- **Pipeline Completo**: Da ingestão de dados até recomendações de manutenção preditiva
- **Framework de Testes**: 209/209 testes passando, incluindo testes unitários e de integração

[📝 Detalhes Técnicos do Backend](./smart-maintenance-saas/README.md)

## ⭐ Funcionalidades Principais

<div align="center">

| Funcionalidade | Descrição | Status |
|---------------|-----------|--------|
| 🔍 **Monitoramento IoT** | Monitoramento contínuo e validação de dados de sensores via sistema de aquisição de dados | ✅ Implementado |
| 🤖 **ML Predictions** | Detecção de anomalias (dual-method) e previsão de falhas com Machine Learning (Isolation Forest + Prophet) | ✅ Implementado |
| 🛡️ **Validação Inteligente** | Validação avançada com ajuste de confiança baseado em regras e análise de contexto histórico | ✅ Implementado |
| ⚡ **Smart Scheduling** | Recomendações de manutenção baseadas em previsões de time-to-failure (implementação parcial) | 🔄 Parcial |
| 📊 **Analytics** | Dashboard interativo e relatórios inteligentes | 🔄 Em Progresso |
| ⚙️ **Multi-Agentic System** | Sistema multi-agente orquestrado com arquitetura escalável e comunicação evento-orientada | ✅ Framework Base Implementado |

</div>

## 🛠️ Stack Tecnológico

<details>
<summary>🌐 IoT e Edge Computing</summary>

- **ESP32** - Aquisição de dados em tempo real
- **MQTT** - Protocolo de comunicação leve e eficiente
- **Apache Kafka** - Streaming de dados escalável
- **AWS IoT Greengrass** - Processamento na borda otimizado

</details>

<details>
<summary>🧠 Backend (Sistema Multi-Agente)</summary>

- **Python 3.11+** - Linguagem moderna com suporte completo a async/await
- **FastAPI** - Framework web assíncrono de alta performance
- **Pydantic v2** - Validação de dados avançada e gerenciamento de configurações
- **SQLAlchemy 2.0** - ORM moderno com segurança de tipos
- **TimescaleDB** - Banco de dados otimizado para séries temporais
- **EventBus Customizado** - Comunicação assíncrona entre agentes
- **Prophet** - Previsões de time-to-failure e manutenção preditiva
- **Isolation Forest** - Detecção de anomalias não supervisionada
- **LangChain/CrewAI** - Framework para implementação de agentes (planejado)
- **MCP & A2A** - Comunicação inter-agêntica (planejado)

[🔗 Ver Stack Completa do Backend](./smart-maintenance-saas/README.md#tech-stack)

</details>

<details>
<summary>🎨 Frontend</summary>

- **Next.js** - Framework React moderno com SSR
- **TypeScript** - Desenvolvimento tipado e seguro
- **Tailwind CSS** - Design responsivo e customizável
- **D3.js** - Visualizações de dados interativas

</details>

<details>
<summary>💾 Banco de Dados</summary>

- **PostgreSQL/TimescaleDB** - Armazenamento otimizado para séries temporais
- **Amazon S3** - Data Lake escalável e durável

</details>

<details>
<summary>☁️ Infraestrutura Cloud</summary>

- **AWS Suite** - IoT Core, EC2, RDS, Lambda, SNS, ECS
- **Container Stack** - Docker + Kubernetes para orquestração

</details>

## 🏗️ Arquitetura

<div align="center">

### Sistema Multi-Agente Especializado

| Agente | Responsabilidade | Tecnologias | Status |
|--------|-----------------|-------------|--------|
| 🔄 **DataAcquisition** | Aquisição de dados | Validação, Enriquecimento, EventBus | ✅ Completo |
| 🔍 **AnomalyDetection** | Detecção de anomalias | Isolation Forest, Estatística | ✅ Completo |
| ✅ **Validation** | Validação de anomalias | Regras, Análise de Contexto Histórico | ✅ Completo |
| 🔮 **Prediction** | Previsão de falhas | Prophet, Time-to-Failure | ✅ Completo |
| 🎯 **Orchestrator** | Coordenação de decisões | Event-driven Workflows, State Management | ✅ Completo |
| 📅 **Scheduler** | Agendamento de manutenções | MCP, Calendar Integration | 🔄 Em Progresso |
| 📊 **Reporter** | Geração de relatórios | NLP, Data Visualization | 🔄 Planejado |
| 🧠 **Learning** | Otimização contínua | RAG, Feedback Loop | 🔄 Planejado |

</div>

## 📊 Visão Geral da Arquitetura

```mermaid
graph TD
    subgraph "Sensores IoT"
        S[Sensores] --> MQTT[MQTT Broker]
    end

    subgraph "Sistema Multi-Agente"
        MQTT --> DA[DataAcquisition Agent]
        DA --> AD[AnomalyDetection Agent]
        AD --> VA[Validation Agent]
        VA --> PA[Prediction Agent]
        PA --> OA[Orchestrator Agent]
        OA --> SA[Scheduler Agent]
        OA --> RA[Reporter Agent]
        LA[Learning Agent] -.-> OA
    end

    subgraph "Frontend"
        UI[Dashboard UI] <--> API[API Layer]
        API <--> OA
    end

    subgraph "Database"
        DB[(TimescaleDB)]
    end
    
    DA <--> DB
    AD <--> DB
    VA <--> DB
    PA <--> DB

    style DA fill:#90EE90,stroke:#333,stroke-width:2px
    style AD fill:#90EE90,stroke:#333,stroke-width:2px
    style VA fill:#90EE90,stroke:#333,stroke-width:2px
    style PA fill:#90EE90,stroke:#333,stroke-width:2px
    style OA fill:#FFA500,stroke:#333,stroke-width:2px
    style SA fill:#FFA500,stroke:#333,stroke-width:2px
    style RA fill:#FFC0CB,stroke:#333,stroke-width:2px
    style LA fill:#FFC0CB,stroke:#333,stroke-width:2px
```

**Legenda:**

- 🟢 Verde - Agentes implementados e testados
- 🟠 Laranja - Agentes em desenvolvimento
- 🔴 Rosa - Agentes planejados

Para uma arquitetura detalhada, consulte a [documentação completa](./system_documentation_and_architecture.md#23-diagrama-de-arquitetura-geral).

## 👥 Equipe

<div align="center">

| Membro | Registro |
|--------|-----------|
| **Yan Pimentel Cotta** | RM: 562836 |

</div>

</div>

## 📊 Status do Projeto

<div align="center">

| Fase | Status | Detalhe | Data |
|------|--------|---------|------|
| ✅ **Fase 1: Documentação e Fundação do Backend** | `Concluído` | Arquitetura, documentação e implementação dos agentes core | Maio 2025 |
| 🔄 **Fase 2: Expansão do Sistema Multi-Agente** | `Em Progresso` | Implementação dos agentes de orquestração e scheduling | Junho 2025 |
| 🔜 **Fase 3: Frontend e Integração** | `Planejado` | Desenvolvimento da interface e integração completa | Julho 2025 |

</div>

## 🔬 Métricas do Sistema

<div align="center">

| Métrica | Valor | Detalhe |
|---------|-------|---------|
| 🧪 **Testes** | 209/209 | Testes unitários e de integração passando |
| ⚡ **Performance** | <5ms | Tempo de processamento por leitura de sensor |
| 🔄 **Agentes Completos** | 4/8 | Agentes core implementados e testados |
| 📊 **Cobertura** | >90% | Cobertura de código atual |

</div>

## 📜 Licença

<div align="center">

Este projeto está licenciado sob a [Licença MIT](LICENSE) - veja o arquivo LICENSE para detalhes.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

</div>

## 📚 Documentação

<div align="center">

| Documento | Descrição | Link |
|-----------|-----------|------|
| **Arquitetura do Sistema** | Visão completa da arquitetura, stack e fluxos de dados | [📝 Documentação Técnica](./system_documentation_and_architecture.md) |
| **Documentação do Backend** | Detalhes técnicos do sistema multi-agente, API e banco de dados | [🔧 README do Backend](./smart-maintenance-saas/README.md) |
| **API Reference** | Especificação da API e endpoints disponíveis | [🔌 Documentação da API](./smart-maintenance-saas/docs/api.md) |

[![Documentação](https://img.shields.io/badge/Docs-System%20Architecture-blue)](./system_documentation_and_architecture.md)
[![Backend](https://img.shields.io/badge/Docs-Backend%20System-green)](./smart-maintenance-saas/README.md)

Para informações detalhadas sobre a arquitetura e implementação técnica, consulte nossa [Documentação Completa](./system_documentation_and_architecture.md).

</div>

---

<div align="center">

**Data de Entrega:** `08 de Maio de 2025` | **Versão:** `1.3`
