import sys
import shutil
import os
import csv
import threading
import socket
import json
import ast
import itertools
from time import time, ctime, sleep
import _thread
from PyQt5 import uic
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from ServerFTP import *
from ServerFolder import *
from ServerDatabase import *

Server_Gui = uic.loadUiType('PAGE/Guiserver.ui')[0]

# 서버 GUI 클래스
class ServerGUI(QWidget,QThread,Server_Gui):
    def __init__(self,parent=None):
        super(ServerGUI,self).__init__(parent)
        self.all_flattened_lists = []
        self.comment_flattened_lists = []
        self.initUI()                                                               # 서버 UI 레이아웃 호출
        self.thread = None                                                          # 쓰레드 활성화 관련 변수
        self.worker = None                                                          # 쓰레드 동작 관련 변수
        self.show()                                                                 # GUI 출력

    def initUI(self):
        self.setupUi(self)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 1. TCP/IP 서버 쓰레드 시작 (동작)
        self.server_socket_thread = ServerThread()
        self.server_socket_thread.start()

        self.server_socket_thread.comment_message.connect(self._Comment_database)

        # 2. 사용자 이름으로 데이터 베이스 검색
        self.Username = "홍길동"
        self.serverdatabase = ServerDatabaseThread(self.Username)                           # 사용자 이름 파싱
        # 5. 사용자 이름 폴더명으로 검색 되어진 리스트 들만 폴더 관리 클래스에 연결 
        self.serverdatabase.serverdatabasesearch.files_database_search.connect(self.Contentsdatabase_file)
        #self.serverdatabase.QR_list.connect(self.QRcode_file)

        
        
        self.server_thread = ServerFTPThread()
        
        self.DataGalleryctbt.clicked.connect(self.send_packet_to_ftp_start)                       # 서버 FTP 동작 시작 버튼
        self.Stopbt.clicked.connect(self.send_packet_to_ftp_stop)                                 # 서버 FTP 삭제 버튼

    
    def _Comment_database(self, sel):
        if sel == '':
            print("empyt data")
        else:
            Comment_Sys_packet_key = str(sel).split(",")
            Contents_ID = Comment_Sys_packet_key[0]
            Comment_ID = Comment_Sys_packet_key[1]
            일시 = Comment_Sys_packet_key[2]
            작성자 = Comment_Sys_packet_key[3]
            Comment_value = Comment_Sys_packet_key[4]

            self.recent_date = self.serverdatabase.commentdatabasesearch.get_most_recent_date()
            print("recent: " + self.recent_date)
            
            self.serverdatabase.commentdatabasesearch._add_customer(Contents_ID, Comment_ID, 일시, 작성자, Comment_value)
            self.CommentDatabasethread_value = self.serverdatabase.commentdatabasesearch._search_customer(Comment_ID)
            self.comment_flattened_lists.extend(self.CommentDatabasethread_value)    
            
    # 폴더 관리 클래스 연결 함수
    def Contentsdatabase_file(self,sel):
        self.serverfolder = ServerFolderThread(sel)                                               # 서버 폴러 쓰레드 클래스 호출
        # 7. FTP 폴더에 분배될 파일 폴더 이동
        self.serverfolder.serverfolderthread.files_selected.connect(self.display_selected_files)  # FTP 폴더 분배 연결
        self.serverfolder.start()                                                                 # 서버 폴더 쓰레드 시작
    
    def send_packet_to_ftp_start(self):
        self.serverdatabase.start()
        self.server_thread.start()
        message = "FTP,open"
        #print(f"Values of self.test: {self.all_flattened_lists}")
        #self.all_flattened_lists.clear()
        
        if not self.all_flattened_lists:
            print("데이터가 준비되지 않았습니다. 버튼을 다시 눌러주세요.")
            return
        #print(self.all_flattened_lists)
        self.server_socket_thread.csv_packet_list_send(self.all_flattened_lists, self.comment_flattened_lists)
        self.all_flattened_lists.clear()
    
    def send_packet_to_ftp_stop(self):
        csv_file = 'System.csv'
        df = pd.read_csv(csv_file)
        
        unique_ips = df['IP'].unique()
        for ip_address in unique_ips:
            folder_name = ip_address.replace('.', '-')
            destination_folder = r'D:\work\Servermain\anonymous\lasthouse\{}'.format(folder_name)
            try:
                shutil.rmtree(destination_folder)
                print(f"{folder_name} 폴더가 삭제되었습니다.")
            except Exception as e:
                print(f"파일 삭제중 오류 발생: {e}")
        message = "FTP,close"
        self.server_socket_thread.send_message_to_client(message)
    
    # 폴더 관리에서 나온 데이터를 이용하여 FTP 폴더에 파일 분배
    # System.csv 파일에 IP(폴더이름) / 서버 폴더\\파일명
    def display_selected_files(self, files, files1):
        path = files1[0]
        folder_path = os.path.dirname(path)
        file_name = os.path.basename(path)
        
        self.test = self.serverdatabase.qrdatabasesearch._search_customer(folder_path, file_name)
        self.all_flattened_lists.extend(self.test)
        #print(self.all_flattened_lists)
        
        #self.all_flattened_lists = [item for item in new_data if item not in self.all_flattened_lists]
        #print("Current all_flattened_lists:", self.all_flattened_lists)
        
        self.cmdmsg = str(files) + '/' + str(files1)                                # IP 이름(폴더명) 과 서버 폴더에 파일 항목을 하나의 문자열로 만듬
        self.cmdmsgvalue = self.cmdmsg.split('/')                                   # IP 이름(폴더명) 과 서버 폴더에 파일 항목을 분리
        file_path_list = ast.literal_eval(self.cmdmsgvalue[1])                      # 전송된 서버 폴더 목록들을 하나의 리스트로 다시 만들어줌
        csv_file = 'System.csv'                                                      
        df = pd.read_csv(csv_file)                                                  # pandas 를 이용하여 csv 파일을 로드

        for index, row in df.iterrows():                                            # iterrows 를 이용하여 csv 파일에 각 행을 반복문 실행
            if row['IP'] == self.cmdmsgvalue[0]:                                    # 각 행의 IP 값과 전송된 IP이름을 매칭(비교)
                folder_name = row['IP'].replace('.', '-')                           # IP 에 . 을 _ 로 변환
                
                # abspath 를 통해 해당 절대 경로 설정되어 있는 폴더안에 IP이름에 폴더 생성을 위한 절대 경로 위치 지정
                destination_folder = os.path.abspath(os.path.join(r'D:\work\Servermain\anonymous\lasthouse', folder_name))
                # 절대 경로에 원하는 폴더 이름이 없을 경우 , 폴더 생성
                if not os.path.exists(destination_folder):
                    os.makedirs(destination_folder)
                    #print(f"폴더 생성: {destination_folder}")
                for file_path in file_path_list:                                    # 서버 폴더 파일 리스트에서 각 행을 반복문 실행
                    file_name = os.path.basename(file_path)                         # basename(상위 경로를 제외한 파일명만 반환) 을 이용하여 해당 행에 파일명만 추출
                    try:
                        shutil.copy(file_path, os.path.join(destination_folder, file_name))     # shutil 를 이용하여 파일을 절대 경로로 복사 이동
                        #print(f"파일 이동/복사: {file_name} -> {destination_folder}")
                    except Exception as e:
                        print(f"파일 이동/복사 중 오류 발생: {e}")

