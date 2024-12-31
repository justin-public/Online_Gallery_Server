import sqlite3
import pandas as pd
import random
from PyQt5.QtCore import *

class CommentDatabase(QObject):
    def __init__(self):
        super().__init__()
    
    def run(self):
        conn = sqlite3.connect('Comment.db')
        c = conn.cursor()
        c.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='Comment'
            """)
        if not c.fetchone():
            c.execute('''CREATE TABLE Comment
                     (Contents_ID text , Comment_ID text, 일시 text, 작성자 text, Comment_word text)''')
            conn.commit()
        conn.close()
    
    def _add_customer(self,Contents_ID,Comment_ID,일시,작성자,Comment_word):
        conn = sqlite3.connect('Comment.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO Comment VALUES (?, ?, ?, ?, ?)", (Contents_ID, Comment_ID, 일시, 작성자, Comment_word))
        conn.commit()

    def _updateDatabse(self,Contents_ID,Comment_ID,일시,작성자,Comment_word):
        conn = sqlite3.connect('Comment.db')
        c = conn.cursor()
        c.execute("UPDATE Comment SET Contents_ID = ?, Comment_ID = ?, 일시 = ?, 작성자 = ?, Comment_word = ?", (Contents_ID, Comment_ID, 일시, 작성자, Comment_word))
        conn.commit()
        conn.close()
    
    def _search_customer(self, Comment_ID):
        conn = sqlite3.connect('Comment.db')
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM Comment WHERE Comment_ID=?", (Comment_ID,))
            Contextvalue = c.fetchall()
        except sqlite3.Error as e:
            Contextvalue = None
        finally:
            conn.close()
        return Contextvalue
    
    def get_most_recent_date(self):
        conn = sqlite3.connect('Comment.db')
        c = conn.cursor()
        try:
            c.execute("SELECT MAX(일시) FROM Comment")
            recent_date = c.fetchone()[0]
        except sqlite3.Error as e:
            recent_date = None
        finally:
            conn.close()
        return recent_date
        
"""
class CommentDatabasethread(QThread):
    def __init__(self, textvalue):
        super().__init__()
        self.contextvalue = textvalue
        self.CommentDatabasethread = CommentDatabase()
    
    def run(self):
        self.CommentDatabasethread.run()
        Comment_Sys_packet = self.contextvalue
        print(Comment_Sys_packet)
        Comment_Sys_packet_key = str(Comment_Sys_packet).split(",")
        Contents_ID = Comment_Sys_packet_key[0]
        Comment_ID = Comment_Sys_packet_key[1]
        일시 = Comment_Sys_packet_key[2]
        작성자 = Comment_Sys_packet_key[3]
        Comment_value = Comment_Sys_packet_key[4]
        
        self.CommentDatabasethread._add_customer(Contents_ID, Comment_ID, 일시, 작성자, Comment_value)
        self.CommentDatabasethread_value = self.CommentDatabasethread._search_customer(Comment_ID)

        if Comment_ID and len(self.CommentDatabasethread_value) > 0:
            Contents_ID = self.CommentDatabasethread_value[0][0]
            Comment_ID = self.CommentDatabasethread_value[0][1]
            일시 = self.CommentDatabasethread_value[0][2]
            작성자 = self.CommentDatabasethread_value[0][3]
            Comment_word = self.CommentDatabasethread_value[0][4]
            print(Contents_ID + "," + Comment_ID + "," + 일시 + "," + 작성자 + "," + Comment_word)
"""
        
# Database 생성
class ServerDatabase(QObject):
    files_database = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        csv_file_path = 'data.csv'
        db_file_path = 'database.db'
        table_name = 'data_table'

        data = pd.read_csv(csv_file_path)
        conn = sqlite3.connect(db_file_path)
        data.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
    
# Database 검색
class ServerDatabaseSearch(QObject):
    files_database_search = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()

    # 4. 사용자 이름과 결합된 디렉토리를 통하여 데이터 베이스 검색 
    def _search_customer(self,target_directory):
        db_file_path = 'database.db'
        table_name = 'data_table'
        target_directory = target_directory
        conn = sqlite3.connect(db_file_path)

        query = f"SELECT * FROM {table_name} WHERE `Contents directory` = ?"
        data = pd.read_sql_query(query, conn, params=(target_directory,))
        data_list = data.values.tolist()
        self.files_database_search.emit(data_list)                                  # 해당 사용자 폴더 디렉토리가 있는 항목만 리스트로 생성후 방출
        conn.close()

# QR 데이터 베이스 검색 / 선택된 파일에 관련되어서만 추출
class QRDatabaseSearch(QObject):
    QR_database_search = pyqtSignal(list)
    def __init__(self):
        super().__init__()
    
    """
    def _search_customer(self,target_directory):
        db_file_path = 'database.db'
        table_name = 'data_table'
        target_directory = target_directory
        conn = sqlite3.connect(db_file_path)

        query = f"SELECT * FROM {table_name} WHERE `Contents directory` = ?"
        #query = f"SELECT * FROM {table_name} WHERE `File name` = ?"
        data = pd.read_sql_query(query, conn, params=(target_directory,))
        data_list = data.values.tolist()
        print(data_list)
        #self.files_database_search.emit(data_list)                                  # 해당 사용자 폴더 디렉토리가 있는 항목만 리스트로 생성후 방출
        conn.close()
    """

    def _search_customer(self, target_directory, target_date):
        db_file_path = 'database.db'
        table_name = 'data_table'
        conn = sqlite3.connect(db_file_path)
        query = f"SELECT * FROM {table_name} WHERE `Contents directory` = ? AND `File name` = ?"
        data = pd.read_sql_query(query, conn, params=(target_directory, target_date))
        data_list = data.values.tolist()
        conn.close()
        return data_list
        #conn.close()

# 서버 데이터 베이스 메인 클래스
class ServerDatabaseThread(QThread):
    QR_list = pyqtSignal(list)
    
    def __init__(self, Username):
        super().__init__()
        self.username = Username
        self.ready = False                  
        self.serverdatabasethread = ServerDatabase()                                # 데이터 베이스 생성  
        self.serverdatabasesearch = ServerDatabaseSearch()                          # 데이터 베이스 검색     
        self.qrdatabasesearch = QRDatabaseSearch()                                  # QR 데이터 검색
        self.commentdatabasesearch = CommentDatabase()
        
        self.serverdatabasesearch.files_database_search.connect(self.slot_data)     # 검색된 리스트 메인 클래스 연결
        
    def run(self):
        self.serverdatabasethread.run()
        # 3. 사용자 이름과 폴더 디렉토리를 결합 하여 데이터 베이스 검색
        #self.serverdatabasesearch._search_customer(f'c:\\lasthouse\\{self.username}')
        self.serverdatabasesearch._search_customer(f'd:\\lasthouse\\{self.username}') 
        #self.qrdatabasesearch._search_customer(self.filedir, self.filename)
        self.ready = True
    
    def slot_data(self, sel):
        self.msg = sel
    
    def is_ready(self):
        return self.ready
    
    
    """    
    def QR_slot_data(self, sel):
        self.msg = sel
        #print(self.msg)
        self.QR_list.emit(self.msg)
    """
    
    