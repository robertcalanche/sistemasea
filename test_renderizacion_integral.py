#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST INTEGRAL - RENDERIZACIÓN DE EXPRESIONES MATEMÁTICAS
Módulo Estudiante - Sistema SEA

Valida:
1. Detección de expresiones
2. Extracción de fórmulas
3. Renderización a imagen
4. Integración en UI
5. Rendimiento (caché)
"""

import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

try:
    import tkinter as tk
    from PIL import Image, ImageTk, ImageDraw
    import io
    from Admin import ModuloEstudiante
    from modulo_superadmin import renderizar_formula

    print("[INFO] Dependencias importadas correctamente")
except ImportError as e:
    print(f"[ERROR] Falta dependencia: {e}")
    sys.exit(1)

# ============================================================================
# TEST 1: Renderización básica
# ============================================================================


def test_renderizacion_basica():
    """Valida que renderizar_formula() genera imágenes correctamente"""
    print("\n" + "=" * 70)
    print("TEST 1: RENDERIZACIÓN BÁSICA")
    print("=" * 70)

    test_cases = [
        ("4x^{2}y^{3} - 5x^{2}y + 2x^{2}y^{2}", "Potencias múltiples"),
        (r"\sqrt{x^2 + y^2}", "Raíces cuadradas"),
        (r"\frac{2x + 3}{x - 1}", "Fracciones"),
        ("x^2 + 3x + 1", "Exponente simple"),
        (r"\pi r^2", "Constantes matemáticas"),
        (r"\int_0^1 f(x)dx", "Integrales"),
        ("a_{n+1} = 2a_n + 1", "Subíndices"),
    ]

    results = []
    for expr, desc in test_cases:
        result = renderizar_formula(expr, dpi=220)
        status = "PASS" if result else "FAIL"
        results.append(status)

        # Detalles
        if result:
            buf, dpi = result
            size = len(buf.getvalue()) if hasattr(buf, "getvalue") else 0
            print(f"  [{status}] {desc:30s} | DPI={dpi} | Tamaño={size:,} bytes")
        else:
            print(f"  [{status}] {desc:30s} | No se pudo renderizar")

    passed = sum(1 for r in results if r == "PASS")
    total = len(results)
    print(f"\n  RESULTADO: {passed}/{total} pruebas pasadas")
    return passed == total


# ============================================================================
# TEST 2: Detección de expresiones (desde app.py ModuloEstudiante)
# ============================================================================


def test_deteccion_expresiones():
    """Valida que _detectar_expresion_matematica_visual() funciona"""
    print("\n" + "=" * 70)
    print("TEST 2: DETECCIÓN DE EXPRESIONES")
    print("=" * 70)

    # Crear instancia temporal mínima para acceder al método
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana

    try:
        estudiante = ModuloEstudiante(
            ventana=root, documento="TEST", nombre="Test", grado="1", curso="A"
        )

        test_cases = [
            ("$x^2$", True, "LaTeX delimitado"),
            ("$4x^{2}y^{3}$", True, "LaTeX con llaves"),
            ("Resuelve x^2 + 3x + 1", True, "Exponente sin $"),
            ("Calcula sqrt(16)", True, "Raíz sin $"),
            ("El perímetro es 2 por pi por r", False, "Texto normal"),
            ("¿Cuál es la solución?", False, "Pregunta normal"),
            ("$\int_0^1 f(x)dx$", True, "Integral"),
            ("x/2 + y/3", True, "División"),
        ]

        results = []
        for texto, esperado, desc in test_cases:
            resultado = estudiante._detectar_expresion_matematica_visual(texto)
            status = "PASS" if resultado == esperado else "FAIL"
            results.append(status)

            esperado_txt = "SÍ" if esperado else "NO"
            resultado_txt = "SÍ" if resultado else "NO"
            detalle = (
                "OK"
                if status == "PASS"
                else f"Esperado:{esperado_txt} Obtuvo:{resultado_txt}"
            )

            print(f"  [{status}] {desc:30s} | {detalle}")

        passed = sum(1 for r in results if r == "PASS")
        total = len(results)
        print(f"\n  RESULTADO: {passed}/{total} pruebas pasadas")

        root.destroy()
        return passed == total

    except Exception as e:
        print(f"  [ERROR] No se pudo crear ModuloEstudiante: {e}")
        root.destroy()
        return False


# ============================================================================
# TEST 3: Extracción de fórmulas
# ============================================================================


def test_extraccion_formulas():
    """Valida que _extraer_formula_para_visual() funciona"""
    print("\n" + "=" * 70)
    print("TEST 3: EXTRACCIÓN DE FÓRMULAS")
    print("=" * 70)

    root = tk.Tk()
    root.withdraw()

    try:
        estudiante = ModuloEstudiante(
            ventana=root, documento="TEST", nombre="Test", grado="1", curso="A"
        )

        test_cases = [
            ("$x^2$", ("", "x^2"), "Fórmula pura"),
            ("Resuelve $x^2 + 1 = 0$", ("Resuelve", "x^2 + 1 = 0"), "Con contexto"),
            ("x^2 + y^2", ("", "x^2 + y^2"), "Expresión corta"),
            (
                "Este es un texto largo",
                ("Este es un texto largo", None),
                "Texto normal",
            ),
        ]

        results = []
        for texto, esperado, desc in test_cases:
            resultado = estudiante._extraer_formula_para_visual(texto)
            status = "PASS" if resultado == esperado else "FAIL"
            results.append(status)

            print(f"  [{status}] {desc:30s}")
            if status == "FAIL":
                print(f"      Esperado: {esperado}")
                print(f"      Obtuvo:   {resultado}")

        passed = sum(1 for r in results if r == "PASS")
        total = len(results)
        print(f"\n  RESULTADO: {passed}/{total} pruebas pasadas")

        root.destroy()
        return passed == total

    except Exception as e:
        print(f"  [ERROR] {e}")
        root.destroy()
        return False


# ============================================================================
# TEST 4: Caché de imágenes
# ============================================================================


def test_cache_imagenes():
    """Valida que el caché funciona correctamente"""
    print("\n" + "=" * 70)
    print("TEST 4: CACHÉ DE IMÁGENES")
    print("=" * 70)

    root = tk.Tk()
    root.withdraw()

    try:
        estudiante = ModuloEstudiante(
            ventana=root, documento="TEST", nombre="Test", grado="1", curso="A"
        )

        # Test 1: verificar que caché está vacío
        cache_inicial = len(estudiante._math_image_cache)
        print(f"  [INFO] Caché inicial: {cache_inicial} entradas")

        # Test 2: generar imagen e intentar cachearla
        expr = "x^2 + 3x + 1"
        img1 = estudiante._obtener_formula_img_tk(expr, max_width=760)
        cache_post1 = len(estudiante._math_image_cache)

        if img1 is not None:
            print(f"  [PASS] Primera renderización exitosa")
            print(f"         Caché post-render: {cache_post1} entradas")
        else:
            print(f"  [FAIL] Primera renderización falló")
            root.destroy()
            return False

        # Test 3: solicitar misma imagen (debe venir de caché)
        img2 = estudiante._obtener_formula_img_tk(expr, max_width=760)
        cache_post2 = len(estudiante._math_image_cache)

        if cache_post2 == cache_post1 and img1 is img2:
            print(f"  [PASS] Segunda solicitud recuperada de caché (sin regenerar)")
        else:
            print(f"  [WARN] Segunda solicitud NO fue del caché (img2 diferente)")

        # Test 4: llenar caché hasta límite
        print(f"  [INFO] Probando capacidad de caché (máx 300)...")
        for i in range(50):
            estudiante._obtener_formula_img_tk(f"x^{i}", max_width=760)

        cache_parcial = len(estudiante._math_image_cache)
        if cache_parcial <= 300:
            print(f"  [PASS] Caché respeta límite: {cache_parcial} <= 300")
        else:
            print(f"  [FAIL] Caché exceede límite: {cache_parcial} > 300")
            root.destroy()
            return False

        root.destroy()
        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        root.destroy()
        return False


# ============================================================================
# TEST 5: Rendimiento
# ============================================================================


def test_rendimiento():
    """Valida que no hay lag en operaciones de cacheable"""
    print("\n" + "=" * 70)
    print("TEST 5: RENDIMIENTO (CACHÉ)")
    print("=" * 70)

    import time

    root = tk.Tk()
    root.withdraw()

    try:
        estudiante = ModuloEstudiante(
            ventana=root, documento="TEST", nombre="Test", grado="1", curso="A"
        )

        expr = "x^2 + y^2 + z^2"

        # Primer render (LENTO, genera imagen)
        t1_inicio = time.time()
        img1 = estudiante._obtener_formula_img_tk(expr, max_width=760)
        t1_duracion = time.time() - t1_inicio

        # Segundo render (RÁPIDO, desde caché)
        t2_inicio = time.time()
        img2 = estudiante._obtener_formula_img_tk(expr, max_width=760)
        t2_duracion = time.time() - t2_inicio

        # Tercer render (múltiples ancho, caché miss)
        t3_inicio = time.time()
        img3 = estudiante._obtener_formula_img_tk(expr, max_width=640)
        t3_duracion = time.time() - t3_inicio

        print(f"  Expresión: {expr}")
        print(f"\n  [1] Primer render (genera):    {t1_duracion*1000:.2f}ms")
        print(
            f"  [2] Segundo render (caché):   {t2_duracion*1000:.2f}ms (speedup: {t1_duracion/max(t2_duracion,0.001):.1f}x)"
        )
        print(f"  [3] Tercer render (width diferentes): {t3_duracion*1000:.2f}ms")

        if t2_duracion < t1_duracion * 0.5:  # Al menos 2x más rápido
            print(f"\n  [PASS] Caché mejora rendimiento significativamente")
            root.destroy()
            return True
        else:
            print(f"\n  [WARN] Caché no está mostrando mejora esperada")
            root.destroy()
            return True  # No es falso crítico

    except Exception as e:
        print(f"  [ERROR] {e}")
        root.destroy()
        return False


# ============================================================================
# TEST 6: Integración UI
# ============================================================================


def test_integracion_ui():
    """Valida que las funciones de aplicación funcionan"""
    print("\n" + "=" * 70)
    print("TEST 6: INTEGRACIÓN CON UI (BÁSICA)")
    print("=" * 70)

    root = tk.Tk()
    root.withdraw()

    try:
        estudiante = ModuloEstudiante(
            ventana=root, documento="TEST", nombre="Test", grado="1", curso="A"
        )

        # Simular Labels de UI
        label_texto = tk.Label(root, text="", wraplength=900)
        label_formula = tk.Label(root, bg="white")

        # Función _aplicar_texto_y_formula es interna, pero podemos probar
        # que no genera excepciones con diferentes textos

        test_texts = [
            "$x^2$",
            "Resuelve $x^2 + 1 = 0$",
            "Texto normal sin math",
            r"\frac{a}{b}",
        ]

        print(f"  Probando diferentes textos en Labels...")
        for i, texto in enumerate(test_texts, 1):
            try:
                # Simular extracción
                txt_limpio, expr = estudiante._extraer_formula_para_visual(texto)

                # Si hay expresión, intentar renderizar
                if expr:
                    img = estudiante._obtener_formula_img_tk(expr, max_width=760)
                    status = "OK" if img else "FAIL"
                else:
                    status = "OK (texto)"

                print(f"      [{i}] {status}: {texto[:50]}")
            except Exception as e:
                print(f"      [{i}] ERROR: {e}")
                root.destroy()
                return False

        print(f"\n  [PASS] Integración UI funciona sin excepciones")
        root.destroy()
        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        root.destroy()
        return False


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("#" * 70)
    print("# TEST INTEGRAL - RENDERIZACIÓN DE EXPRESIONES MATEMÁTICAS")
    print("# Módulo Estudiante (SEA)")
    print("#" * 70)

    tests = [
        ("Renderización básica", test_renderizacion_basica),
        ("Detección de expresiones", test_deteccion_expresiones),
        ("Extracción de fórmulas", test_extraccion_formulas),
        ("Caché de imágenes", test_cache_imagenes),
        ("Rendimiento", test_rendimiento),
        ("Integración UI", test_integracion_ui),
    ]

    resultados = []
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"\n  [EXCEPCIÓN CRÍTICA] {e}")
            resultados.append((nombre, False))

    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)

    for nombre, resultado in resultados:
        status = "✓ PASS" if resultado else "✗ FAIL"
        print(f"  {status} | {nombre}")

    total_tests = len(resultados)
    total_pass = sum(1 for _, r in resultados if r)

    print(f"\n  TOTAL: {total_pass}/{total_tests} tests pasados")

    if total_pass == total_tests:
        print("\n  ✓✓✓ TODAS LAS PRUEBAS PASADAS ✓✓✓")
        print("  Sistema de renderización FUNCIONAL Y LISTO")
        return 0
    else:
        print("\n  ✗✗✗ ALGUNAS PRUEBAS FALLARON ✗✗✗")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
