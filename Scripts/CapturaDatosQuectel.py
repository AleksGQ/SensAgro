#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 17:49:17 2026

@author: lex
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
from datetime import datetime
import sys
import os

# ------------------------------------------------------------
# Configuración
# ------------------------------------------------------------
PORT = "/dev/ttyUSB2"
BAUDRATE = 9600
TIMEOUT = 0.01            # segundos
ITERATIONS = 20
LOOP_DELAY = 2         # segundos

INIT_COMMANDS = [
    "ATI",
    "AT+CGSN",
    "AT+CPIN?",
    "AT+CIMI",
    "AT+QNWPREFCFG=\"nr5g_band\"",
    "AT+CGDCONT?",
    "AT+C5GREG?",
    "AT+QCAINFO",
    "AT+CGCONTRDP",
    "AT+COPS?",
    "AT+QNWINFO",
    "AT+CGPADDR=1"
]

LOOP_COMMANDS = [
    "AT+QNETDEVSTATUS?",
    "AT+QCSQ",
    "AT+QENG=\"servingcell\""
]

# ------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------
def current_datetime_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_log_file():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Quectel_{timestamp}.txt"

    header = (
        "============================================================\n"
        "INFORMACIÓN DEL MÓDEM QUECTEL RM520N-GL\n"
        "============================================================\n\n"
        f"Fecha y hora: {current_datetime_str()}\n"
        f"Puerto: {PORT}\n"
        f"Baudrate: {BAUDRATE}\n"
        "------------------------------------------------------------\n"
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(header)

    return filename


def open_serial_port():
    try:
        print(f"[INFO] Abriendo puerto {PORT} a {BAUDRATE} bps...")
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            timeout=TIMEOUT
        )
        time.sleep(1)
        print("[OK] Conexión con el módem establecida correctamente.")
        return ser
    except serial.SerialException as e:
        print(f"[ERROR] Error al abrir el puerto serie: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        sys.exit(1)


def send_at_command(ser, command):
    """
    Envía un comando AT y devuelve únicamente las líneas de respuesta útiles:
    - Excluye 'OK'
    - Excluye eco del comando
    - Excluye líneas vacías
    """
    try:
        ser.reset_input_buffer()
        full_cmd = command + "\r"
        ser.write(full_cmd.encode("utf-8"))
        time.sleep(0.5)

        response_lines = []
        start_time = time.time()

        while time.time() - start_time < TIMEOUT:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            if line == "OK":
                continue
            if line == command:
                continue
            response_lines.append(line)

        return response_lines

    except serial.SerialException as e:
        print(f"[ERROR] Error de comunicación serie con '{command}': {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Error inesperado con '{command}': {e}")
        return []


def append_lines_to_file(filename, lines):
    if not lines:
        return
    with open(filename, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


# ------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------
def main():

    # 1. Crear archivo TXT con encabezado
    log_filename = create_log_file()
    print(f"[INFO] Archivo de mediciones creado: {log_filename}")

    # 2. Abrir conexión con el módem
    ser = open_serial_port()

    # 3. Ejecutar comandos AT iniciales
    print("[INFO] Ejecutando comandos AT iniciales...")
    for cmd in INIT_COMMANDS:
        print(f"  -> {cmd}")
        lines = send_at_command(ser, cmd)
        append_lines_to_file(log_filename, lines)

    # Separador
    with open(log_filename, "a", encoding="utf-8") as f:
        f.write("------------------------------------------------------------\n")

    # 4. Bucle de mediciones periódicas
    print(f"[INFO] Iniciando bucle de medición ({ITERATIONS} iteraciones)...")

    for i in range(1, ITERATIONS + 1):
        print(f"  Iteración {i}/{ITERATIONS}")
        for cmd in LOOP_COMMANDS:
            lines = send_at_command(ser, cmd)
            append_lines_to_file(log_filename, lines)
        time.sleep(LOOP_DELAY)

    # 5. Cierre de recursos
    try:
        ser.close()
        print("[OK] Puerto serie cerrado correctamente.")
    except Exception:
        print("[WARN] No fue posible cerrar el puerto serie de forma limpia.")

    print("------------------------------------------------------------")
    print("[FINALIZADO] Proceso completado exitosamente.")
    print(f"[ARCHIVO] Los datos fueron almacenados en: {log_filename}")


if __name__ == "__main__":
    main()
