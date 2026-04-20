## Inclusion Intelligence System (IIS)

# Project Overview

The Inclusion Intelligence System is a web-based platform designed to help organizations assess their inclusion practices 
across key dimensions such as hiring, onboarding, accommodation, retention and culture.

# SYSTEM SETUP GUIDE
  1. Clone the Repository

     git clone https://github.com/mock_iis.git
     cd (your-project-profile)

# DATABASE SETUP (MySQL Workbench)
  Step 1: Open MyQL Workbench and connect to your local server
  Step 2: Create Database
          Run this command: CREATE DATABASE iis_db;
  Step 3: Import Database File

          1. Go to Server -> Data Import
          2. Select -> Import from Self-Contained File
          3. Browse and select -> iis_db.sql
          4. Under Default Target Schema, choose: -> iis_db
          5. Click -> Start Import          

  Step 4: Verify Tables
          Run this command: SHOW TABLES;

# USER ROLES
  . VIRTUALAHAN ADMIN
      - Approves access request
      - Manges question bank
      - Oversees system

  . ORGANIZATION ADMIN
      - Submit assessments
      - View dashboard results
      - Manages Organization data

# SYSTEM FLOW
   1. Organizations signedup and submits for approval
   2. Virtualahan reviews and approves request
   3. Approved organization can log in
   4. Organization completes assessment
   5. System generates:
        . Scores
        . Gap Analysis
        . Dashboard Insights
  6. Options
        . PDF report export
        . Fellow tracking

# Project Structure

        project-folder/
        |___database/
        |   |___iis_db.sql
        |___templates/
        |___static/
        |___app.py
        |___README.md

# Note: Always pull latest changes before starting:

#  TECH STACK
      . Frontend: HTML, CSS, JavaScript
      . Backend: Python (FLASK)
      . Database: MySQL

# DEVELOPERS
     


