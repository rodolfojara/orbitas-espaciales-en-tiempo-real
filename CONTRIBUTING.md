# Contribuir a Órbitas Espaciales en Tiempo Real

¡Gracias por tu interés en contribuir!

## Cómo empezar

1. Haz fork del repositorio.
2. Clona tu fork: `git clone https://github.com/tu-usuario/orbitas-espaciales-en-tiempo-real.git`
3. Crea un entorno virtual: `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
4. Instala dependencias: `pip install -e . && pip install pytest`
5. Crea una rama: `git checkout -b mi-feature`

## Ejecutar tests

```bash
python tests/test_basic.py
# o con pytest:
pytest
```

## Ejecutar ejemplos

```bash
python examples/run_demo.py
python examples/run_leo_ground_track.py
python examples/run_orbit3d.py
```

## Estilo de código

- Python 3.9+.
- Seguir PEP 8.
- Docstrings en funciones públicas.
- Type hints recomendados.
- Commits en español o inglés, descriptivos.

## Pull Requests

1. Asegúrate de que los tests pasen.
2. Actualiza el README si agregas funcionalidad nueva.
3. Describe claramente qué cambia y por qué.

## Reportar bugs

Abre un issue en GitHub con:
- Descripción del problema.
- Pasos para reproducir.
- Versión de Python y sistema operativo.

## Licencia

Al contribuir, aceptas que tu código se licencie bajo MIT.