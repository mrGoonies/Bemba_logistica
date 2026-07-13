# Caminata Gemba — Logística

App para digitalizar el formulario de la caminata Gemba del área de Logística
(Patio exterior y Bodega 1, Seguridad, Bodega principal y Despacho),
reemplazando el papel y permitiendo detectar incidencias y generar reportes
semanales automáticamente.

## Stack

Django 6 · Tailwind CSS v4 · HTMX · Alpine.js · SQLite (desarrollo)

## Requisitos

- Python 3.12 y [uv](https://docs.astral.sh/uv/)
- Node.js (para compilar Tailwind)

## Puesta en marcha

```bash
uv sync
npm install
npm run build-css

cp .env.example .env   # y edita SECRET_KEY si vas a exponer el servidor

uv run manage.py migrate
uv run manage.py seed_demo     # crea usuarios y preguntas de ejemplo
uv run manage.py runserver
```

Abre http://127.0.0.1:8000 — el comando `seed_demo` imprime las credenciales
de acceso (una Jefatura y un Operador por cada área) y genera además 21 días
de caminatas de ejemplo para que el dashboard de reportes tenga datos.

Durante el desarrollo, para que los cambios de estilos se reflejen sin
recompilar a mano:

```bash
npm run watch-css
```

## Administración

Las preguntas y su criterio (contexto) de cada área, así como los usuarios y
el área que tiene asignada cada uno, se administran desde `/admin/`. Crea un
superusuario con:

```bash
uv run manage.py createsuperuser
```

## Roles

- **Operador**: solo ve y llena el formulario de la caminata del día para su
  área asignada.
- **Jefatura**: ve el dashboard de reportes consolidado de las 3 áreas
  (incidencias identificadas, solucionadas e incidencias abiertas por
  antigüedad), sin acceso al llenado del formulario.

Una incidencia (respuesta "No conforme" o "Parcial") se considera
solucionada automáticamente cuando esa misma pregunta, en una caminata
posterior de la misma área, se responde "Conforme" — no hay un botón manual
de resolución.

## Tests

```bash
uv run manage.py test
```

## Logo y marca

Los colores corporativos ya están cargados en
`static_src/src/styles.css` (`@theme`). Para agregar el logo, reemplaza el
ícono de `templates/base.html` (cabecera) y `templates/accounts/login.html`
por una imagen en `static/img/`.
