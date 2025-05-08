# Documentação Final – Fase 1: Smart Maintenance SaaS

**Desafio FIAP SP em parceria com Hermes Reply**  
**Autor:** Yan Pimentel Cotta et al.  
**Data de Entrega:** 08 de Maio de 2025, 23h59  
**Versão:** 1.3  

---

## 1. Introdução

Este documento consolida a Fase 1 do projeto **Smart Maintenance SaaS**, uma solução inovadora de manutenção preditiva para o setor industrial, desenvolvida em parceria com a **Hermes Reply**. Nosso objetivo é atender ao desafio FIAP SP, entregando uma proposta técnica robusta, clara e profissional, digna de apresentação a uma grande empresa de tecnologia.

### 1.1 Contextualização do Problema
Empresas industriais enfrentam interrupções inesperadas na produção devido a falhas em equipamentos críticos, resultando em paradas não planejadas, perda de produtividade e altos custos de manutenção corretiva. A abordagem tradicional de manutenção reativa ou preventiva é ineficiente, pois não prevê falhas com precisão, levando a intervenções desnecessárias ou tardias. Com a Indústria 4.0, a integração de **IoT**, **IA** e **análise de dados em tempo real** oferece uma oportunidade para transformar a gestão de ativos, promovendo uma manutenção proativa e inteligente.

### 1.2 Objetivo do Projeto
Desenvolver uma plataforma SaaS multi-tenant escalável para manutenção preditiva de equipamentos industriais, utilizando dados de sensores em tempo real. A solução deve:
- Monitorar equipamentos continuamente via **IoT**.
- Detectar anomalias e prever falhas com modelos de **Machine Learning**.
- Automatizar alertas e agendamentos de manutenção.
- Oferecer um dashboard interativo e relatórios inteligentes.
- Garantir escalabilidade, segurança e alta disponibilidade.

### 1.3 Entregável da Fase 1
Esta documentação detalha a metodologia, o **technology stack**, o pipeline de dados, a arquitetura do sistema e a validação dos requisitos da Fase 1. Inclui três representações visuais (diagramas Mermaid) e um plano de desenvolvimento, atendendo aos padrões de uma apresentação técnica de alto nível.

---

## 2. Arquitetura do Sistema

### 2.1 Visão Geral
A **Smart Maintenance SaaS** é uma plataforma multi-tenant baseada em nuvem, projetada para suportar múltiplos clientes com isolamento de dados seguro. Ela utiliza uma arquitetura modular com um sistema multi-agente no backend, orquestrado por protocolos avançados como **Google’s Agent-to-Agent (A2A)**, **Model Context Protocol (MCP)** e **Agent Communication Protocol (ACP)**. A solução integra **IoT**, **IA** e capacidades de **human-in-the-loop**, oferecendo monitoramento em tempo real, análise preditiva, agendamento automatizado e relatórios inteligentes.

### 2.2 Componentes Principais

#### 2.2.1 Camada IoT
- **Funcionalidade**: Coleta dados em tempo real de sensores industriais.
- **Tecnologias**:
  - **ESP32**: Microcontroladores para aquisição de dados (e.g., temperatura, vibração, pressão).
  - **MQTT**: Protocolo leve para transmissão de dados a um broker (e.g., Mosquitto).
  - **Apache Kafka**: Streaming de dados tolerante a falhas com alta taxa de transferência.
  - **AWS IoT Greengrass**: Pré-processamento na borda para reduzir latência.
- **Fluxo de Dados**: Sensores → MQTT → Kafka → Backend.

#### 2.2.2 Backend: Sistema Multi-Agente
- **Funcionalidade**: Processa dados, detecta anomalias, prevê falhas e automatiza fluxos de trabalho.
- **Tecnologias**:
  - **Google A2A, MCP, ACP**: Comunicação segura e integração de ferramentas externas.
  - **LangChain/CrewAI**: Frameworks para implementação de agentes.
  - **LLMs**: OpenAI API para deploy rápido ou modelos locais (e.g., LLaMA) para otimização de custos.
  - **FastAPI**: API RESTful para comunicação com o frontend.
  - **gRPC**: Comunicação eficiente entre microsserviços.
- **Agentes**:
  - **Monitor Agent**: Detecta anomalias com modelos de ML (e.g., Isolation Forest, Autoencoders).
  - **Validator Agent**: Confirma anomalias com lógica híbrida (regras + inferência bayesiana).
  - **Orchestrator Agent**: Coordena agentes usando aprendizado por reforço para otimizar decisões.
  - **Scheduler Agent**: Agenda manutenções via APIs externas (e.g., Google Calendar).
  - **Reporter Agent**: Gera relatórios e envia e-mails (e.g., Gmail API).
  - **Learning Agent**: Otimiza o sistema com base em dados históricos e feedback.
  - **Human-in-the-Loop**: Permite intervenção humana em decisões críticas.

