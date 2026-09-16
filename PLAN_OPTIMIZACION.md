# PLAN DE OPTIMIZACIÓN — DulceDetalle

> Cómo usar este archivo: cada paso es independiente y termina con un **check de validación**.
> Si se corta la sesión, un nuevo motor de IA puede continuar desde el primer paso sin `[x]`.
> Comandos siempre desde `dulce_detalle/`: `..\env\Scripts\python.exe manage.py <cmd>`.

## Estado base (working tree, SIN commitear)

Ya implementados antes de este plan (no rehacer, solo verificar):
- [x] `Procfile`: `gunicorn ... --workers 2 --threads 4 --max-requests 1000 --max-requests-jitter 100`
- [x] Índices compuestos en `app/models.py` + migración sin aplicar `app/migrations/0030_performance_indexes.py`
  (Producto: negocio+stock/categoria/subcategoria · Venta: negocio+fecha/creado · Pedido: negocio+estado/creado · EventoAnalytics: negocio+tipo+fecha)
- [x] Carrito por lotes: `get_carrito_detalle` y `get_carrito_publico_detalle` usan `in_bulk` (sin N+1)
- [x] Menú sin consultas repetidas: `_contexto_base` anota `_pedidos_pendientes_count`; `Negocio.pedidos_pendientes_count` lo respeta

Resultado por paso (checks):
- [x] **Paso 1 — Refactor SQL de estadísticas** (2026-09-11)
  Validado: `manage.py check` OK; en shell con DB real:
  `mes` → cantidad 1 / total 5600 / ganancia 3200 / gastos 2400
  coincide con consultas directas (Sum/Count/ExpressionWrapper). Sin vuelta a iterar en Python.
- [x] **Paso 2 — Caché corta de notificaciones** (2026-09-11)
  Validado: `manage.py check` OK. Con Client autenticado: 2ª petición = 0 consultas `notificacion`;
  tras `cache.clear()` vuelven a ejecutarse (2). TTL 60 s.
- [x] **Paso 3 — Paginación (productos, ventas, pedidos)** (2026-09-11)
  Validado: `manage.py check` OK. Con Client autenticado:
  - productos (616) → barra visible, contador muestra 616; `?q=chocolate` → 1 resultado y barra oculta.
  - ventas con `?movimiento=venta` → enlaces `?movimiento=venta&page=2` (filtros preservados).
  - pedidos sin warning de orden; se agregó `.order_by('-creado')` a `get_pedidos`.
  - páginas 1/2 con contenido distinto.
- [x] **Paso 4 — Miniaturas Cloudinary en ventas / pedidos / checkout** (2026-09-11)
  Validado: `manage.py check` OK. Render con Client (slug mango-accesorio):
  `ventas/` 200, `ventas/nueva/` 200 (thumb en resumen de orden), `pedidos/` 200,
  `/tienda/checkout/` 200 con ítem en carrito. El tag es no-op en archivos locales
  (devuelve la misma URL) y aplica `w,h,c_fill,q_auto,f_auto` en Cloudinary.
- [x] **Paso 5 — Validación final** (2026-09-11)
  Validado: `migrate` aplicó `0030_performance_indexes` OK; `manage.py check` sin issues;
  `manage.py test` corre (0 tests, esperado). Smoke test con Client (slug mango-accesorio):
  productos, productos?page=3, ventas (con filtros combinados), pedidos, estadisticas,
  calculadora, notas, tienda pública autenticada y anónima → todas 200.
  Revisión de `git diff`: sin regresiones en las vistas; agregados se calculan antes de paginar.

## Paso 1 — Refactor SQL de `get_resumen_estadisticas`

- **Archivo**: `dulce_detalle/app/services.py` (función desde ~línea 403).
- **Qué**: eliminar la carga completa de `ventas`+`productos` en Python. Reemplazar por agregados SQL
  usando `Sum`, `Count`, `F`, `ExpressionWrapper(DecimalField)`, `ExtractYear/ExtractMonth`.
  La salida debe ser EXACTAMENTE la misma estructura de dict:
  `hoy`, `semana`, `mes` (cada uno: `total`, `ganancia`, `gastos`, `cantidad`),
  `grafico_labels`, `grafico_gastos`, `grafico_ganancias`, `visitas_semana`,
  `pedidos_online_semana`, `top_busquedas`, `top_clicks`.
