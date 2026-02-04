#!/usr/bin/env python3
"""
Database Migration Script for PV Management App

This script handles database schema migrations safely.
It checks for missing columns and adds them without affecting existing data.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from app.models import Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database URL from environment or default
DATABASE_URL = os.getenv("PVAPP_DB_URL", "sqlite:///./data/pvapp.db")

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_invoice_table(engine):
    """Add new columns to invoice table for file upload feature."""
    logger.info("Checking invoice table for missing columns...")
    
    migrations = [
        {
            'column': 'file_path',
            'sql': 'ALTER TABLE invoice ADD COLUMN file_path VARCHAR(500)',
            'description': 'Path to uploaded invoice file'
        },
        {
            'column': 'file_type',
            'sql': 'ALTER TABLE invoice ADD COLUMN file_type VARCHAR(10)',
            'description': 'File format (PDF, DOC, TXT, XML)'
        },
        {
            'column': 'raw_text',
            'sql': 'ALTER TABLE invoice ADD COLUMN raw_text TEXT',
            'description': 'Extracted text content from file'
        }
    ]
    
    with engine.connect() as conn:
        for migration in migrations:
            column = migration['column']
            if not check_column_exists(engine, 'invoice', column):
                try:
                    logger.info(f"Adding column '{column}' to invoice table...")
                    conn.execute(text(migration['sql']))
                    conn.commit()
                    logger.info(f"✓ Successfully added column '{column}' - {migration['description']}")
                except Exception as e:
                    logger.error(f"✗ Failed to add column '{column}': {e}")
                    conn.rollback()
                    raise
            else:
                logger.info(f"✓ Column '{column}' already exists, skipping")

def migrate_invoice_item_table(engine):
    """Add new columns to invoice_item table for better matching."""
    logger.info("Checking invoice_item table for missing columns...")
    
    migrations = [
        {
            'column': 'unit',
            'sql': 'ALTER TABLE invoice_item ADD COLUMN unit VARCHAR(20)',
            'description': 'Unit of measure'
        },
        {
            'column': 'suggested_material_id',
            'sql': 'ALTER TABLE invoice_item ADD COLUMN suggested_material_id INTEGER',
            'description': 'Suggested material match'
        },
        {
            'column': 'match_confidence',
            'sql': 'ALTER TABLE invoice_item ADD COLUMN match_confidence FLOAT',
            'description': 'Confidence score for material match'
        }
    ]
    
    with engine.connect() as conn:
        for migration in migrations:
            column = migration['column']
            if not check_column_exists(engine, 'invoice_item', column):
                try:
                    logger.info(f"Adding column '{column}' to invoice_item table...")
                    conn.execute(text(migration['sql']))
                    conn.commit()
                    logger.info(f"✓ Successfully added column '{column}' - {migration['description']}")
                except Exception as e:
                    logger.error(f"✗ Failed to add column '{column}': {e}")
                    conn.rollback()
                    raise
            else:
                logger.info(f"✓ Column '{column}' already exists, skipping")

def run_migrations():
    """Run all database migrations."""
    logger.info("=" * 60)
    logger.info("Starting Database Migrations")
    logger.info("=" * 60)
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # Check if invoice table exists
        inspector = inspect(engine)
        if 'invoice' not in inspector.get_table_names():
            logger.warning("Invoice table doesn't exist. Run init_db.py first.")
            return False
        
        # Run migrations
        migrate_invoice_table(engine)
        migrate_invoice_item_table(engine)
        
        logger.info("=" * 60)
        logger.info("Database Migrations Completed Successfully!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Migration Failed: {e}")
        logger.error("=" * 60)
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
