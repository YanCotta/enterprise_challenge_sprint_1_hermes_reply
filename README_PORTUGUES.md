# Smart Maintenance SaaS

*[English](README.md) | **Português***

**Status:** V1.0 Pronto para Produção | Documentação Sincronizada  
**Última Atualização:** 2025-09-30

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-V1.0%20Pronto-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-17%2B%20Modelos-blue)](.)
[![Performance](https://img.shields.io/badge/API%20Response-<2s-purple)](.)
[![Cloud](https://img.shields.io/badge/Cloud-Pronto-orange)](.)

## Visão Geral

Plataforma SaaS de manutenção preditiva pronta para produção, otimizada para aplicações industriais. Apresenta implantação cloud-native (TimescaleDB, Redis, S3), orquestração multi-agente com fluxos de trabalho orientados por eventos e insights de manutenção baseados em ML. A V1.0 entrega capacidades essenciais com adiamentos de recursos intencionais documentados no playbook de implantação.

**Visualizações de Arquitetura:** Veja [Diagramas da Arquitetura do Sistema](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#2-system-architecture-visualizations) para guias visuais abrangentes incluindo:
- [Visão Geral do Sistema de Alto Nível](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#21-high-level-system-overview) - Arquitetura completa do sistema
- [Sistema Multi-Agente](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#27-complete-multi-agent-system-architecture) - 12 agentes especializados
- [Pipeline de Ingestão de Dados](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#29-data-ingestion-and-processing-pipeline) - Fluxo de dados orientado por eventos
- [Endpoints da API](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#214-api-endpoints-architecture) - Estrutura da API REST

## Início Rápido

**Pré-requisitos:** Docker & Docker Compose, serviços de cloud configurados

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Configurar ambiente
cp .env_example.txt .env
# Preencher credenciais da cloud (TimescaleDB, Redis, S3, MLflow)

# Implantar
docker compose up -d --build

# Acessar UI: http://localhost:8501
# Saúde da API: http://localhost:8000/health
```

## Capacidades Principais

**V1.0 Entregue:**
- Ingestão de dados + explorador ([veja diagrama do pipeline](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#29-data-ingestion-and-processing-pipeline))
- Previsão ML (resolução automática de versão) ([veja pipeline ML](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#23-mlflow-model-management-pipeline))
- Explorador básico de metadados de modelo (diferenciação de estado)
- Verificações de drift & anomalia sob demanda ([veja automação MLOps](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#28-mlops-automation-drift-detection-to-retraining))
- Demo Golden Path (proteção de timeout de 90s) ([veja fluxo de eventos](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#22-production-event-driven-architecture-flow))
- Log de auditoria de decisões (exportação CSV)
- Relatórios (protótipo apenas JSON)
- Snapshot de métricas (não-streaming)
- Console de simulação (cenários normal/drift/anomalia)
- Camada de estabilidade central (abstração de rerun segura)

## Escopo V1.0 Mínimo vs Adiado

### ✅ Capacidades V1.0 Entregues
1. **Ingestão de dados + explorador** - Ingestão de arquivo único com rastreamento de correlação e paginação
2. **Previsão ML** - Resolução automática de versão com integração ao registro de modelos (MLflow opcional)
3. **Explorador de metadados de modelo** - Diferenciação de estado (desabilitado/vazio/erro/populado)
4. **Detecção de drift & anomalia** - Análise sob demanda com teste KS e Isolation Forest
5. **Demo Golden Path** - Fluxo de trabalho instrumentado com proteção de timeout de 90s e monitoramento de eventos
6. **Log de auditoria de decisões** - Decisões humanas persistidas com filtragem e exportação CSV
7. **Protótipo de relatórios** - Geração de relatórios JSON com pré-visualização de gráficos (artefatos adiados)
8. **Snapshot de métricas** - Métricas Prometheus pontuais (streaming adiado)
9. **Console de simulação** - Cenários de teste normal/drift/anomalia com rastreamento de latência
10. **Camada de estabilidade** - Abstração central de rerun segura prevenindo crashes em tempo de execução

### 🚫 Adiado para V1.5+ (Explicitamente Fora do Escopo)
- Artefatos de relatório (geração/download de arquivos)
- Streaming de métricas em tempo real  
- Processamento SHAP em background
- Ingestão em lote & previsão em batch
- Correlação multi-sensor / análises compostas
- Cache/virtualização de recomendações de modelo
- UI de notificações avançadas
- Visualização / linhagem do feature store
- Políticas de governança & retenção

## Matriz de Links

### Documentação Autoritativa (Fonte Única da Verdade)
- [Playbook de Implantação V1.0](smart-maintenance-saas/docs/v1_release_must_do.md) - **Referência canônica**: Substitui backlog anterior, checklist de prontidão e docs de auditoria; consolida escopo, tarefas e procedimentos de implantação
- [Changelog de Redesign de UI](smart-maintenance-saas/docs/ui_redesign_changelog.md) - Trilha de evolução da UI V1.0 com implementações de recursos e correções
- [Changelog Sprint 4](smart-maintenance-saas/docs/legacy/sprint_4_changelog.md) - Marcos de implantação cloud, integração MLflow e conquistas de infraestrutura
- [Resumo Executivo](smart-maintenance-saas/docs/EXECUTIVE_SUMMARY.md) - Status de estabilização do sistema e confirmação de prontidão V1.0

### Documentação Principal
- [Sistema & Arquitetura](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md) - Arquitetura de alto nível com diagramas abrangentes ([índice de visualizações](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#2-system-architecture-visualizations))
- [Referência da API](smart-maintenance-saas/docs/api.md) - Endpoints REST & integração ([veja diagrama da arquitetura da API](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#214-api-endpoints-architecture))
- [Documentação do Banco de Dados](smart-maintenance-saas/docs/db/README.md) - Schema & recursos TimescaleDB ([veja arquitetura do DB](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#24-timescaledb-performance-architecture))
- [Documentação ML](smart-maintenance-saas/docs/ml/README.md) - Modelos & pipelines ([veja diagrama do pipeline ML](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#23-mlflow-model-management-pipeline))
- [Documentação de Segurança](smart-maintenance-saas/docs/SECURITY.md) - Arquitetura de segurança ([veja fluxo de segurança](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#211-security-and-authentication-flow))

### Performance & Testes  
- [Resultados de Teste de Carga](smart-maintenance-saas/docs/legacy/DAY_17_LOAD_TEST_REPORT.md) - Validação de 103.8 RPS (arquivado)
- [Resultados de Performance](smart-maintenance-saas/docs/legacy/DAY_18_PERFORMANCE_RESULTS.md) - Otimização TimescaleDB (arquivado)
- [Baseline de Performance](smart-maintenance-saas/docs/legacy/PERFORMANCE_BASELINE.md) - Metas SLO & métricas (arquivado)
- [Plano de Cobertura](smart-maintenance-saas/docs/legacy/COVERAGE_IMPROVEMENT_PLAN.md) - Estratégia de cobertura de teste (arquivado)

### Operações & Implantação
- [Guia de Implantação Cloud](smart-maintenance-saas/docs/CLOUD_DEPLOYMENT_GUIDE.md) - Implantação específica por plataforma (Render, Railway, Heroku) com configuração de ambiente ([veja arquitetura de implantação](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#appendix-d-deployment-architecture-future-oriented-illustration))
- [Configuração de Implantação](smart-maintenance-saas/docs/DEPLOYMENT_SETUP.md) - Configuração de ambiente e gerenciamento de .env ([veja serviços Docker](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#26-docker-services-architecture))
- [Guia de Configuração DVC](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md) - Configuração de controle de versão de dados
- [Orientação de Desenvolvimento](smart-maintenance-saas/docs/legacy/DEVELOPMENT_ORIENTATION.md) - Padrões de engenharia (arquivado)

### Legado & Histórico
- [Índice de Documentação Legada](smart-maintenance-saas/docs/legacy/INDEX.md) - Documentos históricos arquivados

## Contribuição

Contribuições bem-vindas para melhorias V1.0+. Processo de revisão:

1. Consultar [Playbook de Implantação V1.0](smart-maintenance-saas/docs/v1_release_must_do.md) para escopo atual e recursos adiados
2. Verificar alinhamento com capacidades entregues (sem aumento de escopo V1.0)
3. Testar mudanças contra suítes de teste existentes (ver diretório `tests/`)
4. Atualizar documentação relevante para mudanças arquiteturais ou de API
5. Seguir diretrizes da [Documentação de Segurança](smart-maintenance-saas/docs/SECURITY.md) para mudanças relacionadas à segurança

---

**Lançamento V1.0:** Todos os fluxos de trabalho principais operacionais com implantação cloud verificada. Capacidades de backend com 100% de prontidão; UI intencionalmente expõe conjunto mínimo de fluxos de trabalho conforme Seção 2 do playbook de implantação.