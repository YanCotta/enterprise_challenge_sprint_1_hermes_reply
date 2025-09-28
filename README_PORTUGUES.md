# Smart Maintenance SaaS

*[English](README.md) | **Português***

**Status:** Estável (Escopo V1.0 Mínimo) | Prontidão: 94.5% | Recursos Adiados Rastreados  
**Última Sincronização:** 2025-12-19

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-V1.0%20Pronto-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-17%2B%20Modelos-blue)](.)
[![Performance](https://img.shields.io/badge/API%20Response-<2s-purple)](.)
[![Cloud](https://img.shields.io/badge/Cloud-Pronto-orange)](.)

## DOCUMENTACAO DESATUALIZADA -> SERA ATUALIZADA ATE DIA 03/10, NO LANCAMENTO DA VERSAO 1.0

## Visão Geral

Plataforma de manutenção preditiva pronta para produção, entregando escopo V1.0 mínimo com 94.5% de prontidão. Apresenta implantação cloud-native, orquestração multi-agente e insights de manutenção orientados por dados otimizados para aplicações industriais.

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
- Ingestão de dados + explorador  
- Previsão ML (resolução automática de versão)
- Explorador básico de metadados de modelo (diferenciação de estado)
- Verificações de drift & anomalia sob demanda
- Demo Golden Path (proteção de timeout de 90s)
- Log de auditoria de decisões (exportação CSV)
- Relatórios (protótipo apenas JSON)
- Snapshot de métricas (não-streaming)
- Console de simulação (cenários normal/drift/anomalia)
- Camada de estabilidade central (abstração de rerun segura)

## Escopo V1.0 Mínimo vs Adiado

### ✅ Escopo V1.0 Mínimo (Entregue - 94.5% Pronto)
1. **Ingestão de dados + explorador** - Ingestão de arquivo único com rastreamento de correlação
2. **Previsão ML** - Resolução automática de versão (SHAP intencionalmente adiado)  
3. **Explorador básico de metadados de modelo** - Diferenciação de estado (desabilitado/vazio/erro/populado)
4. **Verificações de drift & anomalia sob demanda** - Análise de gatilho manual
5. **Demo Golden Path** - Fluxo de trabalho instrumentado com proteção de timeout de 90s
6. **Log de auditoria de decisões** - Decisões humanas persistidas com exportação CSV
7. **Relatórios** - Protótipo apenas JSON (downloads de artefatos adiados)
8. **Snapshot de métricas** - Métricas pontuais (streaming adiado)
9. **Console de simulação** - Cenários de teste normal/drift/anomalia
10. **Camada de estabilidade** - Abstração central de rerun segura

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

### Documentação Autoritativa (Fontes da Verdade)
- [Resumo Executivo](smart-maintenance-saas/docs/EXECUTIVE_SUMMARY.md) - Status de estabilização do sistema
- [Backlog Priorizado](smart-maintenance-saas/docs/PRIORITIZED_BACKLOG.md) - Escopo V1.0 & recursos adiados  
- [Checklist de Prontidão V1.0](smart-maintenance-saas/docs/V1_READINESS_CHECKLIST.md) - Avaliação de prontidão 94.5%
- [Capacidades do Sistema & Redesign de UI](smart-maintenance-saas/docs/SYSTEM_CAPABILITIES_AND_UI_REDESIGN.md) - Matriz completa de capacidades
- [Changelog de Redesign de UI](smart-maintenance-saas/docs/ui_redesign_changelog.md) - Trilha de evolução V1.0

### Documentação Principal
- [Sistema & Arquitetura](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md) - Arquitetura de alto nível
- [Referência da API](smart-maintenance-saas/docs/api.md) - Endpoints REST & integração
- [Documentação do Banco de Dados](smart-maintenance-saas/docs/db/README.md) - Schema & recursos TimescaleDB
- [Documentação ML](smart-maintenance-saas/docs/ml/README.md) - Modelos & pipelines
- [Documentação de Segurança](smart-maintenance-saas/docs/SECURITY.md) - Arquitetura de segurança

### Performance & Testes  
- [Baseline de Performance](smart-maintenance-saas/docs/PERFORMANCE_BASELINE.md) - Metas SLO & métricas
- [Resultados de Teste de Carga](smart-maintenance-saas/docs/DAY_17_LOAD_TEST_REPORT.md) - Validação de 103.8 RPS
- [Plano de Teste V1](smart-maintenance-saas/docs/TEST_PLAN_V1.md) - Framework de estratégia de teste
- [Plano de Cobertura](smart-maintenance-saas/docs/COVERAGE_IMPROVEMENT_PLAN.md) - Estratégia de cobertura de teste

### Operações & Implantação
- [Guia de Implantação Cloud](smart-maintenance-saas/docs/CLOUD_DEPLOYMENT_GUIDE.md) - Configuração & provisionamento cloud  
- [Guia de Configuração DVC](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md) - Controle de versão de dados
- [Orientação de Desenvolvimento](smart-maintenance-saas/docs/DEVELOPMENT_ORIENTATION.md) - Padrões de engenharia

### Legado & Histórico
- [Índice de Documentação Legada](smart-maintenance-saas/docs/legacy/INDEX.md) - Documentos históricos arquivados

## Contribuição

Este é software V1.0 pronto para produção. Para contribuições:

1. Revisar escopo autoritativo em V1_READINESS_CHECKLIST.md
2. Alinhar com conjunto mínimo de recursos V1.0 (sem aumento de escopo)  
3. Testar mudanças contra suíte de testes existente
4. Atualizar documentação para quaisquer mudanças arquiteturais
5. Seguir checklist de auditoria de segurança para mudanças relacionadas à segurança

---

**Conquista V1.0:** 94.5% de prontidão para produção com todos os fluxos de trabalho principais operacionais e bloqueadores de implantação resolvidos.

**Próxima Fase:** Endurecimento V1.1 (cobertura de teste aprimorada, percentis de métricas, design de persistência de artefatos) começa após ciclo de feedback do usuário.