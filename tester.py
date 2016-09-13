import subprocess
import os

# p = subprocess.Popen('/home/yorick/IdeaProjects/computer-networks-http-server/cgi-bin/test.py', shell=True, stdout=subprocess.PIPE)
# output, err = p.communicate()
# print(output, err)

string = 'localhost?haha=2929'

def split_request(request):
    query_string = ''
    if '?' in request:
        request_uri, query_string = request.split('?', 1)
    else:
        request_uri = request
    return request_uri, query_string

def split_query_string(query_string):
    splitted = query_string.split('&')
    return dict(map(str, x.split('=')) for x in splitted)


print(split_request(string))
_, query_string = split_request(string)
print(query_string)
print(split_query_string(query_string))