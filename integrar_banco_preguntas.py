# -*- coding: utf-8 -*-
"""
Script de Integración Automática
=================================

Este script modifica modulo_superadmin.py para integrar el Banco de Preguntas
profesional de forma automática.

Uso:
    python integrar_banco_preguntas.py
"""

import os
import sys
import re
from pathlib import Path


def crear_respaldo(archivo):
    """Crea un respaldo del archivo original."""
    respaldo = archivo.replace(".py", "_respaldo.py")
    if not os.path.exists(respaldo):
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
        with open(respaldo, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"✓ Respaldo creado: {respaldo}")
        return respaldo
    return respaldo


def integrar_automaticamente(archivo_modulo):
    """Integra automáticamente la nueva interfaz en modulo_superadmin.py"""

    if not os.path.exists(archivo_modulo):
        print(f"✗ Archivo no encontrado: {archivo_modulo}")
        return False

    # Crear respaldo
    crear_respaldo(archivo_modulo)

    # Leer archivo
    with open(archivo_modulo, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Buscar e insertar import al inicio del archivo
    import_nuevo = (
        "from interfaz_banco_preguntas import InterfazBancoPreguntasAvanzada\n"
    )

    # Encontrar el módulo intro (después del docstring y otros imports)
    if import_nuevo not in contenido:
        # Buscar dónde insertar el import (después de los demás imports)
        lines = contenido.split("\n")
        insert_line = 0

        for i, linea in enumerate(lines):
            if (
                linea.startswith("try:")
                and "PIL" in contenido[max(0, len("\n".join(lines[:i])) - 50) :]
            ):
                insert_line = i + 1
                break

        # Insertar import (ubicarlo justo antes de la definición de clase o funciones)
        for i, linea in enumerate(lines):
            if linea.startswith("class ModuloSuperAdmin"):
                # Insertar antes de la clase
                lines.insert(i, import_nuevo)
                break

        contenido = "\n".join(lines)
        print("✓ Import agregado")

    # Reemplazar el método _build_preguntas_tab
    patron_old = r"def _build_preguntas_tab\(self\):.*?(?=\n    def |\Z)"

    metodo_nuevo = '''def _build_preguntas_tab(self):
        """Construye la pestaña de Banco de Preguntas (versión profesional)."""
        InterfazBancoPreguntasAvanzada._build_preguntas_tab_mejorada(self)'''

    # Verificar si ya está reemplazado
    if (
        "InterfazBancoPreguntasAvanzada" in contenido
        and "_build_preguntas_tab_mejorada" in contenido
    ):
        print("✓ El método ya está integrado")
        return True

    # Hacer el reemplazo
    contenido_nuevo = re.sub(patron_old, metodo_nuevo, contenido, flags=re.DOTALL)

    if contenido_nuevo == contenido:
        # Si no encontró con espacios, intentar sin espacios
        print("⚠ No se encontró el patrón exacto, intentando alternativa...")

        # Alternativa: buscar manualmente
        if "def _build_preguntas_tab(self):" in contenido:
            # Encontrar el inicio y fin del método
            inicio = contenido.find("def _build_preguntas_tab(self):")
            if inicio != -1:
                # Encontrar el siguiente método
                siguiente_metodo = contenido.find("\n    def ", inicio + 1)
                if siguiente_metodo != -1:
                    contenido_nuevo = (
                        contenido[:inicio] + metodo_nuevo + contenido[siguiente_metodo:]
                    )
                    print("✓ Método reemplazado (alternativa)")
    else:
        print("✓ Método _build_preguntas_tab reemplazado")

    # Guardar archivo modificado
    with open(archivo_modulo, "w", encoding="utf-8") as f:
        f.write(contenido_nuevo)

    print(f"✓ Archivo actualizado: {archivo_modulo}")
    return True


def verificar_archivos_necesarios():
    """Verifica que los archivos necesarios existan."""
    archivos_requeridos = [
        "banco_preguntas_profesional.py",
        "interfaz_banco_preguntas.py",
        "modulo_superadmin.py",
    ]

    print("Verificando archivos necesarios...")
    faltantes = []

    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            print(f"  ✓ {archivo}")
        else:
            print(f"  ✗ {archivo} (FALTANTE)")
            faltantes.append(archivo)

    return len(faltantes) == 0, faltantes


def main():
    """Función principal."""
    print("=" * 60)
    print("INTEGRACIÓN AUTOMÁTICA - BANCO DE PREGUNTAS PROFESIONAL")
    print("=" * 60 + "\n")

    # Verificar archivos
    ok, faltantes = verificar_archivos_necesarios()
    if not ok:
        print(f"\n✗ Error: Faltan {len(faltantes)} archivo(s):")
        for arch in faltantes:
            print(f"    - {arch}")
        print("\nAsegúrate de que todos los archivos estén en el mismo directorio.")
        return False

    print("\n✓ Todos los archivos están presentes\n")

    # Confirmar antes de proceder
    print("⚠ ADVERTENCIA: Se modificará 'modulo_superadmin.py'")
    print("   Se creará un respaldo automáticamente.\n")

    respuesta = input("¿Deseas continuar? (s/n): ").strip().lower()
    if respuesta != "s":
        print("Operación cancelada.")
        return False

    # Integrar
    print("\nIntegrando...\n")
    exitoso = integrar_automaticamente("modulo_superadmin.py")

    if exitoso:
        print("\n" + "=" * 60)
        print("✓ INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\nPróximos pasos:")
        print("1. Ejecuta tu aplicación normalmente")
        print("2. Abre la pestaña 'Banco Preguntas' en SuperAdmin")
        print("3. Disfruta de la nueva interfaz profesional")
        print("\nSi necesitas revertir, ejecuta:")
        print("    python")
        print("    >>> import shutil")
        print(
            "    >>> shutil.copy('modulo_superadmin_respaldo.py', 'modulo_superadmin.py')"
        )
        return True
    else:
        print("\n✗ Error durante la integración")
        return False


if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)
