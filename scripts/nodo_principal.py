import socket
import json
import os

PUERTO_ESCUCHA = 5050
PUERTO_DESTINO = 5051
BUFFER_SIZE = 4096
MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024

def recibir_y_reenviar():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('0.0.0.0', PUERTO_ESCUCHA))
    servidor.listen(5)
    print(f"[Servidor] Esperando archivos en el puerto {PUERTO_ESCUCHA}...")

    while True:
        conn, addr = servidor.accept()
        print(f"[Servidor] Conexión desde {addr[0]}")

        try:
            # Recibir longitud del JSON (10 bytes)
            data = conn.recv(10).decode().strip()
            print(f"[DEBUG] Cabecera recibida: {data}")
            metadata_len = int(data)

            # Recibir el JSON exacto
            metadata = b""
            while len(metadata) < metadata_len:
                remaining = metadata_len - len(metadata)
                metadata += conn.recv(remaining)

            paquete = json.loads(metadata.decode())
            nombre = paquete['nombre']
            destino_ip = paquete['destino']

            # Guardar archivo temporal
            temp_path = f"temp_{nombre}"
            total_recibido = 0

            with open(temp_path, 'wb') as f:
                while True:
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_recibido += len(chunk)
                    if total_recibido > MAX_FILE_SIZE:
                        print("[ERROR] Archivo excede 3GB")
                        os.remove(temp_path)
                        return

            print(f"[Servidor] Archivo '{nombre}' recibido ({total_recibido} bytes)")

            # Reenviar al receptor final
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                    cliente.connect((destino_ip, PUERTO_DESTINO))

                    metadata_envio = json.dumps({
                        'nombre': nombre,
                        'tamano': total_recibido
                    }).encode()

                    cliente.sendall(f"{len(metadata_envio):<10}".encode())
                    cliente.sendall(metadata_envio)

                    with open(temp_path, 'rb') as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            cliente.sendall(chunk)

                print(f"[Servidor] Archivo reenviado a {destino_ip}:{PUERTO_DESTINO}")
            except Exception as e:
                print(f"[ERROR] Reenvío fallido: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"[ERROR] Fallo al procesar conexión: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    recibir_y_reenviar()