#### 2.2.3 Frontend
- **Funcionalidade**: Dashboard interativo para monitoramento em tempo real e controle humano.
- **Tecnologias**:
  - **Next.js**: Framework React com renderização server-side.
  - **Node.js**: Runtime para integrações.
  - **TypeScript**: Segurança de tipos.
  - **Tailwind CSS**: Estilização responsiva.
  - **D3.js**: Visualizações avançadas de dados.

#### 2.2.4 Banco de Dados
- **Funcionalidade**: Armazena dados de sensores, logs de agentes e registros de manutenção.
- **Tecnologias**:
  - **PostgreSQL**: Banco relacional.
  - **TimescaleDB**: Extensão para séries temporais.
  - **Amazon S3**: Data Lake para histórico bruto.

#### 2.2.5 Infraestrutura em Nuvem
- **Funcionalidade**: Garante escalabilidade, segurança e alta disponibilidade.
- **Tecnologias**:
  - **AWS**: IoT Core, EC2, RDS, Lambda, SNS, ECS.
  - **Docker**: Containerização de microsserviços.
  - **Kubernetes**: Orquestração e escalonamento automático.

### 2.3 Diagrama de Arquitetura Geral
```mermaid
graph TD
    subgraph "Camada IoT"
        A[Sensores ESP32] -->|MQTT| B[Broker MQTT]
        B -->|Kafka Producer| C[Apache Kafka]
    end
    subgraph "Backend: Sistema Multi-Agente"
        C --> D[Monitor Agent]
        D --> E[Validator Agent]
        E --> F[Orchestrator Agent]
        F --> G[Scheduler Agent]
        F --> H[Reporter Agent]
        F --> I[Learning Agent]
        F <--> J[Human-in-the-Loop]
    end
    subgraph "Banco de Dados"
        C --> K[(PostgreSQL/TimescaleDB)]
        F --> K
        C --> L[S3 Data Lake]
    end
    subgraph "Frontend"
        F -->|REST/gRPC| M[Next.js Dashboard]
    end
    subgraph "Infraestrutura em Nuvem"
        B --> N[AWS - IoT Core, EC2, RDS, SNS]
        C --> N
        K --> N
        D --> N
        F --> N
    end
```

---

## 3. Stack Tecnológico

A tabela abaixo detalha as tecnologias por camada, com justificativas para cada escolha:

| **Camada**         | **Tecnologias**                       | **Justificativa**                              |
|--------------------|----------------------------------------|------------------------------------------|
| **IoT**           | ESP32, MQTT, Apache Kafka, AWS IoT Greengrass | Coleta robusta, streaming escalável e pré-processamento na borda |
| **Backend**       | Python, FastAPI, gRPC, LangChain/CrewAI, Google A2A/MCP/ACP, OpenAI API ou LLMs Locais | Sistema multi-agente modular, comunicação eficiente e APIs escaláveis |
| **Frontend**      | Next.js, Node.js, TypeScript, Tailwind CSS, D3.js | Dashboard interativo, responsivo e com visualizações avançadas |
| **Banco de Dados** | PostgreSQL, TimescaleDB, Amazon S3    | Armazenamento estruturado, séries temporais e histórico bruto |
| **Infraestrutura** | AWS (IoT Core, EC2, RDS, Lambda, SNS, ECS), Docker, Kubernetes | Escalabilidade, segurança e alta disponibilidade |
| **ML Ops**        | TensorFlow/PyTorch, Scikit-learn, MLflow, SageMaker | Ciclo completo de desenvolvimento e deploy de modelos |
| **Observabilidade** | Prometheus, Grafana, AWS CloudWatch  | Métricas, logs e alertas para SLO/SLI |
| **Segurança**     | AWS Cognito, OAuth2, mTLS, TLS, Criptografia at-rest | Autenticação, autorização e proteção de dados |

### 3.1 Protocolos de Agentes
- **Google’s A2A**: Comunicação bidirecional confiável entre agentes via **gRPC** com **mTLS**.
- **MCP**: Troca de contexto de modelos e acesso a ferramentas externas (e.g., APIs de calendário e e-mail).
- **ACP**: Orquestra mensagens, mantendo histórico e consistência.

---

## 4. Funcionalidade

