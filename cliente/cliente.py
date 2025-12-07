import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import socket
import struct
import proto.projeto02_pb2 as proto

GRUPO = "224.1.1.1"         #ip do grupo multicast definido
PORTA_GRUPO = 5007          #porta do grupo multicast (igual)
PORTA_TCP_GATEWAY = 7000

gateway_addr = None         # IP do gateway (descoberto no discovery)

def encontrar_gateway():
    print("[Cliente] Procurando GATEWAY...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('', PORTA_GRUPO))
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_GRUPO}.")

    mreq = struct.pack("4sl", socket.inet_aton(GRUPO), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, addr = sock.recvfrom(1024)
        
        try:
            msg = proto.Descoberta()
            msg.ParseFromString(data)
            
            if msg.inicia_descoberta:
                ip_gateway = addr[0]
                print(f"[CLIENTE] Gateway encontrado em: {ip_gateway}")
                sock.close()
                return ip_gateway
                
        except Exception:
            continue

def enviando_requisicoes_gateway():
    comando = input("Deseja se concetar ao servidor [S/N]? ")
    if comando == "S":
        gateway_addr = encontrar_gateway()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((gateway_addr, PORTA_TCP_GATEWAY))
            print(f"[CLIENTE] Conectado com sucesso!")
        except Exception as e:
            print(f"[CLIENTE] Erro ao conectar: {e}")
            return
        
        while True:
            print("\n--- MENU ---")
            print("1. Listar Dispositivos")
            print("2. Enviar Comando (LIGAR/DESLIGAR)")
            print("0. Sair")
            comando = input("Opção: ")

            if comando == "0":
                break
            elif comando == "1":
                req = proto.RequisicaoCliente()
                req.pedir_lista = True
                
                sock.send(req.SerializeToString())
                
                 #                            Correção
                #####################################################################
                # Na conexão TCP não se pode simplesmente enviar e receber sem saber
                # os tamanhos das mensagens, isso pode deixar o processo esperando 
                # mais bytes do que de fato tem, e trava
                raw_len = sock.recv(4)
                msg_len = int.from_bytes(raw_len, "big")
                data = sock.recv(msg_len)
                ######################################################################

                #data = sock.recv(4096)
                lista = proto.ListaDispositivos()
                lista.ParseFromString(data)
                
                print("\n--- DISPOSITIVOS CONECTADOS ---")
                for dev in lista.dispositivos:
                    if dev.online:
                        conexao = "ONLINE"
                    else:
                        conexao = "OFFLINE"
                    print(f"ID: {dev.id} | Tipo: {dev.tipo} | Estado: {dev.estado} | IP: {dev.ip}:{dev.porta} | Conexão: {conexao}")
            elif comando == "2":
                alvo_id = input("ID do Atuador (ex: Atuador01): ")
                cmd_str = input("Comando (LIGAR/DESLIGAR): ")
                
                req = proto.RequisicaoCliente()
                cmd = req.comando
                cmd.id_alvo = alvo_id
                cmd.tipo_comando = cmd_str
                
                sock.send(req.SerializeToString())
                #####################################################################
                # Na conexão TCP não se pode simplesmente enviar e receber sem saber
                # os tamanhos das mensagens, isso pode deixar o processo esperando 
                # mais bytes do que de fato tem, e trava
                raw_len = sock.recv(4)
                msg_len = int.from_bytes(raw_len, "big")
                data = sock.recv(msg_len)
                ######################################################################

                resp = proto.RespostaComando()
                resp.ParseFromString(data)
                print(f"[CLIENTE] Resposta: {resp.mensagem} (Sucesso: {resp.sucesso})")
        sock.close()

enviando_requisicoes_gateway()