class ServerThread(QThread):
    comment_message = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clients = []                                                           # 클라이언트 리스트 배열
        self.running = True
        PORT = 6060                                                                 # 서버 포트 번호
        SERVER = socket.gethostbyname(socket.gethostname())                         # 서버 IP 주소
        ADDR = (SERVER, PORT)                                                       # 서버 주소와 포트번호 저장 변수
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      # 서버 소켓 드라이브 초기화
        self.server_socket.bind(ADDR)                                               # 서버 바인딩
        self.server_socket.listen()                                                 # 서버 리스트
    
    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()                       # 클라이언트 서버 접근
            self.clients.append(client_socket)
            client_socket.sendall('FTP,close'.encode('utf-8'))                      # 클라이언트에 초기화면 명령어 송신
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()
    
    def handle_client(self, client_socket, addr):
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                self.comment_message.emit(message)
                if not message:
                    break
            except Exception as e:
                break
        client_socket.close() 
        self.clients.remove(client_socket)

    
    #  현재는 로컬 시스템 이기 때문에 system.csv 정보를 모두 던져도 됨
    #  CSV 파일 정보를 클라이언트에 전송하기 위한 함수
    """
    def csv_packet_list_send(self, sel, sel1):
        print("SEL 리스트:", sel)
        print("COMMENT 리스트:", sel1)

        # CSV 파일 읽기
        csv_data = []
        with open('System.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print("CSV 컬럼 이름:", reader.fieldnames)
            for row in reader:
                csv_data.append(row)
    
        # sel 리스트 데이터
        sel_data = []
        for item in sel:
            sel_data.append({
                'ID': item[0],      # sel 리스트의 첫 번째 요소
                'path': item[1],    # sel 리스트의 두 번째 요소
                'image': item[2],   # sel 리스트의 세 번째 요소
                'qr_code': item[3]  # sel 리스트의 네 번째 요소
            })
    
        # sel1 리스트 데이터를 sel_data에 추가
        for item in sel1:
            sel_data.append({
                'Contents': item[0],
                'Comment': item[1],
                'date': item[2],
                'Username': item[3],
                'Commentvalue': item[4],
            })
    
        # JSON 파일 생성
        with open('csv_data.json', 'w') as jsonfile:
            json.dump(csv_data, jsonfile, indent=4)
    
        with open('sel_data.json', 'w') as jsonfile:
            json.dump(sel_data, jsonfile, indent=4)

        # JSON 파일 읽기 및 클라이언트에 전송
        for client_socket in self.clients:
            try:
                # CSV와 sel 데이터를 모두 전송하려면 각 파일의 내용을 읽어서 전송할 수 있습니다
                with open('csv_data.json', 'r') as jsonfile:
                    csv_json_data = json.load(jsonfile)
                with open('sel_data.json', 'r') as jsonfile:
                    sel_json_data = json.load(jsonfile)
        
                # 두 JSON 데이터를 합쳐서 전송합니다
                combined_json_data = {
                    'csv_data': csv_json_data,
                    'sel_data': sel_json_data,
                }
                client_socket.sendto(json.dumps(combined_json_data).encode('utf-8'), ('121.140.54.39', 6060))
            except Exception as e:
                print(f"클라이언트 전송 실패: {e}")
    """
    #"""
    def csv_packet_list_send(self, sel, sel1):
        print("SEL 리스트:", sel)
        print("COMMENT 리스트:", sel1)
        # CSV 파일 읽기
        csv_data = []
        with open('System.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print("CSV 컬럼 이름:", reader.fieldnames)
            for row in reader:
                csv_data.append(row)
    
        # sel 리스트 데이터
        sel_data = []
        for item in sel:
            sel_data.append({
                'ID': item[0],      # sel 리스트의 첫 번째 요소
                'path': item[1],    # sel 리스트의 두 번째 요소
                'image': item[2],   # sel 리스트의 세 번째 요소
                'qr_code': item[3]  # sel 리스트의 네 번째 요소
            })
        
        se1_data1 = []
        for item in sel1:
            se1_data1.append({
                'Contents': item[0],
                'Comment': item[1],
                'date': item[2],
                'Username': item[3],
                'Commentvalue': item[4],
            })
    
        # JSON 파일 생성
        with open('csv_data.json', 'w') as jsonfile:
            json.dump(csv_data, jsonfile, indent=4)
    
        with open('sel_data.json', 'w') as jsonfile:
            json.dump(sel_data, jsonfile, indent=4)
        
        with open('sel_data1.json','w') as jsonfile:
            json.dump(se1_data1, jsonfile, indent=4)

        # JSON 파일 읽기 및 클라이언트에 전송
        for client_socket in self.clients:
            try:
                # CSV와 sel 데이터를 모두 전송하려면 각 파일의 내용을 읽어서 전송할 수 있습니다
                with open('csv_data.json', 'r') as jsonfile:
                    csv_json_data = json.load(jsonfile)
                with open('sel_data.json', 'r') as jsonfile:
                    sel_json_data = json.load(jsonfile)
                with open('sel_data1.json','r') as jsonfile:
                    sel_json_data1 = json.load(jsonfile)
            
                # 두 JSON 데이터를 합쳐서 전송합니다
                combined_json_data = {
                    'csv_data': csv_json_data,
                    'sel_data': sel_json_data,
                    'sel_data1': sel_json_data1,
                }
                client_socket.sendto(json.dumps(combined_json_data).encode('utf-8'), ('121.140.54.39', 6060))
            except Exception as e:
                print(f"클라이언트 전송 실패: {e}")
    #"""
    
    def send_message_to_client(self, message):
        for client_socket in self.clients:  # Send message to all clients
            if client_socket:
                client_socket.sendall(message.encode('utf-8'))
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ServerGUI()
    ex.show()
    sys.exit(app.exec_())