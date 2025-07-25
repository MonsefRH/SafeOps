CREATE SEQUENCE users_id_seq ;

-- Update the users table to include a role column
CREATE TABLE users (
    id INTEGER NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    name CHARACTER VARYING(100) NOT NULL,
    email CHARACTER VARYING(100) NOT NULL,
    password TEXT,
    role CHARACTER VARYING(20) NOT NULL DEFAULT 'user', 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT unique_email UNIQUE (email),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT valid_role CHECK (role IN ('user', 'admin')) 
);
ALTER SEQUENCE users_id_seq OWNED BY users.id;

---------------------------------------------
---Create github_users table
CREATE TABLE IF NOT EXISTS github_users (
    user_id INTEGER PRIMARY KEY,
    github_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT github_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT github_users_github_id_key UNIQUE (github_id)
);

-- Create index for github_users
CREATE INDEX IF NOT EXISTS github_users_pkey ON github_users (user_id);

-- Create sequence for selected_repos
CREATE SEQUENCE IF NOT EXISTS selected_repos_id_seq;

------------------------------------------------------------------------
-- Create sequence for selected_repos.id

CREATE SEQUENCE selected_repos_id_seq;
-- Create selected_repos table
CREATE TABLE selected_repos (
    id INTEGER PRIMARY KEY DEFAULT nextval('selected_repos_id_seq'),
    user_id INTEGER,
    full_name VARCHAR(255),
    name VARCHAR(255),
    html_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT selected_repos_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT selected_repos_full_name_key UNIQUE (full_name)
);

-- Create index for primary key
CREATE INDEX selected_repos_pkey ON selected_repos (id);

-- Set sequence ownership
ALTER SEQUENCE selected_repos_id_seq OWNED BY selected_repos.id;


------------------------------------------------------------------------------
-- Create sequence for repo_configs.id
CREATE SEQUENCE repo_configs_id_seq;

-- Create repo_configs table
CREATE TABLE repo_configs (
    id INTEGER PRIMARY KEY DEFAULT nextval('repo_configs_id_seq'),
    repo_id INTEGER,
    file_path VARCHAR(255),
    file_name VARCHAR(255),
    content BYTEA,
    sha VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    framework VARCHAR(50),
    CONSTRAINT repo_configs_repo_id_fkey
        FOREIGN KEY (repo_id)
        REFERENCES selected_repos(id)
        ON DELETE CASCADE,
    CONSTRAINT unique_file_path_repo_id
        UNIQUE (file_path, repo_id)
);


-- Create index for primary key
CREATE INDEX repo_configs_pkey ON repo_configs (id);

-- Set sequence ownership
ALTER SEQUENCE repo_configs_id_seq OWNED BY repo_configs.id;



------------------------------------------------------------------------

CREATE SEQUENCE scan_history_id_seq ;


CREATE TABLE scan_history (
    id INTEGER NOT NULL DEFAULT nextval('scan_history_id_seq'::regclass),
    user_id INTEGER NOT NULL,
    repo_id INTEGER,
    scan_result JSONB NOT NULL,
    repo_url TEXT,
    status CHARACTER VARYING(50) NOT NULL,
    score INTEGER,
    compliant BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    input_type CHARACTER VARYING(50),
    scan_type VARCHAR(50),
    CONSTRAINT scan_history_pkey PRIMARY KEY (id),
    CONSTRAINT scan_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT scan_history_repo_id_fkey FOREIGN KEY (repo_id) REFERENCES selected_repos(id) ON DELETE SET NULL
);

ALTER SEQUENCE scan_history_id_seq OWNED BY scan_history.id;



----------------------------------------------------------------------
CREATE TABLE file_contents (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER ,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    input_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scan_history(id) ON DELETE CASCADE
);


------------------------------------------------------------
CREATE TABLE pending_users (
    email VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    verification_code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
