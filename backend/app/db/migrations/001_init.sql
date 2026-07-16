CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS service_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    embedding VECTOR(1536),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type TEXT NOT NULL CHECK (doc_type IN ('service_line_description', 'past_proposal', 'positioning_note')),
    service_line TEXT,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    note TEXT,
    classification TEXT NOT NULL CHECK (classification IN ('training', 'consulting', 'retainer', 'certification', 'other')),
    brief TEXT NOT NULL,
    talking_points JSONB NOT NULL,
    rationale TEXT NOT NULL,
    reference_doc_ids JSONB NOT NULL DEFAULT '[]',
    low_confidence BOOLEAN NOT NULL DEFAULT FALSE,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS profiles_company_name_unique ON profiles (lower(company_name));

CREATE TABLE IF NOT EXISTS scout_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id),
    search_queries JSONB NOT NULL DEFAULT '[]',
    search_results_raw JSONB NOT NULL DEFAULT '[]',
    attempts INT NOT NULL DEFAULT 0,
    duration_ms INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO service_lines (key, label, description)
VALUES
    ('training', 'Corporate analytics/BI training', 'Corporate analytics/BI training such as Power BI training, similar to the Groupe Clarins engagement.'),
    ('consulting', 'Dashboard/consulting engagement', 'Dashboard or consulting engagement delivered as a phased project, similar to the Children''s Aid Society (CAS) engagement.'),
    ('retainer', 'Ongoing retainer', 'Ongoing retainer for monitoring and maintenance work, similar to the Alcon engagement.'),
    ('certification', 'Certification/instructor placement', 'Certification or instructor placement work, similar to the Xaltius and Acadwizz engagements.'),
    ('other', 'Other / unclear', 'Lead does not clearly fit an existing service line yet.')
ON CONFLICT (key) DO NOTHING;
