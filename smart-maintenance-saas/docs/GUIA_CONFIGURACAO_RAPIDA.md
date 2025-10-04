# Guia de Configuração Rápida - Smart Maintenance SaaS

**Versão:** 1.0  
**Última Atualização:** 2025-10-03  
**Status:** Pronto para Produção ✅  
**Tempo Estimado:** 60-180 minutos (dependendo do cenário de implantação)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Cenário 1: Implantação Completamente Local](#cenário-1-implantação-completamente-local)
4. [Cenário 2: Implantação Híbrida (Local + Cloud)](#cenário-2-implantação-híbrida-local--cloud)
5. [Cenário 3: Implantação Completamente na Cloud](#cenário-3-implantação-completamente-na-cloud)
6. [Solução de Problemas Comuns](#solução-de-problemas-comuns)
7. [Próximos Passos](#próximos-passos)

---

## Visão Geral

Este guia fornece instruções passo a passo para configurar e executar o Smart Maintenance SaaS em três cenários diferentes:

- **Cenário 1 - Completamente Local:** Tudo rodando na sua máquina local (ideal para desenvolvimento e testes)
- **Cenário 2 - Híbrido:** UI e MLflow locais, mas usando serviços cloud (TimescaleDB, Redis, S3)
- **Cenário 3 - Cloud Completo:** Backend na AWS EC2 e UI no Streamlit Cloud (produção)

**⚠️ NOTA IMPORTANTE SOBRE DEPENDÊNCIAS:**
- A partir de 03/10/2025, o projeto usa `pip` e `virtualenv` ao invés de Poetry para gerenciar dependências dentro dos containers Docker.
- Isso resolve um bug conhecido do Poetry (que será corrigido na v1.5).
- O arquivo `requirements/api.txt` é a fonte autoritativa de dependências para builds de containers.

---

## Pré-requisitos

### Ferramentas Necessárias

**Para todos os cenários:**
- Git
- Python 3.11+
- Docker Engine v24+
- Docker Compose v2+

**Para cenário cloud (3):**
- Conta AWS (para EC2 e S3)
- Conta no Streamlit Cloud (gratuita)
- Cliente SSH

### Contas de Serviços Cloud (Cenários 2 e 3)

1. **TimescaleDB Cloud:** https://console.cloud.timescale.com/
2. **Redis Cloud:** Render (https://render.com) ou Upstash
3. **AWS S3:** Bucket para artefatos MLflow
4. **Streamlit Cloud:** Para hospedagem da UI (cenário 3)

### Verificar Instalações

```bash
# Verificar versões
git --version
python3 --version
docker --version
docker compose version

# Verificar que Docker está rodando
docker ps
```

---

## Cenário 1: Implantação Completamente Local

**Tempo Estimado:** 60-90 minutos  
**Ideal Para:** Desenvolvimento local, testes, experimentação

Este cenário roda todos os serviços na sua máquina local usando Docker Compose, incluindo banco de dados PostgreSQL/TimescaleDB, Redis, MLflow e a aplicação.

### Passo 1.1: Clonar o Repositório

```bash
# Clonar o repositório
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git

# Navegar para o diretório do projeto
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Verificar conteúdo
ls -la
```

### Passo 1.2: Configurar Variáveis de Ambiente

```bash
# Copiar o arquivo de exemplo
cp .env_example.txt .env

# Editar o arquivo .env
nano .env  # ou use seu editor preferido (vim, code, etc.)
```

**Configure as seguintes variáveis para implantação LOCAL:**

```bash
# --- CONFIGURAÇÃO CORE ---
ENV=development
LOG_LEVEL=INFO

# --- SEGURANÇA DA API ---
# Gerar chaves seguras:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY=sua_chave_api_local_aqui
SECRET_KEY=sua_chave_secreta_local_aqui
JWT_SECRET=seu_jwt_secret_local_aqui

# --- BANCO DE DADOS (LOCAL) ---
# Usar o banco de dados local do Docker Compose
DATABASE_URL=postgresql+asyncpg://smart_user:strong_password@db:5432/smart_maintenance_db

# --- REDIS (LOCAL) ---
# Usar o Redis local do Docker Compose
REDIS_URL=redis://redis:6379/0

# --- MLFLOW (LOCAL) ---
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_BACKEND_STORE_URI=sqlite:////mlflow_db/mlflow.db
MLFLOW_ARTIFACT_ROOT=/mlruns

# --- AWS (NÃO NECESSÁRIO PARA LOCAL) ---
# Deixe em branco ou use valores dummy
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_DEFAULT_REGION=us-east-1

# --- CONFIGURAÇÃO DA UI ---
API_BASE_URL=http://api:8000
CLOUD_MODE=false
DEPLOYMENT_ENV=local

# --- OPCIONAL: DESABILITAR RECURSOS ---
DISABLE_MLFLOW_MODEL_LOADING=false
DISABLE_CHROMADB=true
```

### Passo 1.3: Garantir que requirements/api.txt Existe

```bash
# Verificar se o arquivo existe
ls -lh requirements/api.txt

# Se não existir, gerar a partir do pyproject.toml
# (Requer Poetry instalado localmente)
test -f requirements/api.txt || poetry export --without-hashes --format=requirements.txt --output requirements/api.txt
```

### Passo 1.4: Preparar Dados para Treinamento de Modelos

Você tem duas opções: usar modelos pré-treinados via DVC ou treinar do zero.

#### Opção A: Usar DVC para Baixar Dados Pré-treinados (Recomendado - 5-10 minutos)

```bash
# Instalar DVC com suporte ao Google Drive
pip install dvc[gdrive]

# Puxar todos os dados do Google Drive compartilhado
# (A pasta já está configurada em .dvc/config)
dvc pull

# Verificar que os dados foram baixados
ls -lh data/
ls -lh mlflow_data/
ls -lh mlflow_db/

# Você deve ver:
# - data/sensor_data.csv (dados sintéticos)
# - data/AI4I_2020_uci_dataset/ (opcional)
# - data/kaggle_pump_sensor_data/ (opcional)
# - mlflow_data/ (artefatos de modelos)
# - mlflow_db/ (metadados MLflow)
```

**Link da Pasta Compartilhada do Google Drive:**  
https://drive.google.com/drive/folders/1cJvSRaBG0Fzs4D_wlUeVPM9l47RP_k3G?usp=sharing

#### Opção B: Baixar e Treinar Modelos do Zero (60-120 minutos)

**Baixar Datasets:**

```bash
cd data

# 1. Dataset AI4I 2020 (Principal)
wget https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip
unzip "ai4i+2020+predictive+maintenance+dataset.zip" -d AI4I_2020_uci_dataset/
rm "ai4i+2020+predictive+maintenance+dataset.zip"

# 2. Dataset de Sensor de Bomba Kaggle (Opcional)
# Requer Kaggle API: pip install kaggle
# Configurar credenciais: ~/.kaggle/kaggle.json
kaggle datasets download -d nphantawee/pump-sensor-data
unzip pump-sensor-data.zip -d kaggle_pump_sensor_data/
rm pump-sensor-data.zip

# 3. Dataset de Rolamentos NASA (Opcional)
kaggle datasets download -d vinayak123tyagi/bearing-dataset
unzip bearing-dataset.zip -d nasa_bearing_dataset/
rm bearing-dataset.zip

# 4. Dataset de Som MIMII (Opcional - grande, 2GB+)
# Baixar manualmente de: https://zenodo.org/records/3384388

# Voltar para o diretório raiz
cd ..
```

**Treinar Modelos:**

```bash
# Criar ambiente virtual local (recomendado para notebooks)
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements/api.txt

# Construir imagem Docker para ML
make build-ml

# Executar notebooks de treinamento via Makefile
# (Estes rodam dentro de containers Docker para reprodutibilidade)

# Modelos com dados sintéticos (base - 15-30 min total)
make synthetic-validation    # Validação de qualidade dos dados
make synthetic-anomaly       # Detecção de anomalias (IsolationForest)
make synthetic-forecast      # Previsão de séries temporais (Prophet)
make synthetic-tune-forecast # Otimização de previsão

# Modelos com datasets reais (gauntlets - 10-40 min cada)
make classification-gauntlet # Dataset AI4I (99.9% acurácia)
make pump-gauntlet          # Dataset Kaggle Pump (100% acurácia)
make vibration-gauntlet     # Dataset NASA bearing (opcional)
make xjtu-gauntlet          # Dataset XJTU bearing (opcional)
make audio-gauntlet         # Dataset MIMII sound (opcional, pesado 60-90min)

# Alternativa: Executar notebooks manualmente com Jupyter
# jupyter notebook
# Depois executar os notebooks em notebooks/ na ordem numérica
```

### Passo 1.5: Inicializar Banco de Dados

```bash
# Ativar ambiente virtual (se ainda não estiver ativo)
source .venv/bin/activate

# Configurar Alembic para usar o banco local
# Editar alembic.ini e definir:
# sqlalchemy.url = postgresql://smart_user:strong_password@localhost:5433/smart_maintenance_db
nano alembic.ini

# Iniciar apenas o banco de dados primeiro
docker compose up -d db

# Aguardar o banco inicializar (30 segundos)
sleep 30

# Executar migrações
alembic upgrade head

# Verificar tabelas criadas
python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('postgresql://smart_user:strong_password@localhost:5433/smart_maintenance_db')
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tabelas criadas: {tables}')
"

# Opcional: Popular com dados iniciais
python scripts/seed_database.py
```

### Passo 1.6: Iniciar Todos os Serviços

```bash
# Construir e iniciar todos os containers
docker compose up -d --build

# Verificar que todos os containers estão rodando
docker compose ps

# Você deve ver:
# - smart_maintenance_api (porta 8000)
# - smart_maintenance_ui (porta 8501)
# - smart_maintenance_db (porta 5433)
# - smart_maintenance_redis (porta 6379)
# - smart_maintenance_mlflow (porta 5000)

# Ver logs em tempo real (Ctrl+C para sair)
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs api --tail=50
docker compose logs ui --tail=50
```

### Passo 1.7: Verificar a Instalação

```bash
# Testar endpoints da API
curl http://localhost:8000/health
# Esperado: {"status":"ok"}

curl http://localhost:8000/health/db
# Esperado: {"database":"connected"}

curl http://localhost:8000/health/redis
# Esperado: {"redis":"connected"}

# Abrir UI no navegador
echo "Abra no navegador: http://localhost:8501"

# Abrir MLflow no navegador
echo "Abra no navegador: http://localhost:5000"

# Abrir documentação da API
echo "Abra no navegador: http://localhost:8000/docs"
```

### Passo 1.8: Testar Funcionalidades

**No navegador em http://localhost:8501:**

1. **Ingestão de Dados:**
   - Navegue para "Ingestão de Dados"
   - Faça upload de `data/sensor_data.csv`
   - Verifique que os dados foram ingeridos com sucesso

2. **Previsões ML:**
   - Navegue para "Previsões"
   - Selecione um sensor
   - Execute uma previsão
   - Verifique os resultados

3. **Demo Golden Path:**
   - Navegue para "Golden Path Demo"
   - Execute a demonstração completa
   - Verifique que todos os passos completam sem erros

4. **Metadados de Modelos:**
   - Navegue para "Metadados de Modelos"
   - Verifique que os modelos treinados aparecem

### Passo 1.9: Parar e Reiniciar Serviços

```bash
# Parar todos os serviços
docker compose down

# Reiniciar serviços
docker compose up -d

# Parar e remover volumes (CUIDADO: apaga dados!)
docker compose down -v
```

**✅ Implantação Local Completa!**

---

## Cenário 2: Implantação Híbrida (Local + Cloud)

**Tempo Estimado:** 90-120 minutos  
**Ideal Para:** Desenvolvimento com infraestrutura cloud, teste de integração

Este cenário roda a UI e MLflow localmente, mas conecta a serviços cloud gerenciados (TimescaleDB, Redis, S3) para simular um ambiente de produção.

### Passo 2.1: Clonar Repositório e Configurar Ambiente

```bash
# Clonar e navegar
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Copiar arquivo de configuração
cp .env_example.txt .env
```

### Passo 2.2: Provisionar Serviços Cloud

#### 2.2.1: Criar Instância TimescaleDB Cloud

1. Acesse: https://console.cloud.timescale.com/
2. Crie uma conta ou faça login
3. Clique em "Create service"
4. Escolha:
   - **Região:** Mais próxima de você
   - **Plano:** Free tier (512MB RAM) ou Starter
5. Aguarde provisionamento (2-3 minutos)
6. **Copie a connection string:**
   ```
   postgresql://tsdbadmin:sua_senha@seu_host.tsdb.cloud.timescale.com:porta/tsdb?sslmode=require
   ```
7. Configure o firewall para permitir seu IP

#### 2.2.2: Criar Instância Redis Cloud

**Opção A: Render (Recomendado - Gratuito)**

1. Acesse: https://dashboard.render.com/
2. Clique em "New +" → "Redis"
3. Configure:
   - **Name:** smart-maintenance-redis
   - **Plan:** Free (25MB)
   - **Region:** Mais próxima de você
4. Clique em "Create Redis"
5. **Copie a connection string:**
   ```
   rediss://red-xxxx:senha@singapore-redis.render.com:6379
   ```

**Opção B: Upstash**

1. Acesse: https://console.upstash.com/
2. Crie um database Redis
3. Copie a connection string com TLS

#### 2.2.3: Criar Bucket S3 na AWS

```bash
# Instalar AWS CLI
pip install awscli

# Configurar credenciais
aws configure
# Digite:
# - AWS Access Key ID: (da conta IAM)
# - AWS Secret Access Key: (da conta IAM)
# - Default region: us-east-1 (ou sua região preferida)
# - Default output format: json

# Criar bucket
aws s3 mb s3://smart-maintenance-mlflow-artifacts

# Verificar bucket criado
aws s3 ls
```

**Configurar Política do Bucket (IAM):**

1. Acesse: https://console.aws.amazon.com/iam/
2. Crie usuário IAM: `smart-maintenance-s3-user`
3. Anexe política: `AmazonS3FullAccess` ou crie política customizada
4. Gere Access Keys e salve

### Passo 2.3: Configurar Variáveis de Ambiente

Edite o arquivo `.env`:

```bash
# --- CONFIGURAÇÃO CORE ---
ENV=production
LOG_LEVEL=INFO

# --- SEGURANÇA DA API ---
# Gerar com: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY=sua_chave_forte_64_caracteres_aqui
SECRET_KEY=sua_chave_forte_64_caracteres_aqui
JWT_SECRET=sua_chave_forte_64_caracteres_aqui

# --- BANCO DE DADOS (TIMESCALE CLOUD) ---
# Formato: postgresql+asyncpg://user:senha@host:porta/db?ssl=require
DATABASE_URL=postgresql+asyncpg://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb?ssl=require

# --- REDIS (CLOUD) ---
# Formato: rediss://default:senha@host:porta
REDIS_URL=rediss://default:SUA_SENHA_REDIS@SEU_HOST_REDIS:6379

# --- MLFLOW (CLOUD BACKEND + S3) ---
MLFLOW_TRACKING_URI=http://mlflow:5000

# Backend store (TimescaleDB - note: use postgresql:// não postgresql+asyncpg://)
MLFLOW_BACKEND_STORE_URI=postgresql://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb?sslmode=require

# Artifact storage (S3)
MLFLOW_ARTIFACT_ROOT=s3://smart-maintenance-mlflow-artifacts

# --- CREDENCIAIS AWS ---
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=us-east-1

# --- CONFIGURAÇÃO DA UI ---
API_BASE_URL=http://api:8000
CLOUD_MODE=true
DEPLOYMENT_ENV=production

# --- OPCIONAL ---
DISABLE_MLFLOW_MODEL_LOADING=false
DISABLE_CHROMADB=true
```

### Passo 2.4: Preparar Modelos ML

**Opção A: Usar DVC (Recomendado)**

```bash
# Instalar DVC e baixar dados
pip install dvc[gdrive]
dvc pull

# Sincronizar MLflow data com S3
aws s3 sync mlflow_data/ s3://smart-maintenance-mlflow-artifacts/
aws s3 sync mlflow_db/ s3://smart-maintenance-mlflow-artifacts/mlflow_db/
```

**Opção B: Treinar Modelos Localmente**

Siga os passos do Passo 1.4 (Opção B) para treinar modelos, depois sincronize com S3:

```bash
# Após treinamento
aws s3 sync mlflow_data/ s3://smart-maintenance-mlflow-artifacts/
```

### Passo 2.5: Inicializar Banco de Dados Cloud

```bash
# Instalar dependências
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/api.txt

# Configurar Alembic para o banco cloud
nano alembic.ini
# Alterar linha sqlalchemy.url para:
# postgresql://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb

# Executar migrações
alembic upgrade head

# Verificar tabelas
python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('postgresql://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb')
inspector = inspect(engine)
print(f'Tabelas: {inspector.get_table_names()}')
"
```

### Passo 2.6: Inicializar Tabelas MLflow

```bash
# Configurar variável de ambiente
export MLFLOW_BACKEND_STORE_URI="postgresql://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb"

# Inicializar MLflow (cria tabelas automaticamente na primeira conexão)
python -c "
import mlflow
mlflow.set_tracking_uri('$MLFLOW_BACKEND_STORE_URI')
print('MLflow inicializado')
"
```

### Passo 2.7: Iniciar Serviços Locais

```bash
# Garantir que requirements/api.txt existe
test -f requirements/api.txt || poetry export --without-hashes --format=requirements.txt --output requirements/api.txt

# Construir e iniciar containers
docker compose up -d --build

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f
```

### Passo 2.8: Verificar Integração Cloud

```bash
# Testar API
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis

# Testar conexão S3
aws s3 ls s3://smart-maintenance-mlflow-artifacts/

# Verificar MLflow
open http://localhost:5000
# Deve mostrar modelos sincronizados do S3

# Verificar UI
open http://localhost:8501
```

**✅ Implantação Híbrida Completa!**

---

## Cenário 3: Implantação Completamente na Cloud

**Tempo Estimado:** 120-180 minutos  
**Ideal Para:** Produção, demonstrações públicas, uso por equipe distribuída

Este cenário implanta o backend completo em uma VM AWS EC2 e a UI no Streamlit Cloud, conectando a serviços cloud gerenciados.

### Passo 3.1: Provisionar Serviços Cloud

Siga os passos 2.2.1 a 2.2.3 do Cenário 2 para criar:
- ✅ TimescaleDB Cloud
- ✅ Redis Cloud (Render ou Upstash)
- ✅ Bucket S3

### Passo 3.2: Preparar Modelos ML (Local)

Na sua máquina local:

```bash
# Clonar repositório
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Opção A: Usar DVC
pip install dvc[gdrive]
dvc pull

# Opção B: Treinar modelos
# (Siga Passo 1.4 Opção B)

# Sincronizar com S3
pip install awscli
aws configure  # Digite suas credenciais
aws s3 sync mlflow_data/ s3://smart-maintenance-mlflow-artifacts/
aws s3 sync mlflow_db/ s3://smart-maintenance-mlflow-artifacts/mlflow_db/

# Verificar upload
aws s3 ls s3://smart-maintenance-mlflow-artifacts/ --recursive | head -20
```

### Passo 3.3: Inicializar Banco de Dados (Local)

```bash
# Na máquina local
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/api.txt

# Configurar alembic.ini para o banco cloud
nano alembic.ini
# sqlalchemy.url = postgresql://tsdbadmin:SENHA@HOST.tsdb.cloud.timescale.com:PORTA/tsdb

# Executar migrações
alembic upgrade head

# Opcional: Popular dados iniciais
python scripts/seed_database.py
```

### Passo 3.4: Provisionar VM AWS EC2

1. **Acessar AWS Console:**
   - Vá para: https://console.aws.amazon.com/ec2/

2. **Lançar Instância:**
   - Clique em "Launch Instance"
   - **Nome:** `smart-maintenance-vm`
   - **AMI:** Ubuntu Server 22.04 LTS (64-bit x86)
   - **Tipo de Instância:** `t3.medium` (2 vCPU, 4GB RAM) ou `t3.large` (2 vCPU, 8GB RAM)
   - **Storage:** **60 GB** gp3 SSD (CRÍTICO - 30GB é insuficiente)
   - **Key Pair:** Criar novo ou selecionar existente (baixar arquivo `.pem`)

3. **Configurar Security Group:**
   ```
   Regras de Entrada:
   - SSH (22): Seu IP / 0.0.0.0/0 (para acesso)
   - TCP Customizado (8000): 0.0.0.0/0 (API)
   - TCP Customizado (8501): 0.0.0.0/0 (UI - opcional)
   - TCP Customizado (5000): 0.0.0.0/0 (MLflow)
   ```

4. **Lançar e Anotar IP Público:**
   - Aguarde status: "Running"
   - Anote o **Endereço IPv4 Público** (ex: `18.117.235.91`)

### Passo 3.5: Configurar Firewall dos Serviços Cloud

1. **TimescaleDB:**
   - Acesse console TimescaleDB
   - Settings → Allowed IP Addresses
   - Adicione o IP da sua VM EC2

2. **Redis (Render):**
   - Geralmente permite qualquer IP com TLS
   - Verifique a configuração de firewall

### Passo 3.6: Conectar à VM e Instalar Dependências

```bash
# Na sua máquina local
# Tornar a chave SSH legível apenas por você
chmod 400 sua-chave.pem

# Conectar à VM
ssh -i sua-chave.pem ubuntu@SEU_IP_PUBLICO

# Dentro da VM:
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalações
docker --version
docker-compose --version

# Sair e reconectar para aplicar permissões de grupo
exit
ssh -i sua-chave.pem ubuntu@SEU_IP_PUBLICO
```

### Passo 3.7: Clonar Repositório na VM

```bash
# Dentro da VM
# Clonar repositório
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Verificar estrutura
ls -la
```

### Passo 3.8: Configurar Arquivo .env na VM

```bash
# Dentro da VM
# Copiar template
cp .env_example.txt .env

# Editar arquivo
nano .env
```

**Configure com suas credenciais cloud:**

```bash
# --- CONFIGURAÇÃO CORE ---
ENV=production
LOG_LEVEL=INFO

# --- SEGURANÇA ---
API_KEY=sua_chave_64_caracteres
SECRET_KEY=sua_chave_64_caracteres
JWT_SECRET=sua_chave_64_caracteres

# --- TIMESCALEDB CLOUD ---
DATABASE_URL=postgresql+asyncpg://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb?ssl=require

# --- REDIS CLOUD ---
REDIS_URL=rediss://default:SUA_SENHA@SEU_HOST_REDIS:6379

# --- MLFLOW ---
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_BACKEND_STORE_URI=postgresql://tsdbadmin:SUA_SENHA@SEU_HOST.tsdb.cloud.timescale.com:PORTA/tsdb?sslmode=require
MLFLOW_ARTIFACT_ROOT=s3://smart-maintenance-mlflow-artifacts

# --- AWS ---
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=us-east-1

# --- UI (interno para Docker) ---
API_BASE_URL=http://api:8000
CLOUD_MODE=true
DEPLOYMENT_ENV=production

DISABLE_MLFLOW_MODEL_LOADING=false
DISABLE_CHROMADB=true
```

Salvar e fechar (Ctrl+O, Enter, Ctrl+X).

### Passo 3.9: Verificar requirements/api.txt

```bash
# Dentro da VM
# Verificar se arquivo existe
ls -lh requirements/api.txt

# Se não existir, você precisará gerá-lo localmente e fazer commit
# (Na sua máquina local, não na VM)
# poetry export --without-hashes --format=requirements.txt --output requirements/api.txt
# git add requirements/api.txt
# git commit -m "Add requirements/api.txt"
# git push

# Depois, na VM, puxar a atualização:
# git pull
```

### Passo 3.10: Implantar com Docker Compose

```bash
# Dentro da VM
# Construir e iniciar containers
docker compose up -d --build

# Este processo pode levar 10-15 minutos na primeira vez

# Monitorar logs
docker compose logs -f

# Quando ver "Application startup complete", pressione Ctrl+C

# Verificar status dos containers
docker compose ps

# Devem estar "Up":
# - smart_maintenance_api
# - smart_maintenance_ui
# - smart_maintenance_mlflow
```

### Passo 3.11: Verificar Backend na VM

```bash
# Dentro da VM
# Testar health checks
curl http://localhost:8000/health
# Esperado: {"status":"ok"}

curl http://localhost:8000/health/db
# Esperado: {"database":"connected"}

curl http://localhost:8000/health/redis  
# Esperado: {"redis":"connected"}

# Verificar API é acessível externamente (na sua máquina local)
# curl http://SEU_IP_PUBLICO:8000/health
```

### Passo 3.12: Implantar UI no Streamlit Cloud

1. **Fazer Fork do Repositório (se ainda não fez):**
   - Vá para: https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply
   - Clique em "Fork" no canto superior direito
   - Aguarde o fork completar

2. **Acessar Streamlit Cloud:**
   - Vá para: https://share.streamlit.io
   - Faça login com sua conta GitHub

3. **Criar Novo App:**
   - Clique em "New app"
   - **Repository:** `SeuUsuario/enterprise_challenge_sprint_1_hermes_reply`
   - **Branch:** `main`
   - **Main file path:** `smart-maintenance-saas/ui/streamlit_app.py`
   - **App URL:** Escolha um subdomínio (ex: `smart-maintenance`)

4. **Configurar Python Version:**
   - Clique em "Advanced settings..."
   - **Python version:** Selecione `3.11`

5. **Adicionar Secrets:**
   - Em "Secrets", cole a seguinte configuração TOML:

```toml
[default]
API_BASE_URL = "http://SEU_IP_PUBLICO_VM:8000"
CLOUD_MODE = true
DEPLOYMENT_ENV = "production"

# Opcional: se usar autenticação
# API_KEY = "sua_chave_api"
```

6. **Deploy:**
   - Clique em "Deploy!"
   - Aguarde build completar (5-10 minutos)
   - A UI será acessível em: `https://seu-app.streamlit.app`

### Passo 3.13: Testar Deploy Completo

**No navegador:**

1. Acesse sua URL do Streamlit Cloud: `https://seu-app.streamlit.app`

2. **Testar Conectividade:**
   - Verifique que a UI carrega sem erros
   - Verifique que o tooltip está em português

3. **Testar Fluxo Completo:**
   - Navegue para "Ingestão de Dados"
   - Tente fazer upload de dados
   - Navegue para "Previsões"
   - Execute uma previsão
   - Navegue para "Golden Path Demo"
   - Execute a demonstração

4. **Verificar MLflow (se exposto):**
   - Acesse: `http://SEU_IP_PUBLICO:5000`
   - Verifique modelos registrados

### Passo 3.14: Monitoramento e Manutenção

```bash
# Conectar à VM
ssh -i sua-chave.pem ubuntu@SEU_IP_PUBLICO

# Ver logs em tempo real
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs api --tail=100

# Verificar uso de recursos
docker stats

# Reiniciar serviços
docker compose restart

# Parar e reiniciar completamente
docker compose down
docker compose up -d

# Atualizar código
git pull
docker compose up -d --build

# Backup do banco (do TimescaleDB Cloud via console)
# Backup de artefatos S3 (já persistidos)

# Limpar logs antigos
sudo find /var/lib/docker/containers/ -type f -name "*.log" -delete
```

### Passo 3.15: Configurar Domínio Customizado (Opcional)

**Para a API:**

1. Registre um domínio (ex: `api.smart-maintenance.com`)
2. Configure DNS A record apontando para o IP da VM
3. Configure Nginx como reverse proxy com SSL (Let's Encrypt)
4. Atualize `API_BASE_URL` nos secrets do Streamlit Cloud

**Para a UI no Streamlit Cloud:**

1. Vá para App Settings → General → Custom domain
2. Adicione seu domínio (ex: `app.smart-maintenance.com`)
3. Configure DNS CNAME conforme instruções

**✅ Implantação Cloud Completa!**

---

## Solução de Problemas Comuns

### Problema: "requirements/api.txt não encontrado"

**Solução:**
```bash
# Na máquina local com Poetry instalado
cd smart-maintenance-saas
poetry export --without-hashes --format=requirements.txt --output requirements/api.txt
git add requirements/api.txt
git commit -m "Add requirements/api.txt for Docker builds"
git push

# Na VM, puxar a atualização
git pull
```

### Problema: Container de build falha com erro de Poetry

**Causa:** O projeto agora usa pip ao invés de Poetry para builds Docker.

**Solução:**
- Verifique que `requirements/api.txt` existe
- Verifique que o `Dockerfile` usa `pip install -r requirements/api.txt`
- Não use `poetry install` dentro do Docker

### Problema: "Database connection failed"

**Soluções:**

1. **Verificar URL de conexão:**
   ```bash
   # Para FastAPI (asyncpg)
   DATABASE_URL=postgresql+asyncpg://user:senha@host:porta/db?ssl=require
   
   # Para Alembic e MLflow (psycopg2)
   postgresql://user:senha@host:porta/db
   ```

2. **Verificar firewall:**
   - TimescaleDB Cloud: Adicionar IP da VM em allowed IPs
   - AWS Security Group: Verificar portas abertas

3. **Testar conexão:**
   ```bash
   pip install psycopg2-binary
   python -c "
   import psycopg2
   conn = psycopg2.connect('postgresql://user:senha@host:porta/db')
   print('Conexão OK')
   conn.close()
   "
   ```

### Problema: "Redis connection timeout"

**Soluções:**

1. Verificar formato da URL:
   ```bash
   # Render Redis (com TLS)
   REDIS_URL=rediss://red-xxxx:senha@host:6379
   
   # Redis local
   REDIS_URL=redis://localhost:6379/0
   ```

2. Testar conexão:
   ```bash
   pip install redis
   python -c "
   import redis
   r = redis.from_url('sua_redis_url')
   r.ping()
   print('Redis OK')
   "
   ```

### Problema: "MLflow artifacts not found"

**Soluções:**

1. Verificar credenciais AWS:
   ```bash
   aws s3 ls s3://seu-bucket/
   ```

2. Verificar variáveis de ambiente:
   ```bash
   echo $AWS_ACCESS_KEY_ID
   echo $MLFLOW_ARTIFACT_ROOT
   ```

3. Verificar que modelos foram sincronizados:
   ```bash
   aws s3 ls s3://seu-bucket/ --recursive
   ```

### Problema: UI não conecta à API

**Soluções:**

1. **Verificar API_BASE_URL:**
   - Local: `http://api:8000` (dentro do Docker)
   - Cloud: `http://SEU_IP_PUBLICO:8000` (Streamlit Cloud → VM)

2. **Verificar firewall:**
   - AWS Security Group deve permitir porta 8000
   - Verificar que API responde: `curl http://IP:8000/health`

3. **Verificar secrets do Streamlit Cloud:**
   - Secrets → Verificar `API_BASE_URL` está correto

### Problema: "Port already in use"

**Solução:**
```bash
# Identificar processo usando a porta
sudo lsof -i :8000
sudo lsof -i :5433

# Matar processo
sudo kill -9 PID

# Ou usar portas diferentes no docker-compose.yml
```

### Problema: "Out of disk space" na VM

**Soluções:**

1. Verificar uso:
   ```bash
   df -h
   ```

2. Limpar images Docker antigas:
   ```bash
   docker system prune -a
   ```

3. Limpar logs:
   ```bash
   sudo find /var/lib/docker/containers/ -name "*.log" -delete
   ```

4. Expandir volume da VM (AWS Console)

### Problema: Notebooks de treinamento falham

**Soluções:**

1. Verificar que datasets estão presentes:
   ```bash
   ls -lh data/
   ```

2. Verificar memória disponível:
   ```bash
   free -h
   # Notebooks grandes (MIMII) precisam de 8GB+
   ```

3. Executar notebooks um de cada vez:
   ```bash
   # Ao invés de todos de uma vez
   make synthetic-anomaly
   # Aguardar completar, depois
   make synthetic-forecast
   ```

---

## Próximos Passos

### Após Implantação Bem-Sucedida

1. **Explorar Documentação:**
   - [Sistema & Arquitetura](SYSTEM_AND_ARCHITECTURE.md)
   - [Referência da API](api.md)
   - [Documentação ML](ml/README.md)

2. **Testar Recursos Avançados:**
   - Detecção de drift de dados
   - Validação de modelos
   - Logs de auditoria
   - Console de simulação

3. **Personalizar para Seu Caso de Uso:**
   - Adaptar modelos para seus dados
   - Configurar alertas e notificações
   - Integrar com sistemas existentes

4. **Monitoramento de Produção:**
   - Configurar alertas (Slack, email)
   - Monitorar métricas Prometheus
   - Revisar logs regularmente

5. **Backup e Recuperação:**
   - Configurar backups automáticos do TimescaleDB
   - Sincronizar artefatos S3 regularmente
   - Documentar procedimentos de recuperação

### Recursos Adicionais

- **Guia de Implantação Cloud Completo:** [UNIFIED_CLOUD_DEPLOYMENT_GUIDE.md](UNIFIED_CLOUD_DEPLOYMENT_GUIDE.md)
- **Configuração DVC:** [DVC_SETUP_GUIDE.md](DVC_SETUP_GUIDE.md)
- **Segurança:** [SECURITY.md](SECURITY.md)
- **Sumário Executivo:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)

### Suporte

Para questões, problemas ou sugestões:
- **Issues GitHub:** https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply/issues
- **Email:** yanpcotta@gmail.com
- **LinkedIn:** https://www.linkedin.com/in/yan-cotta/

---

## Licença & Autorização

Qualquer uso deste código exige autorização escrita prévia de Yan Pimentel Cotta e deve incluir atribuição explícita. Consulte o arquivo [LICENSE](../../LICENSE) para detalhes completos.

**Contatos para Autorização:**
- Email: yanpcotta@gmail.com
- LinkedIn: https://www.linkedin.com/in/yan-cotta/
- GitHub: https://github.com/YanCotta

---

**Última Atualização:** 2025-10-03  
**Versão do Guia:** 1.0  
**Status:** ✅ Pronto para Produção
