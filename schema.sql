-- Linked Solutions API Documentation - Database Schema
-- SQLite Database

-- Create api_endpoints table
CREATE TABLE IF NOT EXISTS api_endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    http_method TEXT NOT NULL,
    route TEXT NOT NULL,
    parameters TEXT,
    description TEXT DEFAULT '',
    controller TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_endpoints_method ON api_endpoints(http_method);
CREATE INDEX IF NOT EXISTS idx_endpoints_controller ON api_endpoints(controller);
CREATE INDEX IF NOT EXISTS idx_endpoints_route ON api_endpoints(route);

-- Default admin user (password: admin)
-- Note: Password is hashed using bcrypt. The application handles this automatically
-- on first run. The default credentials are: admin / admin

-- Sample data
INSERT INTO api_endpoints (http_method, route, parameters, description, controller)
VALUES
    ('GET', '/api/TRS_TIERS/SelectOrderTiers', '{"sec": "string"}', 'Retrieves order tiers for a given security token', 'TRS_TIERS'),
    ('POST', '/api/TRS_TIERS/ChangeActivity', '{"ids": "List<string>", "act": "string"}', 'Changes activity status for the specified IDs', 'TRS_TIERS');

-- Example: How to add more endpoints manually
-- INSERT INTO api_endpoints (http_method, route, parameters, description, controller)
-- VALUES ('GET', '/api/USERS/GetAll', '', 'Get all users', 'USERS');