# Smart Maintenance SaaS - Desafio FIAP x Hermes Reply

## Sobre o Projeto

O Smart Maintenance SaaS é uma solução inovadora de manutenção preditiva para o setor industrial, desenvolvida como parte do desafio FIAP SP em parceria com a Hermes Reply. O projeto utiliza tecnologias avançadas de IoT, IA e análise de dados em tempo real para transformar a gestão de ativos industriais.

## Funcionalidades Principais

- 🔍 Monitoramento contínuo de equipamentos via IoT
- 🤖 Detecção de anomalias e previsão de falhas com Machine Learning
- ⚡ Alertas automáticos e agendamento inteligente de manutenção
- 📊 Dashboard interativo e relatórios inteligentes
- ⚙️ Sistema multi-agente com arquitetura escalável

## Stack Tecnológico

### IoT e Edge Computing
- ESP32 para aquisição de dados
- MQTT para comunicação
- Apache Kafka para streaming de dados
- AWS IoT Greengrass para processamento na borda

### Backend (Sistema Multi-Agente)
- Python com FastAPI
- gRPC para comunicação entre serviços
- LangChain/CrewAI para implementação de agentes
- Integração com LLMs (OpenAI API ou modelos locais)

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- D3.js para visualizações

### Banco de Dados
- PostgreSQL com TimescaleDB
- Amazon S3 para Data Lake

### Infraestrutura Cloud
- AWS (IoT Core, EC2, RDS, Lambda, SNS, ECS)
- Docker e Kubernetes

## Arquitetura

O sistema é composto por diferentes agentes especializados:
- Monitor Agent: Detecção de anomalias
- Validator Agent: Confirmação de anomalias
- Orchestrator Agent: Coordenação de decisões
- Scheduler Agent: Agendamento de manutenções
- Reporter Agent: Geração de relatórios
- Learning Agent: Otimização contínua

## Instalação e Uso

*Documentação em desenvolvimento para a Fase 2 do projeto*

## Equipe

- Yan Pimentel Cotta / RM: 562836

## Status do Projeto

- ✅ Fase 1: Documentação e Arquitetura (Atual)
- 🔄 Fase 2: Implementação (Em breve)


## Licença

Este projeto está sob a licença incluída no arquivo [LICENSE](LICENSE).

## Documentação Detalhada

Para mais informações sobre a arquitetura e implementação técnica, consulte o arquivo [system_documentation_and_architecture.md](system_documentation_and_architecture.md).

---

**Data de Entrega:** 08 de Maio de 2025
**Versão:** 1.3