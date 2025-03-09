"""
Database models and operations for the CRM system
"""

from typing import List, Dict, Optional, Any
import logging
from mysql.connector import Error
from datetime import datetime
import bcrypt
from .db_config import DatabaseConnection

class BaseModel:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def _execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """Execute a database query and return results if needed"""
        connection = self.db.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            connection.commit()
            return None
        except Error as e:
            connection.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

class User(BaseModel):
    def create_user(self, username: str, password: str, email: str, role_id: int, manager_id: Optional[int] = None) -> int:
        """Create a new user"""
        # Hash the password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        query = """
            INSERT INTO users (username, password_hash, email, role_id, manager_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (username, password_hash, email, role_id, manager_id)
        
        try:
            self._execute_query(query, params, fetch=False)
            # Get the last inserted id
            return self._execute_query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']
        except Error as e:
            logging.error(f"Error creating user: {e}")
            raise

    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        query = "SELECT password_hash FROM users WHERE username = %s"
        result = self._execute_query(query, (username,))
        
        if result:
            stored_hash = result[0]['password_hash'].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
        return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT u.*, r.role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.user_id = %s
        """
        result = self._execute_query(query, (user_id,))
        return result[0] if result else None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        query = """
            SELECT u.*, r.role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.username = %s
        """
        result = self._execute_query(query, (username,))
        return result[0] if result else None

class Contact(BaseModel):
    def create_contact(self, data: Dict[str, Any]) -> int:
        """Create a new contact"""
        query = """
            INSERT INTO contacts 
            (first_name, last_name, email, phone, company, assigned_to, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['first_name'],
            data['last_name'],
            data.get('email'),
            data.get('phone'),
            data.get('company'),
            data.get('assigned_to'),
            data.get('notes')
        )
        
        self._execute_query(query, params, fetch=False)
        return self._execute_query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']

    def get_contact(self, contact_id: int) -> Optional[Dict]:
        """Get contact by ID"""
        query = "SELECT * FROM contacts WHERE contact_id = %s"
        result = self._execute_query(query, (contact_id,))
        return result[0] if result else None

    def get_contacts_by_user(self, user_id: int) -> List[Dict]:
        """Get all contacts assigned to a user"""
        query = "SELECT * FROM contacts WHERE assigned_to = %s"
        return self._execute_query(query, (user_id,))

    def update_contact(self, contact_id: int, data: Dict[str, Any]) -> bool:
        """Update contact information"""
        query = """
            UPDATE contacts 
            SET first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                company = %s,
                assigned_to = %s,
                notes = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE contact_id = %s
        """
        params = (
            data['first_name'],
            data['last_name'],
            data.get('email'),
            data.get('phone'),
            data.get('company'),
            data.get('assigned_to'),
            data.get('notes'),
            contact_id
        )
        
        self._execute_query(query, params, fetch=False)
        return True

class Task(BaseModel):
    def create_task(self, data: Dict[str, Any]) -> int:
        """Create a new task"""
        query = """
            INSERT INTO tasks 
            (title, description, assigned_to, assigned_by, due_date, status_id, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['title'],
            data.get('description'),
            data['assigned_to'],
            data['assigned_by'],
            data['due_date'],
            data['status_id'],
            data.get('priority', 'medium')
        )
        
        self._execute_query(query, params, fetch=False)
        return self._execute_query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']

    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get task by ID"""
        query = """
            SELECT t.*, ts.status_name, 
                   CONCAT(u1.first_name, ' ', u1.last_name) as assigned_to_name,
                   CONCAT(u2.first_name, ' ', u2.last_name) as assigned_by_name
            FROM tasks t
            JOIN task_status ts ON t.status_id = ts.status_id
            JOIN users u1 ON t.assigned_to = u1.user_id
            JOIN users u2 ON t.assigned_by = u2.user_id
            WHERE t.task_id = %s
        """
        result = self._execute_query(query, (task_id,))
        return result[0] if result else None

    def get_tasks_by_user(self, user_id: int, as_manager: bool = False) -> List[Dict]:
        """Get tasks for a user"""
        if as_manager:
            query = """
                SELECT t.*, ts.status_name,
                       CONCAT(u1.first_name, ' ', u1.last_name) as assigned_to_name
                FROM tasks t
                JOIN task_status ts ON t.status_id = ts.status_id
                JOIN users u1 ON t.assigned_to = u1.user_id
                WHERE t.assigned_by = %s
                ORDER BY t.due_date ASC
            """
        else:
            query = """
                SELECT t.*, ts.status_name,
                       CONCAT(u.first_name, ' ', u.last_name) as assigned_by_name
                FROM tasks t
                JOIN task_status ts ON t.status_id = ts.status_id
                JOIN users u ON t.assigned_by = u.user_id
                WHERE t.assigned_to = %s
                ORDER BY t.due_date ASC
            """
        return self._execute_query(query, (user_id,))

    def update_task_status(self, task_id: int, status_id: int) -> bool:
        """Update task status"""
        query = """
            UPDATE tasks 
            SET status_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE task_id = %s
        """
        self._execute_query(query, (status_id, task_id), fetch=False)
        return True

class ReferenceData(BaseModel):
    def get_roles(self) -> List[Dict]:
        """Get all roles"""
        return self._execute_query("SELECT * FROM roles")

    def get_task_statuses(self) -> List[Dict]:
        """Get all task statuses"""
        return self._execute_query("SELECT * FROM task_status")

    def create_role(self, role_name: str, description: str) -> int:
        """Create a new role (Admin only)"""
        query = "INSERT INTO roles (role_name, description) VALUES (%s, %s)"
        self._execute_query(query, (role_name, description), fetch=False)
        return self._execute_query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']

    def create_task_status(self, status_name: str, description: str) -> int:
        """Create a new task status (Admin only)"""
        query = "INSERT INTO task_status (status_name, description) VALUES (%s, %s)"
        self._execute_query(query, (status_name, description), fetch=False)
        return self._execute_query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']
