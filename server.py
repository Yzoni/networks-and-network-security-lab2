import mimetypes
import os
import re
import socket
import subprocess
import time


class HttpServer:
    def __init__(self, port=80, directory=os.path.dirname(os.path.realpath(__file__))):
        self.port = port
        self.directory = directory

    def start(self):
        """
        Main launch function
        :return:
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', self.port))
            s.listen(5)
            try:
                print('Server started listening on port ' + str(self.port))
                while True:
                    connection, addr = s.accept()
                    with connection as c:
                        data = c.recv(1024)
                        string = bytes.decode(data)
                        request_method = string.split(' ')[0]
                        request_file = string.split(' ')[1]

                        # Only accept GET requests
                        if request_method != 'GET':
                            self.return_501(c)
                            continue

                        # Default to index.html
                        if (request_file == '/'):
                            request_file = '/index.html'

                        # Split URI and GET parameters
                        request_uri, query_string = self.split_request(request_file)
                        full_file_path = self.directory + request_uri
                        static_file_path = self.directory + '/public_html' + request_uri

                        # Check if file exists from root and from public_html
                        if not os.path.isfile(full_file_path) and not os.path.isfile(static_file_path):
                            self.return_404(c)
                        else:
                            # Dynamic
                            if re.match('/cgi-bin/.*', request_file):
                                self.return_200_dynamic(c, request_uri, query_string, addr, request_method)
                            # Static
                            else:
                                self.return_200_static(c, static_file_path)
            except KeyboardInterrupt:
                print("Stopped the server.")
                pass

    def return_200_static(self, connection, file_path):
        """
        Handles static pages
        :param connection: instance of accepted connection
        :param file_path: path to the static file
        :return:
        """
        if mimetypes.guess_type(file_path)[0] == 'text/html':
            file_type = 'r'
        else:
            file_type = 'rb'

        with open(file_path, file_type) as f:
            response_status = self.get_status_line(200)
            response_headers = self.get_headers(file_path)

            # Only encode when text/html
            if file_type == 'r':
                response_content = str.encode(f.read())
            else:
                response_content = f.read()

        print('Serving file: ' + file_path)
        response = str.encode(response_status) + str.encode(response_headers) + response_content
        return connection.send(response)

    def return_200_dynamic(self, connection, request_uri, query_string, address, request_method):
        """
        Handles dynamic pages from cgi-bin
        :param connection: instance of accepted connection
        :param request_uri: file uri
        :param query_string: GET options
        :param address: incoming remote address
        :param request_method: the type of request
        :return:
        """
        file_path = self.directory + request_uri
        proc = subprocess.Popen(["python", file_path], stdout=subprocess.PIPE,
                                env=dict(os.environ,
                                         DOCUMENT_ROOT=self.directory + '/public_html',
                                         REQUEST_METHOD=request_method,
                                         REQUEST_URI=request_uri,
                                         QUERY_STRING=str(self.split_query_string(query_string)),
                                         REMOTE_ADDR=address[0]))
        response_status = self.get_status_line(200)
        response_headers = self.get_headers()
        response_content = proc.stdout.read()

        print('Serving file: ' + file_path)
        response = response_status + response_headers + response_content.decode()
        return connection.send(response.encode())

    @staticmethod
    def split_request(request):
        """
        Splits the request in uri and query GET options
        :param request: the request url
        :return: string of uri, string of queries
        """
        query_string = ''
        if '?' in request:
            request_uri, query_string = request.split('?', 1)
        else:
            request_uri = request
        return request_uri, query_string

    @staticmethod
    def split_query_string(query_string):
        """
        Converts a query string to dict format
        :param query_string:
        :return:
        """
        if query_string == '':
            return None
        try:
            # Split queries
            splitted = query_string.split('&')
            # Create key=value in dict from queries
            return dict(map(str, x.split('=')) for x in splitted)
        except:
            print('Could not convert query string')
            return None

    def return_501(self, connection):
        """
        Returns a 501 page response
        :param connection: instance of accepted connection
        :return:
        """
        response_status = self.get_status_line(501)
        response_headers = self.get_headers()
        response_content = self.get_status_line(501)
        response = response_status + response_headers + response_content
        return connection.send(response.encode())

    def return_404(self, connection):
        """
        Returns a 404 page response
        :param connection: instance of accepted connection
        :return:
        """
        response_status = self.get_status_line(404)
        response_headers = self.get_headers()
        response_content = self.get_status_line(404)
        response = response_status + response_headers + response_content
        return connection.send(response.encode())

    @staticmethod
    def get_status_line(code):
        """
        Get the full response code based on index
        :param code: code index
        :return: string response code
        """
        if code == 200:
            return 'HTTP/1.1 200 OK\n'
        elif code == 404:
            return 'HTTP/1.1 404 Not Found\n'
        elif code == 501:
            return 'HTTP/1.1 501 Not Implemented\n'

    @staticmethod
    def get_headers(file_path=None):
        """
        Generates the headers
        :param file_path:
        :return: str headers
        """
        current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        h = 'Date: ' + current_date + '\n'
        h += 'Server: Python-Socket-Server\n'
        if file_path:
            mime = mimetypes.MimeTypes().guess_type(file_path)[0]
            h += 'Content-Type: ' + mime + '\n'
            h += 'Content-Length: ' + str(os.path.getsize(file_path)) + '\n'
        h += 'Connection: close\n\n'

        return h


if __name__ == '__main__':
    http_server = HttpServer(port=8080)
    http_server.start()
