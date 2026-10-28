# FolioForge — Resume Builder

A database-focused mini project using Flask, Oracle SQL, and PL/SQL. FolioForge stores candidate profiles and resume sections in relational tables, uses stored procedures for inserts, and records profile changes in an audit log.

## Features
- Resume profile creation and printable resume preview
- Education, experience, skills, and project sections
- Oracle relational schema with constraints and indexes
- PL/SQL package for data operations and validation
- Audit triggers and timestamp maintenance
- Responsive interface and browser print-to-PDF

## Setup
1. Install Oracle Database XE or Oracle Database Free.
2. Create an app user and grant permissions:
   ```sql
   CREATE USER folioforge IDENTIFIED BY "ChangeThisPassword";
   GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE PROCEDURE, CREATE TRIGGER, CREATE SEQUENCE TO folioforge;
   ALTER USER folioforge QUOTA UNLIMITED ON USERS;
   ```
3. Connect as `FOLIOFORGE` and run `database/01_schema.sql`, `database/02_package.sql`, then `database/03_triggers.sql`.
4. Create a virtual environment and install packages:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env`, then set the Oracle credentials and DSN. Typical DSNs are `localhost:1521/XEPDB1` or `localhost:1521/FREEPDB1`, depending on your installation.
6. Run `python app.py`, then open `http://127.0.0.1:5000`.

## PL/SQL concepts
Primary/foreign keys, check constraints, stored package procedures, exception handling, triggers, audit logging, transactions, and referential integrity.

## Scope note
This is a classroom mini project, not a production service. Before public deployment, add authentication, CSRF protection, stronger validation, and operational security. Never commit `.env` credentials.
