# Smart Maintenance SaaS

*[English](README.md) | **Português***

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-15%2B%20Models-blue)](.)
[![Performance](https://img.shields.io/badge/P95%20Latency-2ms%20(@50u)-purple)](.)

Uma plataforma de Manutenção Industrial Preditiva e Prescritiva pronta para produção, combinando ingestão IoT, otimização de séries temporais TimescaleDB, ML multimodal (tabular, vibração, áudio, previsão), detecção automatizada de drift e retreinamento, e arquitetura orientada a eventos resiliente.

---

Demonstração resumida do estado do sistema: https://youtu.be/qZnY5U5Vp_s?si=xOOlv7TNTCUzpLxj

---

## 📚 Índice da Documentação

### Essencial

- Principal: este README
- Orientação de Desenvolvimento: [DEVELOPMENT_ORIENTATION.md](smart-maintenance-saas/docs/DEVELOPMENT_ORIENTATION.md)
- Changelog Sprint 30 Dias: [30-day-sprint-changelog.md](smart-maintenance-saas/docs/30-day-sprint-changelog.md)
- Resumo Sprint Final: [final_30_day_sprint.md](smart-maintenance-saas/docs/final_30_day_sprint.md)
- Roadmap Futuro: [FUTURE_ROADMAP.md](smart-maintenance-saas/docs/FUTURE_ROADMAP.md)

### Arquitetura e Design

- Sistema e Arquitetura: [SYSTEM_AND_ARCHITECTURE.md](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md)
- Análise Abrangente do Sistema: [COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md](smart-maintenance-saas/docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)
- Estratégia de Migração para Microsserviços: [MICROSERVICE_MIGRATION_STRATEGY.md](smart-maintenance-saas/docs/MICROSERVICE_MIGRATION_STRATEGY.md)

### Banco de Dados

- Documentação do Banco: [db/README.md](smart-maintenance-saas/docs/db/README.md)
- ERD (dbml/png): [erd.dbml](smart-maintenance-saas/docs/db/erd.dbml), [erd.png](smart-maintenance-saas/docs/db/erd.png), [erd_darkmode.png](smart-maintenance-saas/docs/db/erd_darkmode.png)
- Schema SQL: [schema.sql](smart-maintenance-saas/docs/db/schema.sql)

### API e Configuração

- Referência da API: [api.md](smart-maintenance-saas/docs/api.md)
- Sistema de Configuração: [core/config/README.md](smart-maintenance-saas/core/config/README.md)
- Configuração de Logging: [core/logging_config.md](smart-maintenance-saas/core/logging_config.md)

### Performance e Testes

- Baseline de Performance: [PERFORMANCE_BASELINE.md](smart-maintenance-saas/docs/PERFORMANCE_BASELINE.md)
- Relatório de Teste de Carga (Dia 17): [DAY_17_LOAD_TEST_REPORT.md](smart-maintenance-saas/docs/DAY_17_LOAD_TEST_REPORT.md)
- Performance BD (Dia 18): [DAY_18_PERFORMANCE_RESULTS.md](smart-maintenance-saas/docs/DAY_18_PERFORMANCE_RESULTS.md)
- Instruções de Teste de Carga: [LOAD_TESTING_INSTRUCTIONS.md](smart-maintenance-saas/docs/LOAD_TESTING_INSTRUCTIONS.md)
- Plano de Cobertura: [COVERAGE_IMPROVEMENT_PLAN.md](smart-maintenance-saas/docs/COVERAGE_IMPROVEMENT_PLAN.md)
- Guia de Testes: [tests/README.md](smart-maintenance-saas/tests/README.md)

### ML e Dados

- Documentação ML: [ml/README.md](smart-maintenance-saas/docs/ml/README.md)
- Resumo dos Modelos: [MODELS_SUMMARY.md](smart-maintenance-saas/docs/MODELS_SUMMARY.md)
- Seleção Inteligente de Modelos (Ao Vivo): [Seção de Seleção Dinâmica](smart-maintenance-saas/docs/MODELS_SUMMARY.md#intelligent-dynamic-model-selection-live-system)
- Plano Project Gauntlet: [PROJECT_GAUNTLET_PLAN.md](smart-maintenance-saas/docs/PROJECT_GAUNTLET_PLAN.md)
- Guia de Configuração DVC: [DVC_SETUP_GUIDE.md](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md)
- Comandos de Configuração DVC: [dvc_setup_commands.md](smart-maintenance-saas/docs/dvc_setup_commands.md)

### Segurança e UI

- Segurança: [SECURITY.md](smart-maintenance-saas/docs/SECURITY.md)
- Checklist de Auditoria de Segurança: [SECURITY_AUDIT_CHECKLIST.md](smart-maintenance-saas/docs/SECURITY_AUDIT_CHECKLIST.md)
- Funcionalidades da UI (Abrangente): [UI_FEATURES_COMPREHENSIVE.md](smart-maintenance-saas/docs/UI_FEATURES_COMPREHENSIVE.md)

### Serviços (Futuro)

- Serviço de Anomalias: [services/anomaly_service/README.md](smart-maintenance-saas/services/anomaly_service/README.md)
- Serviço de Predição: [services/prediction_service/README.md](smart-maintenance-saas/services/prediction_service/README.md)

---

## 🚀 Início Rápido (5 Minutos)

Pré-requisitos: Docker & Docker Compose instalados.

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply
docker compose up -d --build
# Serviços principais:
# API:        http://localhost:8000/docs
# UI:         http://localhost:8501
# MLflow:     http://localhost:5000
# Métricas:   http://localhost:8000/metrics
```

Datasets e modelos (opcional, requer DVC):

```bash
cd smart-maintenance-saas
dvc pull
```
 
Consulte os guias DVC: [DVC_SETUP_GUIDE.md](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md), [dvc_setup_commands.md](smart-maintenance-saas/docs/dvc_setup_commands.md). Espelho de dados público: <https://drive.google.com/drive/folders/1cJvSRaBG0Fzs4D_wlUeVPM9l47RP_k3G?usp=sharing>


Parar e limpar (não destrutivo):

```bash
docker compose down
```

---

## 🧩 Visão Geral da Plataforma

| Capacidade | Status | Notas |
|------------|--------|-------|
| Ingestão e Idempotência | ✅ | Redis-backed SET NX EX (10m TTL) |
| Armazenamento de Séries Temporais | ✅ | TimescaleDB hypertable + compressão + retenção |
| Otimização de Consultas | ✅ | Índice composto (sensor_id, timestamp DESC) + agregado contínuo horário |
| Observabilidade | ✅ | Prometheus (/metrics), logs JSON estruturados, IDs de correlação, endpoints de saúde |
| Registro de Modelos ML | ✅ | MLflow persistente (SQLite + volume) |
| Catálogo de Modelos | ✅ | 15+ modelos (anomalia, previsão, classificação, áudio, vibração) |
| Detecção de Drift | ✅ | Testes KS/PSI, endpoint /api/v1/ml/check_drift, monitoramento agentizado |
| Retreinamento Automatizado | ✅ | Orientado a eventos (Redis pub/sub) agente de retreino com políticas de cooldown |
| Endurecimento de Segurança | ✅ | Auth API key (X-API-Key), limitação de taxa (slowapi), checklist STRIDE |
| Caos e Resiliência | ✅ | Testes de latência/timeout Toxiproxy; bus de eventos com retry; degradação graciosa |
| Scaffolding de Microsserviços | ✅ (Dormente) | prediction_service & anomaly_service (gatilhos de ativação futuros) |

---

## 🗄️ Arquitetura de Dados e Banco de Dados

**Armazenamento Principal:** TimescaleDB  
**Tabela:** sensor_readings (hypertable)  
**Chave Primária:** (timestamp, sensor_id)  
**Índices:**  

- `(sensor_id, timestamp DESC)` → acelera janelas deslizantes ML e consultas de drift  
- `(timestamp)` → varreduras de intervalo temporal  

**Agregado Contínuo:** `sensor_readings_summary_hourly` (avg, max, min, count)  

- Política de atualização: a cada 30m, deslocamento de início de janela 2h, fim 30m  
- Alcançou **37,3% de melhoria na velocidade de consulta** em cargas de trabalho de agregação (validado Dia 18)  

**Políticas:** compressão ≥ 7 dias, retenção 180 dias (ajustável)  

Benefícios:

- Estatísticas horárias pré-computadas aceleram engenharia de características e dashboards
- Varreduras de linha reduzidas (83% menos linhas para consultas agregadas de 24h)
- Performance previsível sob carga

Documentos relacionados: `./smart-maintenance-saas/docs/db/README.md`, `./smart-maintenance-saas/docs/DAY_18_PERFORMANCE_RESULTS.md`

---

## 📤 Exportação de Dados

Exportação completa:

```bash
docker compose exec api python scripts/export_sensor_data_csv.py
```
 
Exportação incremental (anexa apenas novas linhas desde a última execução):

```bash
docker compose exec api python scripts/export_sensor_data_csv.py --incremental
```
 
Saída customizada:

```bash
docker compose exec api python scripts/export_sensor_data_csv.py --output /tmp/readings.csv
```

---

## 🔭 Observabilidade e Performance

| Aspecto | Implementação |
|--------|----------------|
| Métricas | Prometheus via prometheus-fastapi-instrumentator (`/metrics`) |
| Logging | JSON estruturado + correlation_id (ContextVar) |
| Rastreamento | Propagação X-Request-ID (RequestIDMiddleware) |
| Teste de Carga (Dia 17) | 50 usuários / 3m → Pico 103,8 RPS, P95 2ms, P99 3ms |
| Throughput de Eventos | Capacidade >100 eventos/seg validada |
| Ganhos de Performance | Redução de latência 10× vs baseline, DB agg 37,3% mais rápido |

Baseline SLO:

- API P95 < 200ms (P95 atual 2–4ms)
- Carga fria de predição P99 < 3s (em cache <1s)
- Verificação de drift P95 < 5s (atual 3–4ms)
- Taxa de erro < 0,1% (endpoints principais)

Variáveis de ambiente principais (seleção):

- `API_KEY` (obrigatório para auth API); UI lê do `.env`
- `DATABASE_URL`, `REDIS_URL` (compose define via Toxiproxy para testes de caos)
- `MLFLOW_TRACKING_URI`, `MLFLOW_S3_ENDPOINT_URL` (cliente MLflow)
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` (email)
- `SLACK_WEBHOOK_URL` (alertas de drift opcionais)
- `DRIFT_CHECK_ENABLED`, `DRIFT_CHECK_SCHEDULE`, `DRIFT_THRESHOLD`
- `RETRAINING_ENABLED`, `RETRAINING_COOLDOWN_HOURS`, `MAX_CONCURRENT_RETRAINING`
- `DISABLE_CHROMADB` (embedding de feature store desligado quando verdadeiro)
- `API_BASE_URL` para UI (usar `http://api:8000` dentro do Docker)

---

## 🤖 Plataforma ML

**Registro:** MLflow (volume persistente)  
**Famílias de Modelos:**  

- Detecção de Anomalias: IsolationForest (sintético + vibração), OneClassSVM (vibração)  
- Previsão: Prophet ajustado (20,86% melhoria MAE) + modelos desafiantes  
- Classificação: AI4I, Pump (100% acurácia), engenharia de características informada por metadados  
- Áudio: MFCC + RandomForest (MIMII, caminho de fallback sintético)  
- Vibração (NASA + XJTU): Características estatísticas + FFT (RMS, curtose, fator de crista, energia espectral)  

**Fases do Project Gauntlet:**  

1. Classificação AI4I (performance teto)  
2. Anomalia de Vibração NASA  
3. Anomalia de Áudio MIMII  
4. Classificação Pump (separação perfeita)  
5. Extensão Run-to-Failure XJTU  
6. Automação de Drift + Ciclo de Vida  
7. UI de Seleção Inteligente de Modelos  

**Seleção Inteligente de Modelos (UI):**

- Tags de modelo MLflow (ex. `domain=bearing|audio|tabular`)
- Subconjunto recomendado por tipo de sensor; override manual permitido

**Drift e Automação:**

- Agente de Drift (`scripts/run_drift_check_agent.py`) – KS & PSI agendados, emite eventos Redis
- Agente de Retreino (`scripts/retrain_models_on_drift.py`) – retreinamento com limitação de taxa com cooldown + incremento de versão MLflow
- Integração de notificação Slack/Webhook (configurável)
- Validação de hash de modelo CI (`scripts/validate_model_hashes.py`) previne drift silencioso/incompatibilidade de fonte

Portfólio de modelos (campeões):

| Tarefa | Modelo | Dataset | Métrica Chave |
| :--- | :--- | :--- | :--- |
| Detecção de Anomalias | `anomaly_detector_refined_v2` | Sensor Sintético | Não supervisionado |
| Previsão | `prophet_forecaster_enhanced_sensor-001` | Sensor Sintético | +20,86% MAE |
| Classificação | `ai4i_classifier_randomforest_baseline` | AI4I 2020 UCI | 99,9% Acc |
| Anomalia de Vibração | `vibration_anomaly_isolationforest` | NASA IMS | 10% Taxa de Anomalia |
| Classificação de Áudio | `RandomForest_MIMII_Audio_Benchmark` | MIMII | 93,3% Acc |
| Classificação | `pump_randomforest_baseline` | Kaggle Pump | 100% Acc |
| Anomalia de Vibração | `xjtu_anomaly_isolation_forest` | XJTU-SY | 10% Taxa de Anomalia |

---

## 🖥️ Destaques da UI

- Dashboard do Sistema: métricas em tempo real (memória, tempo de CPU, requisições, erros) analisadas de `/metrics`
- Ingestão e Gerenciamento de Dados: uploads manuais e CSV com validação
- Predições ML com IA Explicável: integração SHAP com TreeExplainer/KernelExplainer fallback
- Dashboard de Análise Preditiva: tendências, anomalias, previsões
- Gerenciamento de Manutenção: agendar/rastrear/registrar tarefas
- Visualizações: matplotlib/plotly; exportar relatórios (PDF, CSV)

Documentos relacionados: `./smart-maintenance-saas/docs/UI_FEATURES_COMPREHENSIVE.md`

---

## ✉️ Notificações

- Serviço de Email: `core/notifications/email_service.py` (STARTTLS, HTML/texto simples, templates de drift/retreino)
- Slack/Webhook: alertas de drift opcionais via `SLACK_WEBHOOK_URL`
- Degradação graciosa quando credenciais estão faltando (registra em vez de falhar)

Configure via `.env` (veja `./smart-maintenance-saas/.env.example`).
Também disponível: `.env.prod.example`, `.env.test` para overrides específicos de ambiente.

---

## 🎛️ Simulador de Demo Ao Vivo

Roteador FastAPI `apps/api/routers/simulate.py` fornece:

- `POST /api/v1/simulate/drift-event` – gerar drift estatístico
- `POST /api/v1/simulate/anomaly-event` – criar outliers
- `POST /api/v1/simulate/normal-data` – dados baseline

Implementa ingestão em background, resiliência de rede (Docker interno + localhost), e gatilho automático de verificação de drift.

UI integra um painel "Simulador de Demo do Sistema Ao Vivo" para demonstrações com um clique.

---

---

## 🛡️ Segurança

| Controle | Status | Notas |
|---------|--------|-------|
| Autenticação | ✅ | Cabeçalho API Key |
| Limitação de Taxa | ✅ | slowapi (ex. /api/v1/ml/check_drift: 10/min por chave) |
| Modelo de Ameaças | ✅ | STRIDE documentado |
| Checklist de Auditoria de Segurança | ✅ | docs/SECURITY_AUDIT_CHECKLIST.md |
| Escaneamento de Dependências | ✅ | Snyk CI (porta de falha alta/crítica) |
| Validação de Entrada | ✅ | Schemas Pydantic |
| Higiene de Logging | ✅ | Sem segredos nos logs |
| Futuro | ⏳ | Chaves API baseadas em escopo, manifestos de modelo assinados |

---

## ♻️ Resiliência e Confiabilidade

| Mecanismo | Detalhe |
|-----------|--------|
| Ingestão Idempotente | Redis SET NX EX (10m) previne publicação de eventos duplicados |
| Bus de Eventos | Retry com backoff exponencial + fallback DLQ |
| Degradação Graciosa | Continua sem Redis (registra aviso) |
| Engenharia de Caos | Injeção de latência/timeout/partição Toxiproxy |
| Migrações | Manual (intencional) para evitar tempestades de reinício (lição Dia 12) |
| Contrato de Características | feature_names.txt persistido com modelos |
| Recuperação Automatizada | Drift → Evento → Retreino → Atualização de registro |

Notas operacionais:

- Serviço `toxiproxy_init` auto-configura proxies DB/Redis na inicialização
- Script de entrada aplica correção de alinhamento de sequência/PK TimescaleDB durante inicialização do container

---

## 🛠️ Desenvolvimento e CI/CD

| Área | Notas |
|------|-------|
| Ambiente | Todas as operações containerizadas (diretrizes DEVELOPMENT_ORIENTATION) |
| Migrações | Alembic – executar manualmente: `docker compose exec api alembic upgrade heads` |
| Agregados Contínuos | Criados fora da transação Alembic (limitação TimescaleDB) |
| Jobs CI | Lint, testes (cobertura ≥80%), escaneamento de segurança, validação de hash de modelo, matriz de validação ML opcional |
| Endurecimento de Instalação Poetry | Mudou para instalação determinística baseada em pip com retries |
| Testes de Carga | Cenários Locust (API + drift + interações de modelo) |
| Testes de Integração | FastAPI assíncrono + BD + Redis + testes de resiliência Toxiproxy |

Auth e Rede:

- Autenticação API via `X-API-Key`; UI envia cabeçalhos automaticamente (veja `API_KEY` no `.env`)
- Rede entre serviços Docker via nomes de serviço (`API_BASE_URL=http://api:8000` na UI)

Destaques do Makefile (`smart-maintenance-saas/Makefile`):

- `make build-ml` / `make rebuild-ml` – construir imagem ML
- `make synthetic-forecast` / `make synthetic-anomaly` – executar notebooks de treinamento
- `make classification-gauntlet` / `make vibration-gauntlet` / `make audio-gauntlet`
- `make run-final-analysis` – relatório project gauntlet
- `make test-features` – testes de engenharia de características
- `make logs-api` / `make logs-mlflow` / `make logs-db`

---

## 🔀 Migração para Microsserviços (Gatilho Futuro)

Serviços scaffolded mas dormentes:

- prediction_service (porta 8001)
- anomaly_service (porta 8002)

Gatilhos de ativação (docs/MICROSERVICE_MIGRATION_STRATEGY.md):

- Latência P95 > 50ms sustentada
- Throughput de API >200 req/s sustentado
- Atrito de acoplamento de equipe/deployment
- Saturação elevada de CPU/memória (>80%)

Padrão strangler gradual: migrar endpoints de inferência ML e análise primeiro.

---

## 📊 Principais Destaques de Performance

| Métrica | Resultado |
|--------|--------|
| Carga (50 usuários / 3m) | Pico 103,8 RPS |
| API P95 | 2 ms |
| Ganho de Agregação BD | 37,3% mais rápido (CAGG) |
| Melhoria de Previsão | Prophet ajustado +20,86% MAE vs ingênuo |
| Classificação (Pump) | 100% acurácia, ROC-AUC perfeito |
| Endpoint de Drift P95 | ~3 ms |
| Dataset (Base Sintética) | 9.000 leituras / 15 sensores |

---

## 🧪 Estratégia de Testes

| Camada | Foco |
|-------|-------|
| Unidade | Transformadores de características, utilitários de modelo |
| Integração | BD + Redis + ingestão + estatísticas de drift |
| E2E | Fluxo de trabalho de detecção de drift + carregamento de modelo |
| Carga | Concorrência de endpoint misto + estresse de ingestão |
| Resiliência | Latência induzida, timeouts (Toxiproxy) |
| Segurança | Limite de taxa, rejeição de auth, escaneamento de dependências |
| Integridade ML | Verificação de hash de modelo + presença de artefato |

---

## 🔐 Runbook Operacional (Essenciais)

| Ação | Comando |
|--------|---------|
| Aplicar migrações | `docker compose exec api alembic upgrade heads` |
| Reconstruir imagem ML | `make build-ml` |
| Executar notebook de previsão | `make train-forecast` |
| Listar modelos MLflow | Abrir <http://localhost:5000> |
| Verificação manual de drift | POST `/api/v1/ml/check_drift` |
| Forçar retreino (manual) | Gatilho via agente de retreino ou notebook |
| Exportação incremental de dados | Veja seção Exportação de Dados |

---


## 📄 Licença

MIT – veja [LICENSE](./LICENSE)

---

## 🧾 Autoridade do Changelog

Todas as reivindicações arquiteturais e de características rastreiam para: `./smart-maintenance-saas/docs/30-day-sprint-changelog.md`

---

## 🙋 Suporte

1. Verificar métricas/logs
2. Verificar saúde do BD e Redis
3. Confirmar persistência do registro de modelos
4. Executar endpoint de drift com sensor conhecido
5. Inspecionar logs do agente de retreino em eventos de drift

---