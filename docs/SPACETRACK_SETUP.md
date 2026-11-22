# Configuración de Space-Track.org

Space-Track.org es el catálogo oficial del Departamento de Defensa de EE.UU.
Es la fuente más autoritativa para elementos orbitales (TLE/GP).

## Registro (gratis)

1. Ir a https://www.space-track.org/
2. Crear cuenta (requiere email).
3. Confirmar el email.

## Configuración

Configurar las variables de entorno:

### Windows (PowerShell)
```powershell
$env:SPACETRACK_USER = "tu_email@example.com"
$env:SPACETRACK_PASS = "tu_contraseña"
```

### Linux/macOS
```bash
export SPACETRACK_USER="tu_email@example.com"
export SPACETRACK_PASS="tu_contraseña"
```

### Permanente (Windows)
Agregar a las variables de entorno del sistema:
- Panel de control → Sistema → Variables de entorno → Nueva.

## Verificación

```python
from orbitas_rt.spacetrack import is_configured, search_by_name
print(is_configured())  # True si está configurado
results, err = search_by_name("ISS")
print(results)  # lista de resultados
```

## Uso en el sistema

Una vez configurado, la búsqueda inteligente (`smart_search`) consulta Space-Track
automáticamente como tercera fuente, después de CelesTrak. Los resultados se
cross-referencian para detectar inconsistencias.

## Notas
- Space-Track tiene límites de uso (no hacer más de ~300 queries/hora).
- Los datos de Space-Track son los mismos que CelesTrak redistribuye, pero con
  más metadatos (país, tipo de objeto, tamaño RCS, etc.).
- La integración permite validar la frescura de los TLEs de CelesTrak.