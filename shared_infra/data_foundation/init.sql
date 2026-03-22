-- AXEworks Foundation Engine - Initial Database Schema
-- Non-destructive: all AX tables are prefixed with ax_ to avoid collisions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- Shared: Audit & Governance
-- ============================================================
CREATE TABLE IF NOT EXISTS ax_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service VARCHAR(64) NOT NULL,
    action VARCHAR(128) NOT NULL,
    actor VARCHAR(128),
    resource_type VARCHAR(64),
    resource_id VARCHAR(256),
    detail JSONB DEFAULT '{}',
    confidence_score FLOAT,
    outcome VARCHAR(32) DEFAULT 'success'
);

CREATE INDEX idx_audit_timestamp ON ax_audit_log(timestamp DESC);
CREATE INDEX idx_audit_service ON ax_audit_log(service);

-- ============================================================
-- Policy Engine
-- ============================================================
CREATE TABLE IF NOT EXISTS ax_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(256) NOT NULL UNIQUE,
    description TEXT,
    domain VARCHAR(64) NOT NULL DEFAULT 'global',
    rules JSONB NOT NULL DEFAULT '[]',
    priority INT NOT NULL DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ax_approval_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES ax_policies(id),
    requested_by VARCHAR(128) NOT NULL,
    action_type VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    decided_by VARCHAR(128),
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AXEngine: Orchestrator State
-- ============================================================
CREATE TABLE IF NOT EXISTS ax_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(512) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    priority INT DEFAULT 50,
    created_by VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ax_execution_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID REFERENCES ax_goals(id) ON DELETE CASCADE,
    steps JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(32) NOT NULL DEFAULT 'planned',
    current_step INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ax_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES ax_execution_plans(id) ON DELETE CASCADE,
    step_index INT NOT NULL,
    agent_name VARCHAR(128),
    action VARCHAR(256),
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    confidence FLOAT,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ============================================================
-- AXEngine: Human-in-the-Loop Override Tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS ax_hitl_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_log_id UUID REFERENCES ax_execution_logs(id),
    original_action JSONB NOT NULL,
    override_action JSONB NOT NULL,
    reason TEXT,
    overridden_by VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AXE_POE: Operation Pipeline State
-- ============================================================
CREATE TABLE IF NOT EXISTS ax_poe_data_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(128) NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    raw_payload JSONB NOT NULL,
    normalized_payload JSONB,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_poe_events_source ON ax_poe_data_events(source, event_type);
CREATE INDEX idx_poe_events_time ON ax_poe_data_events(captured_at DESC);

CREATE TABLE IF NOT EXISTS ax_poe_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES ax_poe_data_events(id),
    insight_type VARCHAR(128) NOT NULL,
    severity VARCHAR(32) DEFAULT 'info',
    summary TEXT NOT NULL,
    detail JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ax_poe_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    insight_id UUID REFERENCES ax_poe_insights(id),
    recommended_action VARCHAR(256) NOT NULL,
    action_params JSONB DEFAULT '{}',
    confidence FLOAT NOT NULL,
    policy_check_result JSONB DEFAULT '{}',
    status VARCHAR(32) DEFAULT 'proposed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ax_poe_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID REFERENCES ax_poe_decisions(id),
    action_type VARCHAR(128) NOT NULL,
    target_system VARCHAR(128),
    request_payload JSONB DEFAULT '{}',
    response_payload JSONB DEFAULT '{}',
    status VARCHAR(32) DEFAULT 'pending',
    executed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ax_poe_learning_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES ax_poe_executions(id),
    metric_name VARCHAR(128) NOT NULL,
    metric_value FLOAT,
    feedback_type VARCHAR(64) DEFAULT 'auto',
    detail JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- poQat: Health Monitoring
-- ============================================================
CREATE TABLE IF NOT EXISTS ax_service_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
    latency_ms FLOAT,
    error_count INT DEFAULT 0,
    detail JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_service ON ax_service_health(service_name, checked_at DESC);

CREATE TABLE IF NOT EXISTS ax_agent_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(128) NOT NULL,
    domain VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
    tasks_completed INT DEFAULT 0,
    tasks_failed INT DEFAULT 0,
    avg_confidence FLOAT,
    detail JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT NOW()
);
