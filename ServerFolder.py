import os
import glob
import random
import pandas as pd
from ServerDatabase import *
from PyQt5.QtCore import *

# 이 쪽 부분이 뭔가 어색함;;;
class ServerFolder(QObject):
    files_selected = pyqtSignal(str ,list)
    
    def __init__(self, textvalue1):
        super().__init__()
        self.textmsg1 = textvalue1          
          
    def run(self):
        folder_path = 'd:\\lasthouse\\홍길동'           
        #folder_path = 'c:\\lasthouse\\홍길동'
        all_files = glob.glob(folder_path + '/*')
        df = pd.read_csv('System.csv')

        ip_display_map = {}
        for index, row in df.iterrows():
            ip = row['IP']
            display = row['Display Port']
            if ip not in ip_display_map:
                ip_display_map[ip] = []
            ip_display_map[ip].append(display)
        
        selected_files = []
        for ip, displays in ip_display_map.items():
            count = len(displays)
            if count > 0:
                num_elements_to_select = count
                available_files = [f for f in all_files if f not in selected_files]
                if len(available_files) < num_elements_to_select:
                     print(f"경고: {ip}의 선택할 파일 개수가 너무 많습니다.")
                     num_elements_to_select = len(available_files)
                random_selected = random.sample(available_files, num_elements_to_select)
                selected_files.extend(random_selected)
                self.files_selected.emit(ip, random_selected)  # Emit IP along with selected files
            else:
                print(f"{ip}에 대한 디스플레이 정보가 없습니다.")


# 서버 폴더 관리 메인 클래스
class ServerFolderThread(QThread):
    def __init__(self, textvalue):
        super().__init__()
        self.textmsg = textvalue
        # 6. 사용자 이름으로 검색하여 나온 리스트 폴더 관린 클래스 함수에 파싱
        self.serverfolderthread = ServerFolder(self.textmsg)
        self.serverfolderthread.files_selected.connect(self.slot_data)
        
    def run(self):
        self.serverfolderthread.run()
        
    def slot_data(self, ip ,sel):
        self.msg = (ip, sel)            # IP이름(폴더명) 과 파일 관리 폴더에 랜덤 파일을 방출
        
        """
        path = self.msg[1][0]
        folder_path = os.path.dirname(path)
        file_name = os.path.basename(path)
        
        self.qrsearchdatabase = ServerDatabaseThread('',folder_path, file_name)
        self.qrsearchdatabase.start()
        """
        

        
        
        

