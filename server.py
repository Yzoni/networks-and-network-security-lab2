import mimetypes
import os
import re
import socket
import subprocess
import time


class HttpServer:
    def __init__(self, port=80, directory='public_html/'):
        self.host = ''
        self.port = port
        self.directory = directory

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(3)
            while True:
                s.listen(5)
                connection, addr = s.accept()
                with connection as c:
                    data = c.recv(1024)
                    string = bytes.decode(data)
                    request_method = string.split(' ')[0]
                    request_file = string.split(' ')[1]

                    if request_method != 'GET':
                        self.return_501(c)
                    else:
                        if re.match('/cgi-bin/.*', request_file):  # Dynamic
                            request_uri, query_string = self.split_request(request_file)
                            self.return_200_dynamic(c, request_uri, query_string, addr, request_method)
                        else:  # Static
                            if (request_file == '/'):
                                request_file = '/index.html'
                            file_path = self.directory + '/public_html' + request_file
                            if os.path.isfile(file_path):
                                self.return_200_static(c, file_path)
                            else:
                                self.return_404(c)

    def return_200_static(self, connection, file_path):
        # TODO cleanup this function
        if mimetypes.guess_type(file_path)[0] == 'text/html':
            with open(file_path, 'r') as f:
                response_status = self._get_status_line(200)
                response_headers = self._get_headers(file_path)
                response_content = f.read()
            response = str.encode(response_status) + str.encode(response_headers) + str.encode(response_content)
        else:
            with open(file_path, 'rb') as f:
                response_status = self._get_status_line(200)
                response_headers = self._get_headers(file_path)
                response_content = f.read()
            response = str.encode(response_status) + str.encode(response_headers) + response_content

        return connection.send(response)

    def return_200_dynamic(self, connection, request_uri, query_string, address, request_method):
        with subprocess.Popen(["python", self.directory + request_uri], stdout=subprocess.PIPE,
                              env=dict(os.environ,
                                       DOCUMENT_ROOT=self.directory + '/public_html',
                                       REQUEST_METHOD=request_method,
                                       REQUEST_URI=request_uri,
                                       QUERY_STRING=str(self.split_query_string(query_string)),
                                       REMOTE_ADDR=address[0])) as proc:
            response_status = self._get_status_line(200)
            response_headers = self._get_headers()
            response_content = proc.stdout.read()
            response = response_status + response_headers + response_content.decode()
        return connection.send(response.encode())

    def split_request(self, request):
        query_string = ''
        if '?' in request:
            request_uri, query_string = request.split('?', 1)
        else:
            request_uri = request
        return request_uri, query_string

    def split_query_string(self, query_string):
        try:
            splitted = query_string.split('&')
            return dict(map(str, x.split('=')) for x in splitted)
        except:
            print('Invalid query string')

    def return_501(self, connection):
        response_status = self._get_status_line(501)
        response_headers = self._get_headers()
        response_content = self._get_status_line(501)
        response = response_status + response_headers + response_content
        return connection.send(response.encode())

    def return_404(self, connection):
        response_status = self._get_status_line(404)
        response_headers = self._get_headers()
        response_content = self._get_status_line(404)
        response = response_status + response_headers + response_content
        return connection.send(response.encode())

    def _get_status_line(self, code):
        if code == 200:
            return 'HTTP/1.1 200 OK\n'
        elif code == 404:
            return 'HTTP/1.1 404 Not Found\n'
        elif code == 501:
            return 'HTTP/1.1 501 Not Implemented\n'

    def _get_headers(self, file_path=None):
        h = ''
        current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        h += 'Date: ' + current_date + '\n'
        h += 'Server: HTTP-Socket-Server\n'
        if file_path:
            mime = mimetypes.MimeTypes().guess_type(file_path)[0]
            h += 'Content-Type: ' + mime + '\n'
            h += 'Content-Length: ' + str(os.path.getsize(file_path)) + '\n'
        h += 'Connection: close\n\n'

        return h


if __name__ == '__main__':
    http_server = HttpServer(port=8081,
                             directory='/home/yorick/IdeaProjects/computer-networks-http-server')
    http_server.start()
