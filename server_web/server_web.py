import socket
import re
import threading
import json
import gzip
import urllib.parse

lock = threading.Lock()
cerere_number_global = 1
def get_content_type(extension):
	if extension == 'html':
		return "text/html"
	elif extension == 'css':
		return "text/css"
	elif extension == 'js':
		return "application/js"
	elif extension == 'png':
		return "text/png"
	elif extension == 'jpg' or extension == 'jpeg':
		return "text/jpeg"
	elif extension == 'gif':
		return "text/gif"
	elif extension == 'ico':
		return "image/x-icon"
	elif extension == 'xml':
		return "application/xml"
	elif extension == 'json':
		return 'application/json'


def http_builder(data, filename=None, compress=False):
	html_response = "HTTP/1.1 200 OK\r\n"
	html_response += "Content-Length: "+str(len(data))+"\r\n"
	if filename:
		html_response += "Content-Type: {}\r\n".format(get_content_type(filename.split('.')[-1]))
	else:
		html_response += "Content-Type: text/html\r\n"
	if compress:
		html_response += "Content-Encoding: gzip\r\n"
	html_response += "Server: server_web.py\r\n\r\n"
	return html_response


def treat_client(clientsocket, address):

	global cerere_number_global, lock
	cerere_number = cerere_number_global
	lock.acquire()
	cerere_number_global += 1
	lock.release()
	
	print('S-a conectat un client. [Index cerere = {}][Start Thread]'.format(cerere_number))
	# se proceseaza cererea si se citeste prima linie de text
	cerere = ''
	linieDeStart = ''
	while True:
		data = clientsocket.recv(1024)
		cerere = cerere + data.decode()
		print('S-a citit mesajul: \n---------------------------\n' + cerere + '\n---------------------------')
		pozitie = cerere.find('\r\n')
		if (pozitie > -1):
			linieDeStart = cerere[0:pozitie]
			print('S-a citit linia de start din cerere: ##### ' + linieDeStart + ' #####')
			
			need_compression = False
			pozitieGzip = cerere.find('gzip')
			if(pozitieGzip > -1):
				print("Encoding accepted")
				need_compression = True

			linieDeStartSplitter = linieDeStart.split()
			method = linieDeStartSplitter[0]
			print("Method : {}".format(method))
			if method == 'GET':
				filename = "../continut" + (linieDeStartSplitter[1] if linieDeStartSplitter[1] != "/" else "/index.html")
				try:
					file = open(filename, "rb")
					data = file.read()
					if need_compression:
						data = gzip.compress(data)
					html_response = http_builder(data, filename=filename, compress=need_compression)
					#html_response += data
					print(html_response)
					clientsocket.sendall(html_response.encode(encoding = 'UTF-8') + data)

					break
				except FileNotFoundError: 
					data="Pagina {} ceruta nu exista".format(linieDeStart.split()[1])
					if need_compression:
						data = gzip.compress(data.encode())
					html_response = http_builder(data, compress=need_compression)

					clientsocket.sendall(html_response.encode(encoding = 'UTF-8') + data)
					break
			elif method == 'POST':
				if linieDeStartSplitter[1] == '/api/utilizatori':
					post_body = cerere.split('\r\n\r\n')[1]
					post_body_fields = post_body.split('&')
					user_dict = {}
					for field in post_body_fields:
						if field.find("username") > -1:
							username = field.split('=')[1]
							if username != "":
								user_dict['utilizator'] = urllib.parse.unquote_plus(username)
						elif field.find("password") > -1:
							password = field.split('=')[1]
							if password != "":
								user_dict['parola'] = urllib.parse.unquote_plus(password)
						elif field.find("nume") > -1:
							nume = field.split('=')[1]
							if nume != "":
								user_dict['nume'] = urllib.parse.unquote_plus(nume)
						elif field.find("prenume") > -1:
							prenume = field.split('=')[1]
							if prenume != "":
								user_dict['prenume'] = urllib.parse.unquote_plus(prenume)
						elif field.find("email") > -1:
							email = field.split('=')[1]
							if email != "":
								user_dict['email'] = urllib.parse.unquote_plus(email)
						elif field.find("color") > -1:
							color = field.split('=')[1]
							if color != "":
								user_dict['color'] = urllib.parse.unquote_plus(color)
						elif field.find("phone") > -1:
							phone = field.split('=')[1]
							if phone != "":
								user_dict['phone'] = urllib.parse.unquote_plus(phone)
						elif field.find("data_nastere") > -1:
							data_nastere = field.split('=')[1]
							if data_nastere != "":
								user_dict['data_nastere'] = urllib.parse.unquote_plus(data_nastere)
						elif field.find("ora_nastere") > -1:
							ora_nastere = field.split('=')[1]
							if ora_nastere != "":
								user_dict['ora_nastere'] = urllib.parse.unquote_plus(ora_nastere)
						elif field.find("varsta") > -1:
							varsta = field.split('=')[1]
							if varsta != "":
								user_dict['varsta'] = urllib.parse.unquote_plus(varsta)
						elif field.find("url") > -1:
							url = field.split('=')[1]
							if url != "":
								user_dict['url'] = urllib.parse.unquote_plus(url)
						elif field.find("descriere_form") > -1:
							descriere_form = field.split('=')[1]
							if descriere_form != "":
								user_dict['descriere_form'] = descriere_form
					print("USERNAME {}\nPAROLA {}\n".format(username, password))
					if (username != '' and password != ''):
						with open('../continut/resurse/utilizatori.json') as json_file:
							users = json.load(json_file)
							json_file.close()
							exists = False
							for user in users:
								if user['utilizator'] == username:
									data="Operatiune esuata. Utilizatorul dat exista deja"
									exists = True
									break
							if not exists:
								data="Operatiune cu succes. Utilizatorul a fost adaugat"
								
								users.append(user_dict)
								print(users)
								with open('../continut/resurse/utilizatori.json', 'w') as json_file:
									json_file.write(json.dumps(users))
					else:
						data="Operatiune esuata. Parola si numele de utilizator nu trebuie sa fie goale"
					if need_compression:
						data = gzip.compress(data.encode())
					html_response = http_builder(data, compress=need_compression)
					clientsocket.sendall(html_response.encode(encoding = 'UTF-8') + data)
					break

				else:
					data="Pagina {} ceruta nu exista".format(linieDeStart.split()[1])
					if need_compression:
						data = gzip.compress(data.encode())
					html_response = http_builder(data, compress=need_compression)
					clientsocket.sendall(html_response.encode(encoding = 'UTF-8') + data)
					break
		else:
			break
			
	print('S-a terminat citirea.')
	# TODO interpretarea sirului de caractere `linieDeStart` pentru a extrage numele resursei cerute
	# TODO trimiterea răspunsului HTTP
	clientsocket.close()
	print('S-a terminat comunicarea cu clientul cu cererea {}.[Stop Thread]'.format(cerere_number))


def main():
	# creeaza un server socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# specifica ca serverul va rula pe portul 5678, accesibil de pe orice ip al serverului
	serversocket.bind(('', 5678))
	# serverul poate accepta conexiuni; specifica cati clienti pot astepta la coada
	serversocket.listen(5)
	threads=[]

	while True:
		print('#########################################################################')
		print('Serverul asculta potentiali clienti.')
		# asteapta conectarea unui client la server
		# metoda `accept` este blocanta => clientsocket, care reprezinta socket-ul corespunzator clientului conectat
		(clientsocket, address) = serversocket.accept()
		t = threading.Thread(target=treat_client, args=(clientsocket, address))
		t.start()
		threads.append(t)
	
	for thread in threads:
		thread.join()
		


if __name__ == '__main__':
	main()