-- Elite Creatif PostgreSQL Database Setup
-- This script creates the database and user for the application

-- Drop database if exists (for clean setup)
DROP DATABASE IF EXISTS elite_creatif_saas;

-- Create database
CREATE DATABASE elite_creatif_saas
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Connect to the new database
\c elite_creatif_saas

-- Create UUID extension (required for UUID primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create application user with secure password
CREATE USER elite_creatif_user WITH PASSWORD 'EliteCreatif2025!SecurePass';

-- Grant all privileges on database to user
GRANT ALL PRIVILEGES ON DATABASE elite_creatif_saas TO elite_creatif_user;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO elite_creatif_user;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO elite_creatif_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO elite_creatif_user;

-- Success message
\echo 'Database setup completed successfully!'
\echo 'Database: elite_creatif_saas'
\echo 'User: elite_creatif_user'
