-- supabase/migrations/20250103_workflow_tables.sql

-- =====================================================
-- WORKFLOW AUTOMATION TABLES
-- For visual workflow builder (automation workflows)
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. WORKFLOW FLOWS TABLE
-- Stores the main workflow/automation definitions
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_flows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner UUID NOT NULL,
    org_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) DEFAULT 'automation' CHECK (type IN ('automation', 'pipeline')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes for performance
    CONSTRAINT workflow_flows_owner_fkey FOREIGN KEY (owner) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Row Level Security
ALTER TABLE workflow_flows ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own flows
CREATE POLICY "Users own their flows"
    ON workflow_flows FOR ALL
    USING (auth.uid() = owner);

-- Indexes
CREATE INDEX idx_workflow_flows_owner ON workflow_flows(owner);
CREATE INDEX idx_workflow_flows_status ON workflow_flows(status);
CREATE INDEX idx_workflow_flows_type ON workflow_flows(type);
CREATE INDEX idx_workflow_flows_org ON workflow_flows(org_id) WHERE org_id IS NOT NULL;

-- =====================================================
-- 2. WORKFLOW NODES TABLE
-- Individual steps/actions in a workflow
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id UUID NOT NULL REFERENCES workflow_flows(id) ON DELETE CASCADE,
    node_type VARCHAR(100) NOT NULL,
    label VARCHAR(255),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    position JSONB DEFAULT '{"x": 0, "y": 0}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- node_type examples: 'gmail_trigger', 'calendar_action', 'condition', 'webhook'
    CONSTRAINT valid_position CHECK (
        jsonb_typeof(position) = 'object' AND
        position ? 'x' AND
        position ? 'y'
    )
);

-- Indexes
CREATE INDEX idx_workflow_nodes_flow ON workflow_nodes(flow_id);
CREATE INDEX idx_workflow_nodes_type ON workflow_nodes(node_type);

-- =====================================================
-- 3. WORKFLOW EDGES TABLE  
-- Connections between nodes
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id UUID NOT NULL REFERENCES workflow_flows(id) ON DELETE CASCADE,
    from_node UUID NOT NULL REFERENCES workflow_nodes(id) ON DELETE CASCADE,
    to_node UUID NOT NULL REFERENCES workflow_nodes(id) ON DELETE CASCADE,
    condition JSONB,
    label VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate edges
    CONSTRAINT unique_edge UNIQUE (flow_id, from_node, to_node),
    
    -- Prevent self-loops
    CONSTRAINT no_self_loops CHECK (from_node != to_node)
);

-- Indexes
CREATE INDEX idx_workflow_edges_flow ON workflow_edges(flow_id);
CREATE INDEX idx_workflow_edges_from ON workflow_edges(from_node);
CREATE INDEX idx_workflow_edges_to ON workflow_edges(to_node);

-- =====================================================
-- 4. WORKFLOW RUNS TABLE
-- Execution history and logs
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id UUID NOT NULL REFERENCES workflow_flows(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('pending', 'running', 'success', 'error', 'timeout', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    trigger_data JSONB DEFAULT '{}'::jsonb,
    logs JSONB DEFAULT '[]'::jsonb,
    step_results JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Performance constraint
    CONSTRAINT valid_completion CHECK (
        (status IN ('success', 'error', 'timeout', 'cancelled') AND completed_at IS NOT NULL) OR
        (status IN ('pending', 'running') AND completed_at IS NULL)
    )
);

-- Indexes
CREATE INDEX idx_workflow_runs_flow ON workflow_runs(flow_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX idx_workflow_runs_started ON workflow_runs(started_at DESC);

-- =====================================================
-- 5. WORKFLOW CREDENTIALS TABLE
-- OAuth tokens and API keys for connectors
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner UUID NOT NULL,
    provider VARCHAR(100) NOT NULL,
    label VARCHAR(255),
    account_identifier VARCHAR(255),
    encrypted_token TEXT NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    scopes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Unique constraint per user per provider account
    CONSTRAINT unique_credential UNIQUE (owner, provider, account_identifier),
    CONSTRAINT workflow_credentials_owner_fkey FOREIGN KEY (owner) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Row Level Security
ALTER TABLE workflow_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own their credentials"
    ON workflow_credentials FOR ALL
    USING (auth.uid() = owner);

-- Indexes
CREATE INDEX idx_workflow_credentials_owner ON workflow_credentials(owner);
CREATE INDEX idx_workflow_credentials_provider ON workflow_credentials(provider);

-- =====================================================
-- 6. WORKFLOW VALIDATION ISSUES TABLE
-- Track validation problems for flows
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_validation_issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_id UUID NOT NULL REFERENCES workflow_flows(id) ON DELETE CASCADE,
    severity VARCHAR(20) CHECK (severity IN ('error', 'warning', 'info')),
    issue_type VARCHAR(100) NOT NULL,
    node_id UUID REFERENCES workflow_nodes(id) ON DELETE CASCADE,
    field_name VARCHAR(255),
    message TEXT NOT NULL,
    suggested_fix TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_validation_issues_flow ON workflow_validation_issues(flow_id);
CREATE INDEX idx_validation_issues_unresolved ON workflow_validation_issues(flow_id) WHERE resolved_at IS NULL;

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER update_workflow_flows_updated_at
    BEFORE UPDATE ON workflow_flows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_nodes_updated_at
    BEFORE UPDATE ON workflow_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_credentials_updated_at
    BEFORE UPDATE ON workflow_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Get flow with all nodes and edges
CREATE OR REPLACE FUNCTION get_complete_flow(flow_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'flow', row_to_json(f.*),
        'nodes', COALESCE(
            (SELECT json_agg(row_to_json(n.*))
             FROM workflow_nodes n
             WHERE n.flow_id = flow_uuid),
            '[]'::json
        ),
        'edges', COALESCE(
            (SELECT json_agg(row_to_json(e.*))
             FROM workflow_edges e
             WHERE e.flow_id = flow_uuid),
            '[]'::json
        )
    ) INTO result
    FROM workflow_flows f
    WHERE f.id = flow_uuid;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE workflow_flows IS 'Main workflow automation definitions';
COMMENT ON TABLE workflow_nodes IS 'Individual steps in workflows';
COMMENT ON TABLE workflow_edges IS 'Connections between workflow nodes';
COMMENT ON TABLE workflow_runs IS 'Execution history and logs';
COMMENT ON TABLE workflow_credentials IS 'OAuth tokens for connectors';
COMMENT ON TABLE workflow_validation_issues IS 'Validation problems tracking';

COMMENT ON COLUMN workflow_flows.type IS 'automation = visual workflow builder, pipeline = CRM pipeline automation';
COMMENT ON COLUMN workflow_flows.status IS 'draft = being edited, active = running, paused = temporarily stopped, archived = deleted but kept';