- **Fórmulas que replicar** (no cambiar la semántica):
  - `total` = `Sum(Venta.total)` del periodo (incluye compras de stock con total negativo).
  - `cantidad` = `Count(Venta)` del periodo.
  - `ganancia` = `Sum(ItemVenta.cantidad * (precio_unitario - costo_unitario))` de las ventas del periodo.
  - `gastos_ventas` = `total - ganancia`.
  - `gastos_inventario` = `Sum(Producto.costo * Producto.stock)` según fecha de creación del producto:
    hoy → `creado__date=hoy`; semana → `creado__date__gte=inicio_semana`; mes → `creado__date__gte=inicio_mes`.
  - `gastos` = `gastos_ventas + gastos_inventario`.
  - Gráfico 6 meses: etiquetas como el original (i en 5..0, mes anterior → año previo si m<=0).
    Agrupar ventas por `(year, month)` de `Venta.fecha` y productos por `(year, month)` de `Producto.creado`.
- **Validación**: `..\env\Scripts\python.exe manage.py check`.
  Si la base está disponible, correr en `manage.py shell` la función vieja vs nueva y comparar dicts.

## Paso 2 — Caché corta de notificaciones

- **Archivo**: `dulce_detalle/app/context_processors.py` (`notificaciones_info`).
- **Qué**: envolver la consulta con `django.core.cache.cache`. TTL 60 s. Clave `notif:{user.pk}`.
  Guardar la lista ya evaluada (`list(notifs)`) + `count`. Si no hay cache configurada usa LocMemCache (por proceso, aceptable).
- **Validación**: `manage.py check`; revisar que una petición autenticada haga una sola consulta de notificaciones
  (varias peticiones en 60 s → cacheada).

## Paso 3 — Paginación (productos, ventas, pedidos)

- **Archivos nuevos**:
  - `dulce_detalle/app/templatetags/paginacion_tags.py` — tag `url_replace` (copia `request.GET`, cambia el parámetro `page`, devuelve querystring).
  - `dulce_detalle/app/templates/includes/paginacion.html` — barra de paginación reutilizable, estilo oscuro del sidebar
    (Prev / números con elipsis / Next). Recibe `page_obj` y `page_range` (con `get_elided_page_range`).
- **Archivos a modificar**: `app/views.py` y `listed templates`.
  - `lista_productos` (línea ~122): calcular `valor_inventario` y totales ANTES de paginar.
    `per_page=30`. Pasar `productos` (objeto `Page`) y `page_range`. En `productos/lista.html`
    cambiar `{{ productos.count }}` → `{{ productos.paginator.count }}` y añadir el include.
  - `lista_ventas` (línea ~534): paginar tras los filtros. `per_page=25`. `{% if not ventas %}` sigue
    funcionando (Page implementa `__len__`). Añadir include; el tag `url_replace` preserva `fecha/metodo/tipo/movimiento`.
  - `lista_pedidos` (línea ~1042): paginar. `per_page=20`. Reemplazar `{{ pedidos|length }}`
    (cuenta de página) por `{{ pedidos.paginator.count }}`.
    Evitar COUNT duplicado de pendientes: usar `getattr(negocio, '_pedidos_pendientes_count', None)` antes de
    `get_pedidos_pendientes_count`.
- **Validación**: `manage.py check`; navegar manualmente con `?page=2` y filtros activos
  (los enlaces de paginación deben conservarlos).

## Paso 4 — Miniaturas Cloudinary en ventas / pedidos / checkout

- **Archivos**: `app/templates/ventas/lista.html` (línea ~252), `ventas/crear.html` (~309),
  `pedidos/lista.html` (~94), `tienda_publica/checkout.html` (~35).
- **Qué**: añadir `{% load imagen_tags %}` donde falte y cambiar `{{ X.imagen.url }}`
  por `{% cloudinary_thumb X.imagen W H %}` (W/H según el uso: 96–128 en miniaturas).
  No tocar logos ni la galería embebida en JS de `tienda_publica/index.html`.
- **Validación**: `manage.py check`; revisar visualmente (o verificar el URL generado con Cloudinary configurado).

## Paso 5 — Validación final

- Ejecutar desde `dulce_detalle/`:
  - `..\env\Scripts\python.exe manage.py check`
  - `..\env\Scripts\python.exe manage.py migrate` (aplica migración 0030; requiere Postgres local o `DATABASE_URL`)
  - `..\env\Scripts\python.exe manage.py test` (boilerplate vacío, pero confirma que importa)
- Revisar `git diff` completo; NO commitear salvo pedido explícito.

## Fuera de alcance (por ahora)

- **Tailwind compilado**: no hay toolchain de build en el repo y la paleta es dinámica por negocio;
  se requeriría Tailwind v4 daisyUI/standalone + safelist. Posponer.
- **Carga diferida de galería en tienda pública**: requiere cambios en JS/subidas; posponer.
- **Analíticas en segundo plano**: requiere infraestructura (queue/celery o endpoint separado); posponer.
- **Métricas de rendimiento (CWV, nº queries)**: posponer a después de la validación.