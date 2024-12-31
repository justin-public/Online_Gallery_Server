import os
import sqlite3
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from PyQt5.QtCore import *
from main import *

FTP_HOST = '121.140.54.39'
#FTP_HOST = '192.168.0.114'
FTP_PORT = 1000
FTP_ADMIN_DIR = os.path.join(os.getcwd(), 'anonymous')
#FTP_USERS_DIR = os.path.join(os.getcwd(), 'anonymous/users')
FTP_ANONY_DIR = os.path.join(os.getcwd(),'anonymous/lasthouse')    
#FTP_ANONY_DIR = os.path.join(os.getcwd(),'anonymous') 

class ServerFTPThread(QThread):
    def __init__(self):
        super().__init__()
        
    def run(self):
        #FTP_ANONY_DIR = os.path.join(os.getcwd(),'anonymous/lasthouse')    
        #FTP_ANONY_DIR = os.path.join(os.getcwd(),'anonymous/users')
        authorizer = DummyAuthorizer()
        authorizer.add_user('admin', 'admin1234', FTP_ADMIN_DIR, perm='elradfmwMT')
        #authorizer.add_user('dochi', 'dochi1234', FTP_USERS_DIR, perm='elr')
        
        #for folder in os.listdir(FTP_ANONY_DIR):
            #folder_path = os.path.join(FTP_ANONY_DIR, folder)
            #if os.path.isdir(folder_path):
                #authorizer.add_anonymous(folder_path)
        
        if not hasattr(self, 'anonymous_added') or not self.anonymous_added:
            authorizer.add_anonymous(FTP_ANONY_DIR)
            self.anonymous_added = True
        
        handler = FTPHandler
        handler.banner = "Epicgram FTP Server."
        handler.authorizer = authorizer
        handler.passive_ports = range(60000, 65535)
        address = (FTP_HOST, FTP_PORT)
        server = FTPServer(address, handler)
        server.max_cons = 256
        server.max_cons_per_ip = 5
        server.serve_forever()