-- PostgreSQL 15+ revoked the CREATE privilege on the public schema from
-- PUBLIC (all roles) by default.  This init script restores the minimum
-- required privileges for the application database owner so that Django
-- migrations succeed.
-- Reference: https://www.postgresql.org/docs/15/release-15.html

GRANT USAGE, CREATE ON SCHEMA public TO CURRENT_USER;
