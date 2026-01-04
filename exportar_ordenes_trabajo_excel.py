import json
import openpyxl
import os

# Archivo JSON donde se guardan las órdenes
DATA_FILE = r"C:\RICHARD\RB\2025\Taller Mecánica\ordenes_taller.json"

# Archivo Excel de salida (siempre en la carpeta Taller Mecánica)
OUTPUT_FILE = r"C:\RICHARD\RB\2025\Taller Mecánica\ordenes_taller.xlsx"



def exportar_a_excel():
    # Verificar que el archivo JSON existe
    if not os.path.exists(DATA_FILE):
        print("⚠️ No se encontró el archivo ordenes_taller.json. Guarda al menos una orden primero.")
        return

    # Cargar todas las órdenes
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            ordenes = json.load(f)
    except json.JSONDecodeError:
        print("⚠️ El archivo ordenes_taller.json está vacío o dañado.")
        return

    # Crear libro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Órdenes de Trabajo"

    # Encabezados
    headers = ["Fecha", "Placa", "Cliente", "Servicio", "Estado", "Subtotal", "IVA", "Total"]
    ws.append(headers)

    # Filas con datos
    for o in ordenes:
        ws.append([
            o.get("fecha", ""),
            o.get("placa", ""),
            o.get("cliente", ""),
            o.get("servicio", ""),
            o.get("estado", ""),
            o.get("subtotal", 0),
            o.get("iva", 0),
            o.get("total", 0)
        ])

    # Guardar archivo Excel
    try:
        wb.save(OUTPUT_FILE)
        print(f"✅ Órdenes exportadas correctamente a: {OUTPUT_FILE}")
    except PermissionError:
        print("⚠️ No se pudo guardar el archivo porque está abierto en Excel. Ciérralo y vuelve a intentar.")

if __name__ == "__main__":
    exportar_a_excel()
    

