import socket
import json
import os

PUERTO_ESCUCHA = 5051
BUFFER_SIZE = 4096
MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024  # 3GB

def recibir_archivo():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('0.0.0.0', PUERTO_ESCUCHA))
    servidor.listen(5)
    print(f"[Receptor] Esperando archivos en el puerto {PUERTO_ESCUCHA}...")

    while True:
        conn, addr = servidor.accept()
        print(f"[Receptor] Conexión desde {addr[0]}")

        try:
            data = conn.recv(10).decode().strip()
            print(f"[DEBUG] Longitud de metadatos recibida: {data}")
            metadata_len = int(data)

            metadata = b""
            # Recibir JSON metadata con control de bytes extra
            while len(metadata) < metadata_len:
                received = conn.recv(BUFFER_SIZE)
                if not received:
                    raise Exception("Conexión cerrada inesperadamente")
                metadata += received

            # Aquí puede haber bytes extra en metadata (más allá del JSON)
            json_bytes = metadata[:metadata_len]
            extra_bytes = metadata[metadata_len:]  # bytes que corresponden al archivo, recibidos junto con el JSON

            try:
                metadata_decoded = json_bytes.decode()
                print(f"[DEBUG] Metadatos recibidos: {metadata_decoded}")
                paquete = json.loads(metadata_decoded)
            except Exception as e:
                print(f"[ERROR] Fallo al decodificar JSON: {e}")
                conn.close()
                continue

            nombre = paquete['nombre']
            tamano = paquete['tamano']

            with open(nombre, 'wb') as f:
                total_recibido = 0

                # Primero escribe los bytes extra (de archivo) ya recibidos
                if extra_bytes:
                    f.write(extra_bytes)
                    total_recibido += len(extra_bytes)

                # Ahora sigue recibiendo el resto del archivo
                while total_recibido < tamano:
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_recibido += len(chunk)

            print(f"[Receptor] Archivo '{nombre}' recibido correctamente ({total_recibido} bytes)")

        except Exception as e:
            print(f"[ERROR] Fallo al recibir archivo: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    recibir_archivo()
