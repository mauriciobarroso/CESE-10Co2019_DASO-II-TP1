import socket
import sys
import json
import threading
import time
import signal

############## clase para obtener la lista de divisas ############
class Currency:
    @staticmethod
    def get_list( filepath ):
        # se lee la ruta del archivo csv
        with open( filepath, 'r' ) as f:
            file_location = f.read()

        # se lee el archivo csv y se crea un lista de diccionarios con los valores leídos
        currency_list = []

        with open( file_location + 'currency.csv', 'r', encoding = 'utf-8' ) as f:
            f.readline()    # se omite la primera línea
            file_data = f.read()

            # se crea un diccionario por cada línea del archivo csv y se añaden a la lista de divisas
            for lines in file_data.split( '\n' ):
                values = lines.split( ',' )
            
                currency_info = {
                    "id": int( values[ 0 ] ),
                    "name": values[ 1 ],
                    "value1": float( values[ 2 ] ),
                    "value2": float( values[ 3 ] ),
                }
                currency_list.append( currency_info )

        return currency_list

############### clase para sockets UDP clientes ###############
class ClientConnection( threading.Thread ):
    def __init__( self, addr, port ):
        super().__init__()

        self.s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.server_addr = ( addr, port )

        self.shutdown_flag = threading.Event()  
    
    def run( self ):
        print( "Thread #%s iniciado" % self.ident )

        # se crea una variable para controlar el tiempo en el que se actualiza la lista de divisas
        # se inicializa en 30 para que la primera vez que itere el ciclo while se actualice la lista de divisas
        time_counter = 30

        # se acualiza la lista de divisas cada 30 segundos
        try:
            while not self.shutdown_flag.is_set():           
                if time_counter == 30:
                    # se obtiene la lista de divisas del archivo config.txt
                    currency_list = Currency.get_list( "config.txt" )

                    # se envía la lista de divisas convertida a formato json por el socket
                    print( "Enviando lista de divisas..." )
                    self.s.sendto( bytearray( json.dumps( currency_list ), 'utf-8' ), self.server_addr )
                    self.s.settimeout( 2 )  # se configura un timer para verificar que el servidor reciba lo que se envia

                    # se recibe la respuesta del servidor y se imprime
                    ( data, addr ) = self.s.recvfrom( 128 )

                    if data.__len__() > 0:
                        print( str( data, "utf-8" ) + " from: " + str( addr[ 0 ] ) + ":" + str( addr[ 1 ] ) )
                    else:
                        print( "fail")
                        break

                    # se reinicia el contador de tiempo
                    time_counter = 0

                # se ejecuta sleep por 1 segundo y se aumenta en 1 el contador de tiempo
                time.sleep( 1 )
                time_counter = time_counter + 1                   
        
        # se captura el error de timeout del socket
        except socket.timeout:
            print( "Tiempo máximo de espera superado" )
        
        # se captura el error de archivo no encontrado
        except FileNotFoundError:
            print( "No se puede encontrar config.txt" )

        # se finaliza el thread cerrando el socket asociado a este
        finally:            
            print( "Thread #%s terminado" % self.ident )
            self.s.close()
            print( "Socket cerrado" )

################# handler para SIGINT #################
def service_shutdown( signum, frame ):
    print( "Signal %d capturada" % signum )
    raise KeyboardInterrupt # se genera una excepción de tipo KeyboardInterrupt

##################### main ########################

# se configura un handler para la señal SIGINT
signal.signal( signal.SIGINT, service_shutdown )

print( "Iniciando main" )

# se lanzan 2 instancias de ClientConnection para establecer conexión con dos
# servidores en disitintas direcciones IP y puertos
try:
    client1 = ClientConnection( "localhost", 10000 )
    client1.start()

    client2 = ClientConnection( "localhost", 10001 )
    client2.start()

    while True:
        # se puede ejecutar alguna otra cosa en el thread principal
        time.sleep( 1 )

# se poene en 1 el shutdown_flag para detener la ejecución de los threads y
# se ejecuta join para esperar la terminación de los threads antes de terminar
except KeyboardInterrupt:
    client1.shutdown_flag.set()
    client2.shutdown_flag.set()

    client1.join()
    client2.join()

print( "Saliendo de main" )