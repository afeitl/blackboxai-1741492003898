"""
Database configuration and connection management for the CRM system
"""

import mysql.connector
from mysql.connector import Error
import logging
from typing import Optional
from ...config import DB_CONFIG

class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance
    
    def connect(self) -> None:
        """Establish connection to the MySQL database"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**DB_CONFIG)
                logging.info("Database connection established successfully")
        except Error as e:
            logging.error(f"Error connecting to MySQL database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close the database connection"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logging.info("Database connection closed successfully")
        except Error as e:
            logging.error(f"Error closing database connection: {e}")
            raise
    
    def get_connection(self):
        """Get the current database connection"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection

def init_database():
    """Initialize the database schema"""
    db = DatabaseConnection()
    connection = db.get_connection()
    cursor = connection.cursor()
    
    try:
        # Create core tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id INT PRIMARY KEY AUTO_INCREMENT,
                role_name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                role_id INT,
                manager_id INT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(role_id),
                FOREIGN KEY (manager_id) REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                contact_id INT PRIMARY KEY AUTO_INCREMENT,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                company VARCHAR(100),
                assigned_to INT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_to) REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_status (
                status_id INT PRIMARY KEY AUTO_INCREMENT,
                status_name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INT PRIMARY KEY AUTO_INCREMENT,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                assigned_to INT,
                assigned_by INT,
                due_date DATE,
                status_id INT,
                priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_to) REFERENCES users(user_id),
                FOREIGN KEY (assigned_by) REFERENCES users(user_id),
                FOREIGN KEY (status_id) REFERENCES task_status(status_id)
            )
        """)
        
        # Insert default roles
        cursor.execute("""
            INSERT IGNORE INTO roles (role_name, description)
            VALUES 
                ('admin', 'System administrator with full access'),
                ('manager', 'Team manager with reporting and task assignment capabilities'),
                ('employee', 'Regular employee with basic access')
        """)
        
        # Insert default task statuses
        cursor.execute("""
            INSERT IGNORE INTO task_status (status_name, description)
            VALUES 
                ('not_started', 'Task has not been started'),
                ('in_progress', 'Task is currently being worked on'),
                ('completed', 'Task has been completed'),
                ('on_hold', 'Task is temporarily on hold')
        """)
        
        connection.commit()
        logging.info("Database schema initialized successfully")
        
    except Error as e:
        connection.rollback()
        logging.error(f"Error initializing database schema: {e}")
        raise
    finally:
        cursor.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
