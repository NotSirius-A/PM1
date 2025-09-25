import json
import uasyncio as asyncio
from gc import collect as gc_collect
import socket
import select

import app
from communications import usb_

class WebServer:

    def __init__(self, socket: socket.socket, app_state: app.AppState, app_config: app.AppConfig, usb_controller: usb_.USBController) -> None:
        self.s = socket
        self.app_state = app_state
        self.app_config = app_config
        self.usb_controller = usb_controller

        self.poll_obj = select.poll()
        self.poll_obj.register(self.s, select.POLLIN)

    def respond_body_file(self, conn, file_path: str, mode: str="rb", buffer_size: int=1024) -> None:
        with open(file_path, mode) as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                conn.send(data)  

    def respond_file(self, conn, headers:tuple, file_path: str, *args, **kwargs):
        header_line = "HTTP/1.1 200 OK\r\n" + "\r\n".join(headers) + "\r\n\r\n"
        conn.send(header_line)
        self.respond_body_file(conn, file_path, *args, **kwargs)


    def serve_client(self, conn, addr) -> None:
        
        request = conn.recv(1024)
        request = str(request)

        try:
            url_str = request.split()[1]
        except IndexError:
            return

        url_path = url_str.split("?")[0]
        url_args: dict = {}

        try:
            url_args_str = url_str.split("?")[1]
            args = url_args_str.split("&")
            for arg in args:
                arg_split = arg.split("=")
                if len(arg_split) == 2:
                    url_args[arg_split[0]] = arg_split[1]

        except IndexError:
            pass

        if self.app_config.other_config["debug_enabled"]:
            print(f"Received http request from: {addr}, path: {url_path}, args: {url_args}")

        if url_path == "/api/measurements/list/" or url_path == "/api/measurements/list":
            response = "HTTP/1.1 200 OK\r\nContent-type: application/json\r\n\r\n"
            response +=  self.app_state.measurements_asjson()
            conn.send(response)

        elif url_path == "/api/state/list/" or url_path == "/api/state/list":
            response = "HTTP/1.1 200 OK\r\nContent-type: application/json\r\n\r\n"
            response += self.app_state.asjson()
            conn.send(response)

        elif url_path == "/api/command/" or url_path == "/api/command":

            msg = url_args.get("c")
            if msg:
                response = "HTTP/1.1 200 OK\r\nContent-type: text/plain\r\n\r\n"
                is_succesful, msg_response =  self.usb_controller.process_message(msg)
                response += json.dumps({"response:":msg_response})
            else:
                response = "HTTP/1.1 409 Conflict\r\nContent-type: text/plain\r\n\r\n"
            
            conn.send(response)

        elif url_path == "/console/" or url_path == "/console":
            headers = ("Content-type: text/html", "Cache-Control: max-age=3600")
            self.respond_file(conn, headers, "web/assets/command_console.html")

        elif url_path == "/scripts.js":
            headers = ("Content-type: text/javascript", "Cache-Control: max-age=31536000")  
            self.respond_file(conn, headers, "web/assets/scripts.js")

        elif url_path == "/styles.css":
            headers = ("Content-type: text/css", "Cache-Control: max-age=31536000")  
            self.respond_file(conn, headers, "web/assets/styles.css")

        elif url_path == "/favicon.ico":
            headers = ("Cache-Control: max-age=31536000",)  
            self.respond_file(conn, headers, "web/assets/favicon.ico")


        else:
            headers = ("Content-type: text/html", "Cache-Control: max-age=3600")
            self.respond_file(conn, headers, "web/assets/index.html")   


    def run(self, timeout_ms: int=3):
        
        poll_results = self.poll_obj.poll(timeout_ms) 
        if poll_results:

            try:
                conn, addr = self.s.accept()
                self.serve_client(conn, addr)

                conn.close()

            except OSError as e:

                if e.args[0] == 110:
                    #ETIMEDOUT
                    pass
                elif e.args[0] == 11:
                    #EAGAIN
                    pass
                else:
                    conn.close()
