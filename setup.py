from setuptools import setup, find_packages

setup(
    name="proyecto_evaluacion",
    version="1.0.0",
    description="Sistema de Evaluación Automatizada",
    author="Robert Calanche Villa",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "numpy",
        "openpyxl",
        "Pillow",
        "reportlab",
        "qrcode[pil]",
        "pypdf",
        "opencv-python",
        "matplotlib",
        "Flask",
    ],
    entry_points={
        # si se define una función main en app.py, ajustar aquí
        # "console_scripts": ["evaluacion=app:main"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
