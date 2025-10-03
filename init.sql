-- PostgreSQL initialization script for Enterprise Knowledge Assistant
-- This file is executed when the PostgreSQL container starts for the first time

-- Create database (this is done by environment variables, but keeping for reference)
-- CREATE DATABASE enterprise_kb;

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create a schema for the application (optional, tables will be created by SQLAlchemy)
-- CREATE SCHEMA IF NOT EXISTS app;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Enterprise Knowledge Assistant PostgreSQL database initialized successfully';
END $$;