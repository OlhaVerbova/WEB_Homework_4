import pathlib
import urllib.parse 
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import json
import logging
from threading import Thread
import socket
from datetime import datetime

BASE_DIR = pathlib.Path()
SERVER_IP = "192.168.50.66"
SERVER_PORT = 5000
BUFER = 1024

def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))      
    client_socket.close()


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
        self.send_response(302)        
        self.send_header("Location", "/index")
        self.end_headers()


    def do_GET(self):
        route = urllib.parse.urlparse(self.path) 
        match route.path:
            case "/": 
                self.send_html('index.html')
            case "/message":
                self.send_html(BASE_DIR /'message.html')            
            case "/index":
                self.send_html('index.html')
            case _:                
                file = BASE_DIR / route.path[1:]
                if file.exists(): 
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)               


    def send_html(self, filename, status_code = 200):   

        self.send_response(status_code) 

        
        self.send_header('Content-type','text/html') 
        self.end_headers()
        
        with open(filename, "rb") as f:              
            self.wfile.write(f.read())

    def send_static(self, filename):
         self.send_response(200)         
         mime_type, *rest = mimetypes.guess_type(filename)
         if mime_type:             
            self.send_header('Content-type',mime_type)
         else:
            self.send_header('Content-type','text/plain')
    

         self.end_headers()
         with open(filename, "rb") as f:
            self.wfile.write(f.read())

def run(server=HTTPServer, handler=HTTPHandler):
    address = ("", 3000) 
       
    http_server = server(address, handler)
    
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()

def save_data(data): 
    body = urllib.parse.unquote_plus(data.decode())    
    try:         
        payload = {key: value for key, value in [el.split("=")for el in body.split("&")]}              
        text_message = {str(datetime.now()) : payload}

        if not BASE_DIR.joinpath(BASE_DIR/'data/data.json').exists():
            with open(BASE_DIR.joinpath(BASE_DIR/'data/data.json'), 'w', encoding='utf-8') as new_file:
                new_file.write('[]')         
        with open(BASE_DIR.joinpath(BASE_DIR/'data/data.json'), 'r', encoding='utf-8') as existing_file:
            try:
                entries = json.load(existing_file)
            except json.JSONDecodeError:
                entries = []       
        entries.append(text_message)
        
        with open(BASE_DIR.joinpath(BASE_DIR/'data/data.json'), 'w', encoding='utf-8') as fd:
            fd.write(json.dumps(entries, ensure_ascii=False, indent=2))
            fd.write("\n")
            
    except ValueError as err:
        logging.error(f"Field parse data {body}:with error {err}")  
    except OSError as err:
        logging.error(f"Field write data {body}:with error {err}")  

def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)    
    try:
        while True:            
            data = server_socket.recv(BUFER)

            save_data(data)
    except KeyboardInterrupt:
        logging.info("Socket server stoped")
    finally:
        server_socket.close()

    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
  
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()

