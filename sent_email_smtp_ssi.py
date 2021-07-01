import socket
import sys

import binascii

import smtplib, ssl
from email.message import EmailMessage

import requests
import json

# Modo debug Mostrar en consola
DEBUG = True

#ANDRES ES GENIAL

# Configuración TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('', 52300) # IP local, Puerto
#server_address = ('192.168.90.10', 52300)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)
sock.listen(1)


# Configuración Correos
sender_email = "cierres.pos@grupoconsultel.com" ##EMAIL LOCAL
password_email = 'TMS.2021**'      ## PASSWORD EMAIL LOCAL
def_error_email = "cierres.pos@grupoconsultel.com" ## EMAIL RECEPTOR
SMTP_SSL_HOST = 'secure.emailsrvr.com' ## HOST DEL CORREO
SMTP_SSL_PORT = 465 ## PUERTO DEL CORREO


# Configuración API Correos
API_URL_INI = "http://66.97.35.26/email-api/"
API_URL_END = "/get"
HEAD_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaGVjayI6dHJ1ZSwiaWF0IjoxNjI0MzY4MzY0fQ.M8WeSgwCzPD4UBDbkj0yJBsFkMqtdufKpkeEBga6ZpA"
DEFAUL_COD_ADQ = '82481842'

# Función para mostar Trama de bytes
def print_bytes(data_bytes):
    rep = 0
    rep_2 = 0
    n_line = 0
    hex_data_bytes = data_bytes.hex()
    len_hex_data_bytes = len(hex_data_bytes)
    len_line = 32

    while( rep <  len_hex_data_bytes):
        print( '[' + str(n_line) + ']:\t', end='')

        if ( (len_hex_data_bytes - rep) >  len_line):
            for x in range(0,len_line,2):
                if(x == len_line/2):
                    print( '  ', end='')       
                print( hex_data_bytes[rep + x] + hex_data_bytes[rep + x + 1], end=' ')

            print('  ', end=' ' )
            for x in range(0,len_line//2):
                if(x == len_line//4):
                    print( '  ', end='') 
        else:
            for x in range(0,len_hex_data_bytes - rep, 2):
                if(x == len_line//2):
                    print( '  ', end='')
                print( hex_data_bytes[rep + x] + hex_data_bytes[rep + x + 1], end=' ')

            print(' '*(49-(len_hex_data_bytes - rep) ), end=' ' )
            for x in range(0,(len_hex_data_bytes - rep)//2):
                if(x == len_line//4):
                    print( '  ', end='') 

        print('')
        n_line = n_line + 1
        rep = rep + len_line;
        rep_2 = rep_2 + len_line//2 


# Función para mostar Trama de bytes
def send_email(subject_email, data, sender_email, rec_email, password):  
    server = smtplib.SMTP_SSL(host=SMTP_SSL_HOST, port=465)
    msg = EmailMessage()
    msg['subject'] = subject_email   
    msg['From'] = sender_email
    msg['to'] = rec_email
    msg.set_content(data)
   
    server.login(sender_email, password)
    if DEBUG: print("Login success")
    server.send_message(msg)
    #server.sendmail(sender_email, rec_email, message)
    if DEBUG: print("Email has been sent to: ", rec_email)
    server.close()


#Funcion Para Utilizar API-Correos
def get_email_cod_adq(codigo_adquiriente):
    api_end_point= API_URL_INI + codigo_adquiriente + API_URL_END
    api_headers={'access-token': HEAD_ACCESS_TOKEN}
    api_response = requests.get(url = api_end_point, headers = api_headers)
    return api_response



# Main del Programa
#if False:
if __name__ == '__main__':
    len_email = 0
    correo = None
    msg_final = None
    while True:

        # Wait for a connection
        print('Esperando por conexion')
        print('\n')
        connection, client_address = sock.accept()
        raw_data = b'';
        try:
            print('Conexion desde', client_address)
            print('\n')
            # Receive the data in small chunks and retransmit it
            while True:
                data_rec = connection.recv(2)
                if data_rec:
                    data_len = int(data_rec.hex(), 16)
                    raw_data = data_rec + connection.recv(data_len)
                    len_email = int(raw_data.decode("utf-8")[0:2])
                    correo = raw_data.decode("utf-8")[2:len_email+2]
                    msg_final = raw_data.decode("utf-8")[len_email+2:data_len]

                    if DEBUG: print( 'RAW DARA IN: \n')
                    if DEBUG: print(raw_data)
                    if DEBUG: print_bytes(raw_data)
                    if DEBUG: print(msg_final)

                    serial_pos = ''
                    codigo_adquiriente = ''
                    hora_cierre = ''
                    fecha_cierre = ''
                    monto_total = ''
                    tipo_cierre = ''
                    data_list = raw_data.decode("utf-8").split('\n')
                    if len(data_list) >= 18:
                        serial_pos = data_list[7].strip()
                        codigo_adquiriente = data_list[13].strip()
                        hora_cierre = data_list[10].replace('Hora Cierre:','').strip()
                        fecha_cierre = data_list[11].replace('Fecha Cierre:','').strip()
                        monto_total = data_list[18].strip()
                        tipo_cierre = data_list[4].strip()
                        Asunto_Comp = tipo_cierre + " MP70 SN:" + serial_pos + " FECHA:" + fecha_cierre + "-" + hora_cierre

                        codigo_adquiriente_8 = ''
                        if( len(DEFAUL_COD_ADQ) != 0):
                            codigo_adquiriente_8 = DEFAUL_COD_ADQ
                        else:
                            codigo_adquiriente_8 = codigo_adquiriente[-8:]

                        if DEBUG: print("\n\nCodigo Adquirente_8: " + codigo_adquiriente_8)
                        

                        resp_api_corr = None
                        resp_api_corr = get_email_cod_adq(codigo_adquiriente_8)
                        if resp_api_corr != None:
                            if DEBUG: print(resp_api_corr.content)
                            resp_api_json = json.loads(resp_api_corr.content.decode("utf-8"))
                            if(resp_api_json["status"] == 200):
                                send_email(Asunto_Comp, msg_final, sender_email, resp_api_json["email"], password_email)
                                #send_email(Asunto_Comp, msg_final, sender_email, def_error_email, password_email)
                            else:
                                msg_final_2 = 'Error al enviar Correo Codigo Adquiriente (' +  codigo_adquiriente_8 + ') \nERROR: ' + resp_api_json["message"] + msg_final
                                send_email("Error Correo " + Asunto_Comp, msg_final_2, sender_email, def_error_email, password_email)
                                print('No se puedo enviar correo al cliente con Codigo Adquiriente ' +  codigo_adquiriente_8 + ', ERROR: ', resp_api_json["message"])

                        else:
                            print('No se puedo enviar correo, problema la Api para consultar correo', client_address)
                        
                        
                    else:
                        send_email("CIERRE MP70", msg_final, sender_email, def_error_email, password_email)

                   
                else:
                    break
        except Exception as e:
            print('Error Envio Correo')
            print('Exception: ', e)

            
        connection.close()
        
            

