# Brazilian Portuguese Translations for Smart Maintenance SaaS UI

"""
This module provides Brazilian Portuguese (pt-BR) translations for all UI text elements.
Each translation includes the English original and Portuguese translation.
"""

TRANSLATIONS = {
    # ==================== MANUAL SENSOR INGESTION ====================
    "manual_ingestion": {
        "page_title": ("📡 Manual Sensor Ingestion", "📡 Ingestão Manual de Sensores"),
        "description": (
            "Submit individual sensor readings to the system for processing and analysis",
            "Envie leituras individuais de sensores para processamento e análise no sistema"
        ),
        "sensor_id_label": ("Sensor ID", "ID do Sensor"),
        "sensor_id_help": (
            "Unique identifier for the sensor (e.g., sensor-001)",
            "Identificador único do sensor (ex: sensor-001)"
        ),
        "sensor_type_label": ("Sensor Type", "Tipo de Sensor"),
        "sensor_type_help": (
            "Type of measurement: temperature, pressure, vibration, etc.",
            "Tipo de medição: temperatura, pressão, vibração, etc."
        ),
        "value_label": ("Value", "Valor"),
        "value_help": (
            "Numerical reading from the sensor",
            "Leitura numérica do sensor"
        ),
        "unit_label": ("Unit", "Unidade"),
        "unit_help": (
            "Measurement unit (e.g., celsius, bar, Hz)",
            "Unidade de medida (ex: celsius, bar, Hz)"
        ),
        "submit_button": ("Ingest Data", "Ingerir Dados"),
        "success_message": (
            "✅ Data ingested successfully",
            "✅ Dados ingeridos com sucesso"
        ),
        "verification_pending": (
            "⏳ Verification pending (eventual consistency)",
            "⏳ Verificação pendente (consistência eventual)"
        ),
    },
    
    # ==================== DATA EXPLORER ====================
    "data_explorer": {
        "page_title": ("📊 Data Explorer", "📊 Explorador de Dados"),
        "description": (
            "Browse and analyze sensor readings with advanced filtering and pagination",
            "Navegue e analise leituras de sensores com filtragem avançada e paginação"
        ),
        "sensor_filter": ("Select Sensor", "Selecionar Sensor"),
        "sensor_filter_help": (
            "Filter readings by specific sensor ID",
            "Filtrar leituras por ID específico de sensor"
        ),
        "date_range": ("Date Range", "Intervalo de Datas"),
        "date_range_help": (
            "Filter readings between start and end dates",
            "Filtrar leituras entre datas inicial e final"
        ),
        "start_date": ("Start Date", "Data Inicial"),
        "end_date": ("End Date", "Data Final"),
        "limit_label": ("Readings per Page", "Leituras por Página"),
        "limit_help": (
            "Number of readings to display (10-100)",
            "Número de leituras para exibir (10-100)"
        ),
        "load_button": ("Load Data", "Carregar Dados"),
        "export_button": ("Export to CSV", "Exportar para CSV"),
        "no_data": ("No readings found", "Nenhuma leitura encontrada"),
        "loading": ("Loading sensor data...", "Carregando dados dos sensores..."),
    },
    
    # ==================== DECISION LOG ====================
    "decision_log": {
        "page_title": ("📋 Decision Log", "📋 Registro de Decisões"),
        "description": (
            "Submit and track human maintenance decisions for audit and compliance",
            "Registre e acompanhe decisões de manutenção para auditoria e conformidade"
        ),
        "submit_section": ("Submit New Decision", "Registrar Nova Decisão"),
        "request_id": ("Request ID", "ID da Solicitação"),
        "request_id_help": (
            "Unique identifier for the maintenance request",
            "Identificador único da solicitação de manutenção"
        ),
        "decision_type": ("Decision", "Decisão"),
        "decision_approve": ("Approve", "Aprovar"),
        "decision_reject": ("Reject", "Rejeitar"),
        "decision_defer": ("Defer", "Adiar"),
        "justification": ("Justification", "Justificativa"),
        "justification_help": (
            "Explanation for the decision made",
            "Explicação para a decisão tomada"
        ),
        "operator_id": ("Operator ID", "ID do Operador"),
        "operator_id_help": (
            "Identifier of the person making the decision",
            "Identificador da pessoa tomando a decisão"
        ),
        "submit_button": ("Submit Decision", "Registrar Decisão"),
        "view_section": ("Decision History", "Histórico de Decisões"),
        "filter_label": ("Filter by", "Filtrar por"),
        "scope_note": (
            "ℹ️ V1.0 Scope: Create and list only (no edit/delete)",
            "ℹ️ Escopo V1.0: Criar e listar apenas (sem editar/excluir)"
        ),
    },
    
    # ==================== GOLDEN PATH DEMO ====================
    "golden_path": {
        "page_title": ("🛤️ Golden Path Demo", "🛤️ Demonstração do Fluxo Completo"),
        "description": (
            "End-to-end demonstration of the multi-agent predictive maintenance pipeline",
            "Demonstração completa do pipeline de manutenção preditiva multi-agente"
        ),
        "sensor_events_label": ("Sensor Events to Generate", "Eventos de Sensor a Gerar"),
        "sensor_events_help": (
            "Number of synthetic sensor readings (5-100)",
            "Número de leituras sintéticas de sensores (5-100)"
        ),
        "include_decision": ("Include Human Decision Stage", "Incluir Etapa de Decisão Humana"),
        "include_decision_help": (
            "Enable manual approval workflow for maintenance",
            "Ativar fluxo de aprovação manual para manutenção"
        ),
        "start_button": ("Start Demo", "Iniciar Demonstração"),
        "pipeline_steps": ("Pipeline Steps", "Etapas do Pipeline"),
        "event_stream": ("Event Stream", "Fluxo de Eventos"),
        "metrics_tab": ("Metrics", "Métricas"),
        "completion_message": (
            "✅ Completed Successfully",
            "✅ Concluído com Sucesso"
        ),
        "timeout_warning": (
            "⏱️ Demo completion target: <90 seconds",
            "⏱️ Meta de conclusão: <90 segundos"
        ),
        "stages": {
            "ingestion": ("Ingestion", "Ingestão"),
            "processing": ("Processing", "Processamento"),
            "anomaly_detection": ("Anomaly Detection", "Detecção de Anomalias"),
            "validation": ("Validation", "Validação"),
            "prediction": ("Prediction", "Predição"),
            "maintenance": ("Maintenance", "Manutenção"),
            "human_decision": ("Human Decision", "Decisão Humana"),
        },
    },
    
    # ==================== PREDICTION ====================
    "prediction": {
        "page_title": ("🔮 Prediction", "🔮 Predição"),
        "description": (
            "Generate maintenance forecasts and create automated maintenance orders",
            "Gere previsões de manutenção e crie ordens de manutenção automatizadas"
        ),
        "sensor_type_label": ("Sensor Type", "Tipo de Sensor"),
        "sensor_selector": ("Select Sensor", "Selecionar Sensor"),
        "model_section": ("Baseline Model", "Modelo Base"),
        "model_description": (
            "Prophet-based forecaster for synthetic temperature baseline",
            "Modelo de previsão Prophet para baseline de temperatura sintética"
        ),
        "history_window": ("History Window (readings)", "Janela de Histórico (leituras)"),
        "history_window_help": (
            "Number of historical readings to analyze",
            "Número de leituras históricas para analisar"
        ),
        "forecast_horizon": ("Forecast Horizon (steps)", "Horizonte de Previsão (passos)"),
        "forecast_horizon_help": (
            "Number of future time steps to predict",
            "Número de passos futuros para prever"
        ),
        "run_forecast": ("Run Forecast", "Executar Previsão"),
        "forecast_table": ("Forecast Table", "Tabela de Previsão"),
        "historical_context": ("Historical Context", "Contexto Histórico"),
        "maintenance_automation": ("Maintenance Automation (Demo Pipeline)", "Automação de Manutenção (Pipeline Demo)"),
        "maintenance_description": (
            "Trigger the multi-agent scheduling workflow",
            "Acionar o fluxo de agendamento multi-agente"
        ),
        "create_order_button": ("Create Maintenance Order", "Criar Ordem de Manutenção"),
        "order_success": (
            "✅ Maintenance order dispatched. Check the Reporting Prototype for the live feed.",
            "✅ Ordem de manutenção enviada. Verifique o Protótipo de Relatórios para o feed ao vivo."
        ),
    },
    
    # ==================== MODEL METADATA ====================
    "model_metadata": {
        "page_title": ("🛠️ Model Metadata", "🛠️ Metadados do Modelo"),
        "description": (
            "View registered machine learning models and their configuration",
            "Visualize modelos de machine learning registrados e suas configurações"
        ),
        "registry_status": ("MLflow Registry Status", "Status do Registro MLflow"),
        "enabled_badge": ("🟢 Enabled", "🟢 Ativado"),
        "disabled_badge": ("🔴 Disabled (Offline Mode)", "🔴 Desativado (Modo Offline)"),
        "model_list": ("Available Models", "Modelos Disponíveis"),
        "model_name": ("Model Name", "Nome do Modelo"),
        "model_version": ("Version", "Versão"),
        "model_stage": ("Stage", "Estágio"),
        "no_models": (
            "No models available (MLflow disabled or empty registry)",
            "Nenhum modelo disponível (MLflow desativado ou registro vazio)"
        ),
    },
    
    # ==================== SIMULATION CONSOLE ====================
    "simulation": {
        "page_title": ("🎮 Simulation Console", "🎮 Console de Simulação"),
        "description": (
            "Simulate system conditions to demonstrate drift, anomalies, and baseline data flows",
            "Simule condições do sistema para demonstrar desvios, anomalias e fluxos de dados baseline"
        ),
        "drift_tab": ("Drift", "Desvio"),
        "drift_description": (
            "Generate gradual drift in sensor readings to trigger MLOps loop",
            "Gere desvio gradual em leituras de sensores para acionar loop MLOps"
        ),
        "anomaly_tab": ("Anomaly", "Anomalia"),
        "anomaly_description": (
            "Inject sudden anomalies into sensor data stream",
            "Injete anomalias repentinas no fluxo de dados dos sensores"
        ),
        "normal_tab": ("Normal", "Normal"),
        "normal_description": (
            "Generate baseline readings without anomalies or drift for model context",
            "Gere leituras baseline sem anomalias ou desvios para contexto do modelo"
        ),
        "sensor_id_auto": ("Sensor ID (blank = auto)", "ID do Sensor (vazio = automático)"),
        "num_samples": ("Num Samples", "Número de Amostras"),
        "duration_mins": ("Duration (mins)", "Duração (mins)"),
        "drift_magnitude": ("Drift Magnitude (σ)", "Magnitude do Desvio (σ)"),
        "anomaly_magnitude": ("Anomaly Magnitude", "Magnitude da Anomalia"),
        "launch_button": ("Launch Simulation", "Iniciar Simulação"),
        "recent_runs": ("Recent Simulation Runs", "Execuções Recentes"),
    },
    
    # ==================== METRICS OVERVIEW ====================
    "metrics": {
        "page_title": ("📈 Metrics Overview", "📈 Visão Geral de Métricas"),
        "description": (
            "View Prometheus metrics snapshot (no streaming in V1.0)",
            "Visualize snapshot de métricas Prometheus (sem streaming na V1.0)"
        ),
        "snapshot_label": ("📊 Snapshot Only (V1.0)", "📊 Apenas Snapshot (V1.0)"),
        "refresh_button": ("Refresh Metrics", "Atualizar Métricas"),
        "auto_refresh": ("Auto-refresh", "Atualização automática"),
        "auto_refresh_help": (
            "Automatically refresh metrics every 30 seconds",
            "Atualizar métricas automaticamente a cada 30 segundos"
        ),
        "loading": ("Loading metrics...", "Carregando métricas..."),
    },
    
    # ==================== REPORTING PROTOTYPE ====================
    "reporting": {
        "page_title": ("📄 Reporting Prototype", "📄 Protótipo de Relatórios"),
        "description": (
            "Generate and preview maintenance reports (JSON only in V1.0)",
            "Gere e visualize relatórios de manutenção (apenas JSON na V1.0)"
        ),
        "prototype_badge": ("🚧 Prototype (JSON Only)", "🚧 Protótipo (Apenas JSON)"),
        "report_type": ("Report Type", "Tipo de Relatório"),
        "generate_button": ("Generate Report", "Gerar Relatório"),
        "download_button": ("Download JSON", "Baixar JSON"),
        "json_preview": ("JSON Preview", "Prévia JSON"),
        "maintenance_feed": ("Maintenance Schedule Feed", "Feed de Agendamento de Manutenção"),
        "no_schedules": (
            "No maintenance schedules recorded yet",
            "Nenhum agendamento de manutenção registrado ainda"
        ),
    },
    
    # ==================== DEBUG ====================
    "debug": {
        "page_title": ("🐛 Debug", "🐛 Depuração"),
        "description": (
            "System diagnostics and connectivity checks for troubleshooting",
            "Diagnósticos do sistema e verificações de conectividade para solução de problemas"
        ),
        "connectivity_section": ("Connectivity Checks", "Verificações de Conectividade"),
        "health_endpoint": ("Health Endpoint", "Endpoint de Saúde"),
        "database_status": ("Database Status", "Status do Banco de Dados"),
        "redis_status": ("Redis Status", "Status do Redis"),
        "api_base_url": ("API Base URL", "URL Base da API"),
        "latency_samples": ("Recent API Latencies", "Latências Recentes da API"),
        "config_inspection": ("Configuration Inspection", "Inspeção de Configuração"),
        "run_check": ("Run Checks", "Executar Verificações"),
    },
    
    # ==================== COMMON UI ELEMENTS ====================
    "common": {
        "loading": ("Loading...", "Carregando..."),
        "error": ("Error", "Erro"),
        "success": ("Success", "Sucesso"),
        "warning": ("Warning", "Aviso"),
        "info": ("Information", "Informação"),
        "close": ("Close", "Fechar"),
        "cancel": ("Cancel", "Cancelar"),
        "submit": ("Submit", "Enviar"),
        "reset": ("Reset", "Redefinir"),
        "refresh": ("Refresh", "Atualizar"),
        "export": ("Export", "Exportar"),
        "download": ("Download", "Baixar"),
        "view": ("View", "Visualizar"),
        "edit": ("Edit", "Editar"),
        "delete": ("Delete", "Excluir"),
        "search": ("Search", "Pesquisar"),
        "filter": ("Filter", "Filtrar"),
        "sort": ("Sort", "Ordenar"),
        "previous": ("Previous", "Anterior"),
        "next": ("Next", "Próximo"),
        "page": ("Page", "Página"),
        "of": ("of", "de"),
        "items": ("items", "itens"),
        "correlation_id": ("Correlation ID", "ID de Correlação"),
        "timestamp": ("Timestamp", "Data/Hora"),
        "status": ("Status", "Status"),
        "details": ("Details", "Detalhes"),
        "help": ("Help", "Ajuda"),
    },
}


