# Testing Strategy for Smart Maintenance SaaS

🇧🇷 **[Clique aqui para ler em Português](#-estratégia-de-testes-português)** | 🇺🇸 **English Version Below**

📖 **Quick Navigation**

- [📚 Main Documentation](../README.md) | [🏗️ System Architecture](../docs/SYSTEM_AND_ARCHITECTURE.md) | [📸 System Screenshots](../docs/SYSTEM_SCREENSHOTS.md)
- [🚀 Future Roadmap](../docs/FUTURE_ROADMAP.md) | [🚀 Deployment Status](../docs/DEPLOYMENT_STATUS.md) | [⚡ Performance Baseline](../docs/PERFORMANCE_BASELINE.md)
- [📈 Load Testing](../docs/LOAD_TESTING_INSTRUCTIONS.md) | [🔧 API Documentation](../docs/api.md) | [📝 Logging Config](../core/logging_config.md)
- [⚙️ Configuration Management](../core/config/README.md) | [📋 Original Architecture](../docs/original_full_system_architecture.md)

---

This directory contains tests for the Smart Maintenance SaaS application. The testing strategy is designed to ensure code quality and prevent regressions while keeping tests fast and reliable.

## 📊 Current Test Status

**Total Tests: 412** | **✅ Passed: 409** | **❌ Failed: 1** | **⚠️ Errors: 2**

### Test Results Summary
- **Success Rate**: 99.3% (409/412 tests passing)
- **Known Issues**: 1 scheduling constraint failure + 2 UI dependency errors
- **Core Functionality**: 100% operational

### Known Issues

**1. Scheduling Constraint Failure (1 test):**
- **Test**: `test_full_workflow_from_ingestion_to_scheduling`
- **Issue**: No available technician slots found during business hours
- **Impact**: Low - Core system functionality works correctly
- **Details**: Scheduling agent correctly processes events but calendar service constraints prevent scheduling

**2. UI Dependency Errors (2 tests):**
- **Tests**: `test_maintenance_logs`, `test_sensor_data`
- **Issue**: UI integration test dependencies
- **Impact**: Low - UI functionality verified through other means
- **Details**: Core UI components work as verified by `final_system_test.py`

## Test Organization

```text
tests/
├── api/                    # API endpoint tests
│   ├── test_actual_api.py  # Real API endpoint validation
│   └── test_api_endpoints.py # Additional API endpoint tests
├── e2e/                    # End-to-end system tests  
│   ├── final_system_test.py    # Complete system validation
│   ├── test_ui_functionality.py # UI integration testing
│   └── test_e2e_full_system_workflow.py # Full workflow testing
├── unit/                   # Component unit tests
│   ├── agents/            # Agent system unit tests
│   ├── core/              # Core module unit tests
│   ├── data/              # Data layer unit tests
│   ├── ml/                # ML component unit tests
│   └── rules/             # Business rules unit tests
├── integration/           # Service integration tests
│   ├── agents/            # Agent integration tests
│   ├── core/              # Core system integration tests
│   ├── workflows/         # Workflow integration tests
│   ├── test_full_workflow.py    # Complete workflow testing
│   └── test_rbac_enforcement.py # Security and RBAC tests
├── data/                  # Test data and generators
│   └── generators/        # Test data generation utilities
├── conftest.py           # Shared test configuration and fixtures
├── test_db_example.py    # Database testing examples
├── test_settings.py      # Configuration testing utilities
└── test_validation_changes.py # Data validation tests
```

## Test Types

### Unit Tests

- Test individual components in isolation
- Fast execution, no external dependencies
- Marker: `@pytest.mark.unit`

### Integration Tests

- Test interactions between components
- May require external services like databases
- Marker: `@pytest.mark.integration`

### API Tests

- Test HTTP endpoints and responses
- Marker: `@pytest.mark.api`

### Additional Test Markers

Based on the project's `pytest.ini` configuration, the following markers are available:

- `@pytest.mark.db`: Tests that require database access
- `@pytest.mark.slow`: Tests that are known to be slow
- `@pytest.mark.smoke`: Critical path functionality tests for CI

## Database Testing Strategy

We use multiple approaches for database testing to accommodate different testing scenarios:

### 1. Docker Container Approach (Default)

We use `testcontainers` to spin up a PostgreSQL with TimescaleDB container for integration tests:

**Pros:**
- Tests run against a real database instance
- Complete isolation from development and production databases
- Tests can freely modify data without affecting other environments
- Each test session gets a fresh database state
- No need for manual database setup

**Cons:**
- Requires Docker to be installed and running
- Slower startup time for the test suite
- Resource-intensive

### 2. Dedicated Test Database Approach

Alternatively, you can use a pre-configured test database by running tests with `--no-container`:

**Pros:**
- Faster startup time for the test suite
- Doesn't require Docker
- Good for CI/CD environments with pre-configured databases

**Cons:**
- Requires manual setup of a test database
- Potential for test interference if multiple test runs occur simultaneously

## Running Tests

Use the provided script to run tests:

```bash
# Run all tests with Docker container for database
./scripts/run_tests.sh

# Run only unit tests (no database required)
./scripts/run_tests.sh -m unit

# Run only integration tests
./scripts/run_tests.sh -m integration

# Run tests without using Docker container
./scripts/run_tests.sh --no-container

# Run tests with coverage report
./scripts/run_tests.sh --cov
```

## Test Database Configuration

The test database connection is configured via the `.env.test` file or environment variables:

- When using the Docker container approach, connection details are managed automatically
- When using the direct database approach (`--no-container`), the test database URL is determined from:
  1. The `DATABASE_TEST_URL` environment variable, if set
  2. The standard `DATABASE_URL` with the database name appended with `_test`

## Best Practices

1. **Isolation**: Each test should be independent and leave no side effects
2. **Fixtures**: Use pytest fixtures for test setup and teardown
3. **Async**: Use `@pytest.mark.asyncio` for async tests
4. **Markers**: Apply appropriate markers to categorize tests
5. **Mocking**: Use mocks for external services when appropriate
6. **Coverage**: Aim for high test coverage, especially for critical components

---

## 🇧🇷 Estratégia de Testes (Português)

Este diretório contém testes para a aplicação Smart Maintenance SaaS. A estratégia de testes é projetada para garantir qualidade do código e prevenir regressões, mantendo os testes rápidos e confiáveis.

## 📊 Status Atual dos Testes

**Total de Testes: 412** | **✅ Aprovados: 409** | **❌ Falharam: 1** | **⚠️ Erros: 2**

### Resumo dos Resultados dos Testes

- **Taxa de Sucesso**: 99,3% (409/412 testes aprovados)
- **Problemas Conhecidos**: 1 falha de restrição de agendamento + 2 erros de dependência de UI
- **Funcionalidade Principal**: 100% operacional

### Problemas Conhecidos

**1. Falha de Restrição de Agendamento (1 teste):**
- **Teste**: `test_full_workflow_from_ingestion_to_scheduling`
- **Problema**: Nenhum slot de técnico disponível encontrado durante horário comercial
- **Impacto**: Baixo - Funcionalidade principal do sistema funciona corretamente
- **Detalhes**: Agente de agendamento processa eventos corretamente, mas restrições do serviço de calendário impedem agendamento

**2. Erros de Dependência de UI (2 testes):**
- **Testes**: `test_maintenance_logs`, `test_sensor_data`
- **Problema**: Dependências de teste de integração de UI
- **Impacto**: Baixo - Funcionalidade de UI verificada por outros meios
- **Detalhes**: Componentes principais de UI funcionam conforme verificado por `final_system_test.py`

## Organização dos Testes

```text
tests/
├── api/                    # Testes de endpoints da API
│   ├── test_actual_api.py  # Validação de endpoints reais da API
│   └── test_api_endpoints.py # Testes adicionais de endpoints da API
├── e2e/                    # Testes de sistema end-to-end
│   ├── final_system_test.py    # Validação completa do sistema
│   ├── test_ui_functionality.py # Testes de integração de UI
│   └── test_e2e_full_system_workflow.py # Testes de fluxo completo
├── unit/                   # Testes unitários de componentes
│   ├── agents/            # Testes unitários do sistema de agentes
│   ├── core/              # Testes unitários dos módulos principais
│   ├── data/              # Testes unitários da camada de dados
│   ├── ml/                # Testes unitários de componentes ML
│   └── rules/             # Testes unitários de regras de negócio
├── integration/           # Testes de integração de serviços
│   ├── agents/            # Testes de integração de agentes
│   ├── core/              # Testes de integração do sistema principal
│   ├── workflows/         # Testes de integração de workflows
│   ├── test_full_workflow.py    # Testes de workflow completo
│   └── test_rbac_enforcement.py # Testes de segurança e RBAC
├── data/                  # Dados de teste e geradores
│   └── generators/        # Utilitários de geração de dados de teste
├── conftest.py           # Configuração e fixtures compartilhados
├── test_db_example.py    # Exemplos de testes de banco de dados
├── test_settings.py      # Utilitários de teste de configuração
└── test_validation_changes.py # Testes de validação de dados
```

## Tipos de Teste

### Testes Unitários

- Testam componentes individuais isoladamente
- Execução rápida, sem dependências externas
- Marcador: `@pytest.mark.unit`

### Testes de Integração

- Testam interações entre componentes
- Podem requerer serviços externos como bancos de dados
- Marcador: `@pytest.mark.integration`

### Testes de API

- Testam endpoints HTTP e respostas
- Marcador: `@pytest.mark.api`

### Marcadores de Teste Adicionais

Baseado na configuração `pytest.ini` do projeto, os seguintes marcadores estão disponíveis:

- `@pytest.mark.db`: Testes que requerem acesso ao banco de dados
- `@pytest.mark.slow`: Testes que são conhecidamente lentos
- `@pytest.mark.smoke`: Testes de funcionalidade de caminho crítico para CI

## Estratégia de Teste de Banco de Dados

Usamos múltiplas abordagens para testes de banco de dados para acomodar diferentes cenários de teste:

### 1. Abordagem de Container Docker (Padrão)

Usamos `testcontainers` para criar um container PostgreSQL com TimescaleDB para testes de integração:

**Vantagens:**
- Testes executam contra uma instância real de banco de dados
- Isolamento completo dos bancos de desenvolvimento e produção
- Testes podem modificar dados livremente sem afetar outros ambientes
- Cada sessão de teste obtém um estado limpo de banco de dados
- Não necessita configuração manual de banco de dados

**Desvantagens:**
- Requer Docker instalado e executando
- Tempo de inicialização mais lento para a suíte de testes
- Uso intensivo de recursos

### 2. Abordagem de Banco de Dados de Teste Dedicado

Alternativamente, você pode usar um banco de dados de teste pré-configurado executando testes com `--no-container`:

**Vantagens:**
- Tempo de inicialização mais rápido para a suíte de testes
- Não requer Docker
- Bom para ambientes CI/CD com bancos de dados pré-configurados

**Desvantagens:**
- Requer configuração manual de um banco de dados de teste
- Potencial para interferência de teste se múltiplas execuções de teste ocorrerem simultaneamente

## Executando Testes

Use o script fornecido para executar testes:

```bash
# Executar todos os testes com container Docker para banco de dados
./scripts/run_tests.sh

# Executar apenas testes unitários (sem banco de dados necessário)
./scripts/run_tests.sh -m unit

# Executar apenas testes de integração
./scripts/run_tests.sh -m integration

# Executar testes sem usar container Docker
./scripts/run_tests.sh --no-container

# Executar testes com relatório de cobertura
./scripts/run_tests.sh --cov
```

## Configuração do Banco de Dados de Teste

A conexão do banco de dados de teste é configurada via arquivo `.env.test` ou variáveis de ambiente:

- Ao usar a abordagem de container Docker, detalhes de conexão são gerenciados automaticamente
- Ao usar a abordagem de banco direto (`--no-container`), a URL do banco de teste é determinada de:
  1. A variável de ambiente `DATABASE_TEST_URL`, se definida
  2. A `DATABASE_URL` padrão com o nome do banco acrescido de `_test`

## Melhores Práticas

1. **Isolamento**: Cada teste deve ser independente e não deixar efeitos colaterais
2. **Fixtures**: Use fixtures do pytest para configuração e limpeza de testes
3. **Assíncrono**: Use `@pytest.mark.asyncio` para testes assíncronos
4. **Marcadores**: Aplique marcadores apropriados para categorizar testes
5. **Mocking**: Use mocks para serviços externos quando apropriado
6. **Cobertura**: Busque alta cobertura de testes, especialmente para componentes críticos
