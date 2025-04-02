import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_path="conversations.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 대화 세션 테이블 생성
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 메시지 테이블 생성
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_conversation(self, title):
        """새로운 대화 세션 생성"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO conversations (title) VALUES (?)', (title,))
        conversation_id = c.lastrowid
        conn.commit()
        conn.close()
        return conversation_id

    def save_message(self, conversation_id, role, content):
        """메시지 저장"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        ''', (conversation_id, role, content))
        
        # 대화 세션의 updated_at 업데이트
        c.execute('''
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (conversation_id,))
        
        conn.commit()
        conn.close()

    def get_conversations(self):
        """모든 대화 세션 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT id, title, created_at, updated_at 
            FROM conversations 
            ORDER BY updated_at DESC
        ''')
        conversations = c.fetchall()
        conn.close()
        return conversations

    def get_messages(self, conversation_id):
        """특정 대화 세션의 모든 메시지 조회"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT role, content 
            FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at
        ''', (conversation_id,))
        messages = c.fetchall()
        conn.close()
        return messages

    def delete_conversation(self, conversation_id):
        """대화 세션 삭제"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        c.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        conn.commit()
        conn.close() 