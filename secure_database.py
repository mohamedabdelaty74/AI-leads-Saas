import sqlite3
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from cryptography.fernet import Fernet
from contextlib import contextmanager
import logging

class SecureDatabase:
    """Secure database operations with encryption and SQL injection protection"""

    def __init__(self, db_path: str, encryption_key: Optional[str] = None):
        self.db_path = db_path
        self.encryption_key = encryption_key
        self._cipher = None

        if encryption_key:
            self._cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def get_connection(self):
        """Secure database connection context manager"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            # Set secure temp store
            conn.execute("PRAGMA temp_store = memory")

            yield conn

        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def encrypt_field(self, data: str) -> str:
        """Encrypt sensitive field data"""
        if not self._cipher or not data:
            return data
        return self._cipher.encrypt(data.encode()).decode()

    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data"""
        if not self._cipher or not encrypted_data:
            return encrypted_data
        try:
            return self._cipher.decrypt(encrypted_data.encode()).decode()
        except:
            return encrypted_data  # Return as-is if decryption fails

    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False,
                     fetch_all: bool = False, commit: bool = True) -> Optional[Union[List, tuple]]:
        """Execute parameterized query safely"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if commit:
                conn.commit()

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()

            return cursor.rowcount

    def create_secure_tables(self):
        """Create tables with proper security constraints"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Organizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    website TEXT,
                    description TEXT,
                    encrypted_data TEXT,  -- For sensitive information
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Users table (secure version)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secure_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    email_encrypted TEXT,  -- Encrypted email credentials
                    phone_encrypted TEXT,  -- Encrypted phone
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP NULL,
                    last_login TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'readonly'))
                )
            ''')

            # Lead collections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lead_collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    source TEXT NOT NULL,  -- google, linkedin, instagram
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES secure_users (id),
                    CONSTRAINT valid_source CHECK (source IN ('google', 'linkedin', 'instagram', 'manual')),
                    CONSTRAINT valid_status CHECK (status IN ('active', 'archived', 'deleted'))
                )
            ''')

            # Leads table with encryption for sensitive data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id INTEGER NOT NULL,
                    organization_name TEXT NOT NULL,
                    contact_name TEXT,
                    email_encrypted TEXT,  -- Encrypted email
                    phone_encrypted TEXT,  -- Encrypted phone
                    website TEXT,
                    description TEXT,
                    source_url TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    verification_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (collection_id) REFERENCES lead_collections (id),
                    CONSTRAINT valid_verification CHECK (verification_status IN ('pending', 'verified', 'invalid', 'bounced'))
                )
            ''')

            # Audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    table_name TEXT,
                    record_id INTEGER,
                    old_values TEXT,  -- JSON
                    new_values TEXT,  -- JSON
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES secure_users (id)
                )
            ''')

            # Email campaigns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    template TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    sent_count INTEGER DEFAULT 0,
                    opened_count INTEGER DEFAULT 0,
                    clicked_count INTEGER DEFAULT 0,
                    bounced_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES secure_users (id),
                    CONSTRAINT valid_status CHECK (status IN ('draft', 'scheduled', 'sending', 'sent', 'paused', 'cancelled'))
                )
            ''')

            conn.commit()
            self.logger.info("Secure database tables created successfully")

    def log_action(self, user_id: int, action: str, table_name: str = None,
                  record_id: int = None, old_values: Dict = None,
                  new_values: Dict = None, ip_address: str = None,
                  user_agent: str = None):
        """Log user actions for audit trail"""
        try:
            self.execute_query('''
                INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, action, table_name, record_id,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                ip_address, user_agent
            ))
        except Exception as e:
            self.logger.error(f"Failed to log action: {e}")

    def add_lead_secure(self, collection_id: int, organization_name: str,
                       contact_name: str = None, email: str = None,
                       phone: str = None, website: str = None,
                       description: str = None, source_url: str = None,
                       user_id: int = None) -> int:
        """Add lead with encrypted sensitive data"""

        # Encrypt sensitive fields
        email_encrypted = self.encrypt_field(email) if email else None
        phone_encrypted = self.encrypt_field(phone) if phone else None

        lead_id = self.execute_query('''
            INSERT INTO leads (collection_id, organization_name, contact_name,
                             email_encrypted, phone_encrypted, website,
                             description, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (collection_id, organization_name, contact_name,
              email_encrypted, phone_encrypted, website,
              description, source_url))

        # Log the action
        if user_id:
            self.log_action(user_id, 'CREATE_LEAD', 'leads', lead_id, None, {
                'organization_name': organization_name,
                'collection_id': collection_id
            })

        return lead_id

    def get_leads_secure(self, collection_id: int, limit: int = 100,
                        offset: int = 0) -> List[Dict]:
        """Get leads with decrypted sensitive data"""
        leads = self.execute_query('''
            SELECT id, collection_id, organization_name, contact_name,
                   email_encrypted, phone_encrypted, website, description,
                   source_url, confidence_score, verification_status,
                   created_at, updated_at
            FROM leads
            WHERE collection_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (collection_id, limit, offset), fetch_all=True)

        result = []
        for lead in leads:
            lead_dict = {
                'id': lead[0],
                'collection_id': lead[1],
                'organization_name': lead[2],
                'contact_name': lead[3],
                'email': self.decrypt_field(lead[4]) if lead[4] else None,
                'phone': self.decrypt_field(lead[5]) if lead[5] else None,
                'website': lead[6],
                'description': lead[7],
                'source_url': lead[8],
                'confidence_score': lead[9],
                'verification_status': lead[10],
                'created_at': lead[11],
                'updated_at': lead[12]
            }
            result.append(lead_dict)

        return result

    def update_user_credentials(self, user_id: int, email_credentials: str = None,
                               phone: str = None) -> bool:
        """Update user credentials with encryption"""
        try:
            email_encrypted = self.encrypt_field(email_credentials) if email_credentials else None
            phone_encrypted = self.encrypt_field(phone) if phone else None

            self.execute_query('''
                UPDATE secure_users
                SET email_encrypted = COALESCE(?, email_encrypted),
                    phone_encrypted = COALESCE(?, phone_encrypted)
                WHERE id = ?
            ''', (email_encrypted, phone_encrypted, user_id))

            self.log_action(user_id, 'UPDATE_CREDENTIALS', 'secure_users', user_id)
            return True

        except Exception as e:
            self.logger.error(f"Failed to update user credentials: {e}")
            return False

    def cleanup_old_data(self, days: int = 30):
        """Clean up old audit logs and expired sessions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Clean old audit logs
                cursor.execute('''
                    DELETE FROM audit_log
                    WHERE created_at < datetime('now', '-{} days')
                '''.format(days))

                # Clean expired sessions
                cursor.execute('''
                    DELETE FROM user_sessions
                    WHERE expires_at < datetime('now')
                ''')

                conn.commit()
                self.logger.info(f"Cleaned up old data (>{days} days)")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}

        tables = ['secure_users', 'lead_collections', 'leads', 'audit_log']

        for table in tables:
            try:
                result = self.execute_query(f'SELECT COUNT(*) FROM {table}', fetch_one=True)
                stats[table] = result[0] if result else 0
            except:
                stats[table] = 0

        return stats

# Initialize secure database
def init_secure_database(db_path: str = "elite_creatif_secure.db",
                        encryption_key: str = None) -> SecureDatabase:
    """Initialize secure database"""
    secure_db = SecureDatabase(db_path, encryption_key)
    secure_db.create_secure_tables()
    return secure_db