### 4.1 Características Principais
1. **Processamento em Tempo Real**: Ingestão contínua via Kafka e análise com **KSQL/Flink**.
2. **Análise Preditiva**: Modelos de ML (e.g., LSTM, regressão) preveem falhas.
3. **Alertas Automatizados**: Notificações via **AWS SNS** (e-mail, SMS).
4. **Agendamento de Manutenção**: Otimizado por algoritmos genéticos e APIs externas.
5. **Dashboard Interativo**: Visualização em tempo real com controle humano.
6. **Relatórios Inteligentes**: Insights gerados por NLP e recomendações automáticas.

### 4.2 Fluxo de Trabalho Multi-Agente
1. **Monitor Agent**: Detecta anomalia → Validator Agent.
2. **Validator Agent**: Confirma → Orchestrator Agent.
3. **Orchestrator Agent**: Decide ação → Scheduler/Reporter Agents.
4. **Scheduler Agent**: Agenda manutenção via API.
5. **Reporter Agent**: Envia relatórios e registra logs.
6. **Learning Agent**: Otimiza com base em feedback.
7. **Human-in-the-Loop**: Intervenção manual quando necessário.

---

## 5. Representações Visuais

### 5.1 Diagrama de Interação Multi-Agente
```mermaid
graph TD
    A[Monitor Agent] -->|A2A| B[Validator Agent]
    B -->|A2A| C[Orchestrator Agent]
    C -->|A2A| D[Scheduler Agent]
    C -->|A2A| E[Reporter Agent]
    C -->|A2A| F[Learning Agent]
    C <--> G[Human-in-the-Loop]
    D -->|MCP: Calendar API| H[External Tool]
    E -->|MCP: Gmail API| H
```

### 5.2 Diagrama de Fluxo de Dados em Tempo Real
```mermaid
sequenceDiagram
    participant S as ESP32
    participant M as MQTT Broker
    participant K as Apache Kafka
    participant Mon as Monitor Agent
    participant DB as TimescaleDB
    participant UI as Dashboard
    S->>M: Publica dados
    M->>K: Envia para Kafka
    K->>Mon: Consome eventos
    Mon->>DB: Armazena dados brutos
    Mon->>Orchestrator: Envia anomalia
    Orchestrator->>DB: Registra decisão
    Orchestrator->>UI: Atualiza dashboard
    Orchestrator->>SNS: Envia alerta
```

---

## 6. Pipeline de Implementação

### 6.1 Passos da Fase 1
1. **Análise de Requisitos**: Estudo das necessidades industriais e definição de constraints SaaS.
2. **Seleção de Tecnologias**: Escolha de frameworks e LLMs.
3. **Design de Arquitetura**: Mapeamento de interações e pipeline de dados.
4. **Simulação**: Configuração de Wokwi e broker MQTT.
5. **Documentação**: Redação deste documento com diagramas.

### 6.2 Cronograma para Fases Futuras
| **Atividade**                  | **Responsável**   | **Prazo**    |
|--------------------------------|-------------------|--------------|
| Provisionamento de Infra       | Equipe DevOps     | 10/05/2025   |
| Desenvolvimento de Agentes     | Equipe Backend    | 17/05/2025   |
| Treinamento de Modelos         | Equipe ML         | 24/05/2025   |
| Desenvolvimento do Dashboard   | Equipe Frontend   | 31/05/2025   |
| Testes de Integração          | QA                | 07/06/2025   |
| Ajustes Finais                 | Todos             | 14/06/2025   |

---

## 7. Justificativas e Melhorias

### 7.1 Justificativas
- **Kafka**: Streaming confiável e escalável com **KSQL/Flink** para análises em tempo real.
- **Learning Agent**: Adaptação contínua baseada em dados históricos.
- **Edge Computing**: Redução de latência com **AWS IoT Greengrass**.
- **Blockchain**: Logs imutáveis para auditoria (futuro).

### 7.2 Sugestões de Aprimoramento
- **ML Avançado**: Integração de **AutoML** para otimização automática de modelos.
- **Data Lake em S3**: Análise de longo prazo e conformidade.
- **Microserviços Desacoplados**: Escalonamento independente via **gRPC**.

---

## 8. Validação dos Requisitos da Fase 1
- **Documentação Completa**: Metodologia, tecnologias, pipeline e arquitetura detalhados.
- **Coerência Técnica**: Solução modular, segura e escalável.
- **Profissionalismo**: Estrutura organizada, diagramas claros e terminologia técnica.
- **Entrega**: Disponível via GitHub com README e diagramas exportáveis.

---

## 9. Conclusão
Esta proposta estabelece uma base sólida para o **Smart Maintenance SaaS**, alinhada aos requisitos do desafio FIAP. A arquitetura é inovadora, escalável e pronta para prototipação na Fase 2. Aguardamos feedback da Hermes Reply e tutores para ajustes e avanços.