# Load Testing Instructions for Smart Maintenance SaaS

**🇧🇷 Para usuários brasileiros:** [**Ir para a versão em português**](#instruções-de-teste-de-carga-para-smart-maintenance-saas-português)

## 📚 Documentation Navigation

This document is part of the Smart Maintenance SaaS documentation suite. For complete system understanding, please also refer to:

- **[Backend README](../README.md)** - Docker deployment and getting started guide
- **[System Screenshots](./SYSTEM_SCREENSHOTS.md)** - Complete visual system walkthrough with screenshots
- **[System and Architecture](./SYSTEM_AND_ARCHITECTURE.md)** - Complete system architecture and component overview
- **[Future Roadmap](./FUTURE_ROADMAP.md)** - Strategic vision and planned enhancements
- **[Deployment Status](./DEPLOYMENT_STATUS.md)** - Current deployment status and container information
- **[Performance Baseline](./PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics baseline
- **[API Documentation](./api.md)** - Complete REST API reference and usage examples  
- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Project Overview](../../README.md)** - High-level project description and objectives

---

## Overview
This document provides comprehensive instructions for running load tests against the Smart Maintenance SaaS API using Locust.

## Quick Start with Docker

1. **Start the Complete System**:
   ```bash
   cd smart-maintenance-saas
   docker compose up -d
   ```

2. **Verify System Health**:
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy"}
   ```

3. **Run Load Tests**:
   ```bash
   # Using containerized system
   poetry install  # Install test dependencies
   poetry run locust -f locustfile.py --host=http://localhost:8000
   ```

## Alternative: Local Development Setup

1. **Database Setup**: Ensure PostgreSQL is running and tables are migrated:
   ```bash
   poetry run alembic upgrade head
   ```

## Load Test Configuration

The `locustfile.py` currently implements a single unified user class with combined behaviors:

### WebsiteUser (Combined User Class)

- **Purpose**: Simulates both IoT sensor data ingestion and health monitoring
- **Active Endpoints**: `/api/v1/data/ingest`, `/health`
- **Authentication**: Uses `X-API-Key` header with value `your_default_api_key`
- **Wait Time**: 1-3 seconds between requests
- **Active Tasks**:
  - `ingest_normal_sensor_data` (Weight: 10) - Normal sensor readings with realistic data
  - Health check on user initialization
- **Data Generated**: Temperature, vibration, pressure, humidity, and flow rate sensor readings

**⚠️ Note**: Report generation endpoints (`/api/v1/reports/generate`) are currently **commented out** in the load test script due to datetime parsing issues. They will be re-enabled once the issues are resolved.

## Running Load Tests

### Basic Load Test
```bash
cd smart-maintenance-saas
poetry run locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to configure and start the test.

### Command Line Load Test (Headless)
```bash
# Light load test (10 users, 2 spawn rate, 60 seconds)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless

# Medium load test (50 users, 5 spawn rate, 5 minutes)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless

# Heavy load test (100 users, 10 spawn rate, 10 minutes)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless
```

### Load Test with HTML Report
```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless --html load_test_report.html
```

## Test Scenarios

### Scenario 1: Normal Operations Load

- **Users**: 25 (primarily sensor data ingestion)
- **Duration**: 5 minutes
- **Purpose**: Test normal operational load for sensor data processing

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 25 --spawn-rate 3 --run-time 5m --headless --html normal_load_report.html
```

### Scenario 2: Peak Load Testing

- **Users**: 100 (high-frequency sensor data ingestion)
- **Duration**: 10 minutes
- **Purpose**: Test system under peak sensor data load conditions

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless --html peak_load_report.html
```

### Scenario 3: Spike Testing

- **Users**: Gradually increase from 10 to 200
- **Duration**: 15 minutes
- **Purpose**: Test system behavior under sudden load spikes

```bash
# Run step load test manually through web UI or use custom step load script
poetry run locust -f locustfile.py --host=http://localhost:8000
# Configure in web UI: Start with 10 users, then increase to 50, 100, 150, 200 every 3 minutes
```

### Scenario 4: Endurance Testing

- **Users**: 30 (moderate consistent load)
- **Duration**: 30 minutes
- **Purpose**: Test system stability over extended periods

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 30 --spawn-rate 2 --run-time 30m --headless --html endurance_test_report.html
```

## Performance Metrics to Monitor

### Application Metrics
- **Response Time**: 
  - 95th percentile < 500ms for data ingestion
  - 95th percentile < 2s for report generation
- **Throughput**: Requests per second
- **Error Rate**: Should be < 1% under normal load
- **Success Rate**: Should be > 99% under normal load

### System Metrics (Monitor with `htop`, `iostat`, etc.)
- **CPU Usage**: Should not exceed 80% sustained
- **Memory Usage**: Monitor for memory leaks
- **Database Connections**: Monitor PostgreSQL connection pool
- **Disk I/O**: Database write performance

### Database Metrics
- **Connection Pool**: Monitor active/idle connections
- **Query Performance**: Slow query logs
- **Lock Contention**: Monitor database locks
- **Storage Growth**: Monitor data ingestion impact

## Expected Results

### Normal Load (25 users)

- **Sensor Ingestion**: ~60-120 requests/minute
- **Average Response Time**: < 200ms for data ingestion
- **Error Rate**: < 0.5%

### Peak Load (100 users)

- **Sensor Ingestion**: ~300-600 requests/minute
- **Average Response Time**: < 500ms for data ingestion
- **Error Rate**: < 2%

**Note**: Report generation metrics are not currently available due to the endpoints being temporarily disabled in the load test script.

### Breaking Point Identification
Run increasing load tests to identify:
- **Maximum Throughput**: Requests/second before performance degrades
- **Response Time Degradation Point**: When 95th percentile > acceptable limits
- **Error Rate Threshold**: When error rate > 5%
- **Resource Exhaustion**: CPU, memory, or database connection limits

## Troubleshooting Common Issues

### High Error Rates
1. Check API server logs: `docker logs <container_name>` or application logs
2. Verify database connectivity and performance
3. Check for authentication/authorization issues (API key)
4. Monitor resource usage (CPU, memory, disk)

### Poor Performance
1. Check database query performance with EXPLAIN ANALYZE
2. Monitor database connection pool utilization
3. Review application logging level (reduce in production)
4. Check for database locks or long-running transactions

### Test Setup Issues
1. Ensure API server is running and accessible
2. Verify database migrations are up to date
3. Check API key configuration in both server and test script
4. Confirm network connectivity between test client and server

## Post-Test Analysis

### Report Analysis
1. **Response Time Distribution**: Look for outliers and p95/p99 values
2. **Failure Analysis**: Categorize and investigate failed requests
3. **Throughput Trends**: Identify throughput degradation points
4. **Resource Correlation**: Compare performance metrics with system resource usage

### Optimization Recommendations
Based on test results, consider:
1. **Database Indexing**: Add indexes for frequently queried columns
2. **Connection Pooling**: Tune database connection pool settings
3. **Caching**: Implement caching for frequently accessed data
4. **Rate Limiting**: Add rate limiting to prevent abuse
5. **Horizontal Scaling**: Consider load balancing and multiple instances

## Load Test Automation

For CI/CD integration, create automated performance tests:

```bash
#!/bin/bash
# performance_test.sh

echo "Starting performance regression test..."

# Run light load test
poetry run locust -f locustfile.py --host=http://localhost:8000 \
  --users 20 --spawn-rate 2 --run-time 2m --headless \
  --html performance_regression_report.html

# Check exit code and parse results for performance regression
if [ $? -eq 0 ]; then
    echo "Performance test passed"
    exit 0
else
    echo "Performance test failed"
    exit 1
fi
```

## Summary

This load testing setup provides comprehensive coverage of the Smart Maintenance SaaS API under various load conditions. Regular execution of these tests will help identify performance bottlenecks, ensure system stability, and guide scaling decisions.

Key Benefits:
- **Realistic Load Simulation**: Mimics actual IoT sensor ingestion and reporting patterns
- **Scalable Test Scenarios**: From normal operations to stress testing
- **Comprehensive Metrics**: Response times, throughput, error rates
- **Automated Reporting**: HTML reports for analysis and documentation
- **CI/CD Ready**: Can be integrated into deployment pipelines

---

# 🇧🇷 Instruções de Teste de Carga para Smart Maintenance SaaS (Português)

**🇺🇸 For English users:** [**Go to English version**](#load-testing-instructions-for-smart-maintenance-saas)

## 📚 Navegação da Documentação

Este documento faz parte da suíte de documentação do Smart Maintenance SaaS. Para compreensão completa do sistema, consulte também:

- **[README do Backend](../README.md)** - Guia de deployment Docker e primeiros passos
- **[Capturas de Tela do Sistema](./SYSTEM_SCREENSHOTS.md)** - Tour visual completo do sistema com capturas de tela
- **[Sistema e Arquitetura](./SYSTEM_AND_ARCHITECTURE.md)** - Visão geral completa da arquitetura e componentes do sistema
- **[Roadmap Futuro](./FUTURE_ROADMAP.md)** - Visão estratégica e melhorias planejadas
- **[Status de Deployment](./DEPLOYMENT_STATUS.md)** - Status atual de deployment e informações de containers
- **[Baseline de Performance](./PERFORMANCE_BASELINE.md)** - Resultados de testes de carga e baseline de métricas de performance
- **[Documentação da API](./api.md)** - Referência completa da API REST e exemplos de uso
- **[Documentação de Testes](../tests/README.md)** - Guia de organização e execução de testes
- **[Visão Geral do Projeto](../../README.md)** - Descrição de alto nível do projeto e objetivos

---

## Visão Geral

Este documento fornece instruções abrangentes para executar testes de carga contra a API do Smart Maintenance SaaS usando Locust.

## Início Rápido com Docker

1. **Iniciar o Sistema Completo**:
   ```bash
   cd smart-maintenance-saas
   docker compose up -d
   ```

2. **Verificar a Saúde do Sistema**:
   ```bash
   curl http://localhost:8000/health
   # Esperado: {"status":"healthy"}
   ```

3. **Executar Testes de Carga**:
   ```bash
   # Usando sistema containerizado
   poetry install  # Instalar dependências de teste
   poetry run locust -f locustfile.py --host=http://localhost:8000
   ```

## Alternativa: Configuração de Desenvolvimento Local

1. **Configuração do Banco de Dados**: Certifique-se de que o PostgreSQL está rodando e as tabelas foram migradas:
   ```bash
   poetry run alembic upgrade head
   ```

## Configuração do Teste de Carga

O `locustfile.py` atualmente implementa uma única classe de usuário unificada com comportamentos combinados:

### WebsiteUser (Classe de Usuário Combinada)

- **Propósito**: Simula tanto ingestão de dados de sensores IoT quanto monitoramento de saúde
- **Endpoints Ativos**: `/api/v1/data/ingest`, `/health`
- **Autenticação**: Usa header `X-API-Key` com valor `your_default_api_key`
- **Tempo de Espera**: 1-3 segundos entre requisições
- **Tarefas Ativas**:
  - `ingest_normal_sensor_data` (Peso: 10) - Leituras normais de sensores com dados realistas
  - Verificação de saúde na inicialização do usuário
- **Dados Gerados**: Leituras de sensores de temperatura, vibração, pressão, umidade e taxa de fluxo

**⚠️ Nota**: Os endpoints de geração de relatórios (`/api/v1/reports/generate`) estão atualmente **comentados** no script de teste de carga devido a problemas de parsing de datetime. Eles serão reabilitados assim que os problemas forem resolvidos.

## Executando Testes de Carga

### Teste de Carga Básico

```bash
cd smart-maintenance-saas
poetry run locust -f locustfile.py --host=http://localhost:8000
```

Em seguida, abra <http://localhost:8089> em seu navegador para configurar e iniciar o teste.

### Teste de Carga por Linha de Comando (Sem Interface)

```bash
# Teste de carga leve (10 usuários, taxa de spawn 2, 60 segundos)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless

# Teste de carga médio (50 usuários, taxa de spawn 5, 5 minutos)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless

# Teste de carga pesado (100 usuários, taxa de spawn 10, 10 minutos)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless
```

### Teste de Carga com Relatório HTML

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless --html relatorio_teste_carga.html
```

## Cenários de Teste

### Cenário 1: Carga de Operações Normais

- **Usuários**: 25 (principalmente ingestão de dados de sensores)
- **Duração**: 5 minutos
- **Propósito**: Testar carga operacional normal para processamento de dados de sensores

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 25 --spawn-rate 3 --run-time 5m --headless --html relatorio_carga_normal.html
```

### Cenário 2: Teste de Carga de Pico

- **Usuários**: 100 (ingestão de dados de sensores de alta frequência)
- **Duração**: 10 minutos
- **Propósito**: Testar sistema sob condições de carga de pico de dados de sensores

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless --html relatorio_carga_pico.html
```

### Cenário 3: Teste de Picos de Carga

- **Usuários**: Aumentar gradualmente de 10 para 200
- **Duração**: 15 minutos
- **Propósito**: Testar comportamento do sistema sob picos súbitos de carga

```bash
# Executar teste de carga em etapas manualmente através da UI web ou usar script de carga em etapas personalizado
poetry run locust -f locustfile.py --host=http://localhost:8000
# Configurar na UI web: Começar com 10 usuários, depois aumentar para 50, 100, 150, 200 a cada 3 minutos
```

### Cenário 4: Teste de Resistência

- **Usuários**: 30 (carga moderada consistente)
- **Duração**: 30 minutos
- **Propósito**: Testar estabilidade do sistema por períodos prolongados

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 30 --spawn-rate 2 --run-time 30m --headless --html relatorio_teste_resistencia.html
```

## Métricas de Performance para Monitorar

### Métricas da Aplicação

- **Tempo de Resposta**:
  - 95º percentil < 500ms para ingestão de dados
  - 95º percentil < 2s para geração de relatórios
- **Throughput**: Requisições por segundo
- **Taxa de Erro**: Deve ser < 1% sob carga normal
- **Taxa de Sucesso**: Deve ser > 99% sob carga normal

### Métricas do Sistema (Monitorar com `htop`, `iostat`, etc.)

- **Uso de CPU**: Não deve exceder 80% sustentado
- **Uso de Memória**: Monitorar vazamentos de memória
- **Conexões do Banco de Dados**: Monitorar pool de conexões PostgreSQL
- **I/O de Disco**: Performance de escrita do banco de dados

### Métricas do Banco de Dados

- **Pool de Conexões**: Monitorar conexões ativas/inativas
- **Performance de Consultas**: Logs de consultas lentas
- **Contenção de Locks**: Monitorar locks do banco de dados
- **Crescimento de Armazenamento**: Monitorar impacto da ingestão de dados

## Resultados Esperados

### Carga Normal (25 usuários)

- **Ingestão de Sensores**: ~60-120 requisições/minuto
- **Tempo Médio de Resposta**: < 200ms para ingestão de dados
- **Taxa de Erro**: < 0,5%

### Carga de Pico (100 usuários)

- **Ingestão de Sensores**: ~300-600 requisições/minuto
- **Tempo Médio de Resposta**: < 500ms para ingestão de dados
- **Taxa de Erro**: < 2%

**Nota**: As métricas de geração de relatórios não estão disponíveis atualmente devido aos endpoints estarem temporariamente desabilitados no script de teste de carga.

### Identificação do Ponto de Ruptura

Execute testes de carga crescente para identificar:

- **Throughput Máximo**: Requisições/segundo antes da degradação da performance
- **Ponto de Degradação do Tempo de Resposta**: Quando o 95º percentil > limites aceitáveis
- **Limite da Taxa de Erro**: Quando a taxa de erro > 5%
- **Esgotamento de Recursos**: Limites de CPU, memória ou conexão do banco de dados

## Resolução de Problemas Comuns

### Altas Taxas de Erro

1. Verificar logs do servidor da API: `docker logs <nome_container>` ou logs da aplicação
2. Verificar conectividade e performance do banco de dados
3. Verificar problemas de autenticação/autorização (chave API)
4. Monitorar uso de recursos (CPU, memória, disco)

### Performance Ruim

1. Verificar performance de consultas do banco com EXPLAIN ANALYZE
2. Monitorar utilização do pool de conexões do banco de dados
3. Revisar nível de logging da aplicação (reduzir em produção)
4. Verificar locks do banco de dados ou transações de longa duração

### Problemas de Configuração de Teste

1. Garantir que o servidor da API está rodando e acessível
2. Verificar se as migrações do banco de dados estão atualizadas
3. Verificar configuração da chave API tanto no servidor quanto no script de teste
4. Confirmar conectividade de rede entre cliente de teste e servidor

## Análise Pós-Teste

### Análise de Relatório

1. **Distribuição do Tempo de Resposta**: Procurar outliers e valores p95/p99
2. **Análise de Falhas**: Categorizar e investigar requisições falhadas
3. **Tendências de Throughput**: Identificar pontos de degradação do throughput
4. **Correlação de Recursos**: Comparar métricas de performance com uso de recursos do sistema

### Recomendações de Otimização

Com base nos resultados dos testes, considere:

1. **Indexação do Banco de Dados**: Adicionar índices para colunas consultadas frequentemente
2. **Pool de Conexões**: Ajustar configurações do pool de conexões do banco de dados
3. **Cache**: Implementar cache para dados acessados frequentemente
4. **Rate Limiting**: Adicionar limitação de taxa para prevenir abuso
5. **Escalonamento Horizontal**: Considerar balanceamento de carga e múltiplas instâncias

## Automação de Testes de Carga

Para integração CI/CD, crie testes de performance automatizados:

```bash
#!/bin/bash
# teste_performance.sh

echo "Iniciando teste de regressão de performance..."

# Executar teste de carga leve
poetry run locust -f locustfile.py --host=http://localhost:8000 \
  --users 20 --spawn-rate 2 --run-time 2m --headless \
  --html relatorio_regressao_performance.html

# Verificar código de saída e analisar resultados para regressão de performance
if [ $? -eq 0 ]; then
    echo "Teste de performance passou"
    exit 0
else
    echo "Teste de performance falhou"
    exit 1
fi
```

## Resumo

Esta configuração de teste de carga fornece cobertura abrangente da API do Smart Maintenance SaaS sob várias condições de carga. A execução regular destes testes ajudará a identificar gargalos de performance, garantir estabilidade do sistema e orientar decisões de escalonamento.

Principais Benefícios:

- **Simulação de Carga Realista**: Imita padrões reais de ingestão de sensores IoT e relatórios
- **Cenários de Teste Escaláveis**: De operações normais a testes de stress
- **Métricas Abrangentes**: Tempos de resposta, throughput, taxas de erro
- **Relatórios Automatizados**: Relatórios HTML para análise e documentação
- **Pronto para CI/CD**: Pode ser integrado em pipelines de deployment