def get_translation(key: str, subkey: str, lang: str = "en") -> str:
    """
    Get translation for a specific key.
    
    Args:
        key: Category key (e.g., "manual_ingestion")
        subkey: Specific translation key (e.g., "page_title")
        lang: Language code ("en" or "pt")
        
    Returns:
        Translated text
    """
    translation_tuple = TRANSLATIONS.get(key, {}).get(subkey, ("", ""))
    return translation_tuple[0] if lang == "en" else translation_tuple[1]


def help_tooltip(key: str, subkey: str) -> None:
    """
    Display help tooltip with English and Portuguese text.
    
    Args:
        key: Category key
        subkey: Specific translation key with "_help" suffix
    """
    import streamlit as st
    
    translation_tuple = TRANSLATIONS.get(key, {}).get(subkey, ("", ""))
    en_text, pt_text = translation_tuple
    
    with st.expander("ℹ️ Help / Ajuda"):
        st.write(f"**EN:** {en_text}")
        st.write(f"**🇧🇷 PT:** {pt_text}")


def bilingual_text(key: str, subkey: str) -> str:
    """
    Get bilingual text (English + Portuguese).
    
    Args:
        key: Category key
        subkey: Specific translation key
        
    Returns:
        Combined English and Portuguese text
    """
    translation_tuple = TRANSLATIONS.get(key, {}).get(subkey, ("", ""))
    en_text, pt_text = translation_tuple
    return f"{en_text} 🇧🇷 {pt_text}"
