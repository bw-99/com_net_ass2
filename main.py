from socket import *
import os
from time import time
import threading

file_list = os.listdir()
file_list.append('/')
file_list.append('')
file_list.append('favicon.ico')

SERVER_IP=gethostbyname(getfqdn())
SERVER_PORT=10080

SERVER="http://{}:{}".format(SERVER_IP,SERVER_PORT)

def createServer(file_list=file_list):
    serversocket = socket(AF_INET, SOCK_STREAM)
    serversocket.bind((SERVER_IP,SERVER_PORT))
    serversocket.listen(5)
    while(1):
        try:
            (clientsocket, address) = serversocket.accept()
            t=threading.Thread(target=handle_req,args=(clientsocket,))
            t.start()
        except:
            pass

    serversocket.close()

def handle_req(clientsocket):
    rd = clientsocket.recv(5000).decode()
    pieces = rd.split("\n")
    print(pieces)
    id, pw = get_id_pw(pieces[-1])

    destination, cookie = parse_pieces(pieces)
    if (destination == "None"):
        pass
    else:
        index = find_file(destination)
        cookie_value, cookie_refresh,\
        cookie_start_time, cookie_referer,\
        cookie_id,cookie_pw = get_cookie_from_dic(cookie)
        cookie_id=find_real_idorpw(id,cookie,cookie_id,'id')
        cookie_pw=find_real_idorpw(pw,cookie,cookie_pw,'pw')

        if (cookie_value == '0' or cookie_value == "None"):
            send_before_login(index, clientsocket, cookie_refresh,
                              cookie_value,cookie_referer, cookie_id, cookie_pw)
        else:
            send_after_login(index, clientsocket, cookie_start_time, cookie_value, cookie_id)
    clientsocket.shutdown(SHUT_WR)

def get_cookie_from_dic(cookie):
    cookie_value = cookie[' login']
    cookie_refresh = cookie['Refresh']
    cookie_start_time = cookie['start_time']
    cookie_referer = cookie['Referer']
    cookie_id=cookie['id']
    cookie_pw=cookie['pw']
    return cookie_value,cookie_refresh,cookie_start_time,cookie_referer,cookie_id,cookie_pw

def find_real_idorpw(val,cookie,cookie_val,index):
    if (val != -1):
        cookie['{}'.format(index)] = val
    else:
        val=cookie_val
    return val


def send_before_login(index,clientsocket,refresh, login,cookie_referer,id,pw):
    if (index == ""):
        index = "index.html"
        data_format = find_format(index)
        data = "HTTP/1.1 200 OK\r\n"
        data += "Content-Type: " + data_format + "; charset=utf-8\r\n"
        data += "Set-Cookie: login=0;max-age=360000\r\n"
        data += "Set-Cookie: start_time={};max-age=30\r\n".format(-1)
        data += "\r\n"
        clientsocket.send(data.encode())
        send_data(index,clientsocket)
    elif( index == "index.html"):
        send_403(clientsocket)
    elif(index=="secret.html" and refresh=="False" and cookie_referer=="True"):
        data_format = find_format(index)
        data = "HTTP/1.1 200 OK\r\n"
        data += "Content-Type: " + data_format + "; charset=utf-8\r\n"
        data += "Set-Cookie: login=1;max-age=30\r\n"
        data += "Set-Cookie: id={};max-age=30\r\n".format(id)
        data += "Set-Cookie: pw={};max-age=30\r\n".format(pw)
        data += "Set-Cookie: start_time={};max-age=30\r\n".format(time())
        data += "\r\n"
        clientsocket.send(data.encode())
        send_data(index,clientsocket)
    else:
        send_403(clientsocket)

def send_data(index,clientsocket):
    with open(index, "rb") as k:
        html = k.read(100000)
        while (html):
            data = html
            clientsocket.send(data)
            html = k.read(100000)
    k.close()

def send_after_login(index,clientsocket,start_time,login, cookie_id):
    if(index==-1):
        send_404(clientsocket)
    else:
        data_format = find_format(index)
        if (index == "" or index== "index.html"):
            index = "secret.html"

        if(index=="cookie.html"):
            send_200(clientsocket, data_format)
            end_time = time()
            with open(index, "r") as k:
                html = k.read()
                data = """{}""".format(html)
                t=round(30-end_time+float(start_time),3)
                t=0 if t<0 else t
                data=data.format(cookie_id,t)
                clientsocket.send(data.encode())
            k.close()
        else:
            send_200(clientsocket,data_format)
            send_data(index,clientsocket)

def send_200(clientsocket,data_format):
    data = "HTTP/1.1 200 OK\r\n"
    data += "Content-Type: " + data_format + "; charset=utf-8\r\n"
    data += "\r\n"
    clientsocket.send(data.encode())

def send_404(clientsocket):
    data = "HTTP/1.1 404 NOT FOUND\r\n"
    clientsocket.send(data.encode())

def send_403(clientsocket):
    data = "HTTP/1.1 403 Forbidden\r\n"
    clientsocket.send(data.encode())

def parsing(word):
    name=word.split('=')[0][0:]
    value=word.split('=')[1][0:]
    return name,value

def get_id_pw(word):
    if ('=' in word and '&' in word):
        word = word.split('&')
        id = word[0].split('=')[1]
        pw = word[1].split('=')[1]
    else:
        id, pw = -1, -1
    return id,pw

def find_cookie_item(word):
    for k in range(len(word)):
        if ' login' in word[k]:
            login_name,login_value=parsing(word[k])
        elif 'start_time' in word[k]:
            time_name,time_value=parsing(word[k])
        elif 'id' in word[k]:
            id_name,id_value=parsing(word[k])
        elif 'pw' in word[k]:
            pw_name,pw_value=parsing(word[k])

    return login_name,login_value,time_name,\
           time_value,id_name,id_value,pw_name,pw_value

def parse_pieces(pieces):
    tag=0
    destination="None"
    cookie_after = {' login': 'None', 
                    'Refresh' : 'False', 
                    'start_time' : 'None', 
                    'Referer' : 'False', 
                    'id' : 'None', 
                    'pw' : 'None'
                    }
    if (len(pieces) > 1):   #빈 소캣을 보낼 경우 방지
        destination = pieces[0].split(" ")[1][1:]
    for item in pieces:
        if("Cookie:" in item ): #쿠키가 있다면
            tag+=1      # 로그인이 만료된 후 쿠키가 사라짐 -> 만료되지 않은 경우 tag = 1
            try:
                item = item.split(':')[1].split('; ')
                login_name, login_value,time_name,time_value,id_name,id_value,pw_name,pw_value = find_cookie_item(item)
                cookie_after[time_name] = time_value
                cookie_after[login_name] = login_value
                cookie_after[id_name]=id_value
                cookie_after[pw_name]=pw_value
            except:
                pass
        if("Referer" in item):
            cookie_after['Referer']='True'

    if(tag==0): # tag가 증가되지 않았다면 로그인이 만료된 후 새로고침하려 한 것이므로 refresh를 true로 변경
        cookie_after['Refresh'] = 'True'

    return destination, cookie_after

def find_file(destination,file_list=file_list):
    if(destination=="favicon.ico"):
        return -1
    if('?' in destination):
        destination=destination.split('?')[0]
    for item in file_list:
        if (item == destination):
            return item
    return -1

def find_format(index):
    if (index):
        data_format = index.split(".")[1]
    else:
        data_format = "text"
    return data_format


print('Access ',SERVER)

createServer()