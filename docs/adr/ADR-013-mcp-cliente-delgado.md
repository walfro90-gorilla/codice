# ADR-013 — MCP remoto como cliente delgado del API público

Estado: aceptada · Fecha: 2026-08-29

## Contexto

Queremos que asistentes de IA puedan consultar Códice sin alucinar sus datos: si un chat cita el sistema, debe citar fuente, fecha de captura y enlace al documento (R1, R10). Un servidor MCP con acceso directo a la base duplicaría lógica de consulta, abriría una segunda superficie de seguridad sobre Postgres y podría divergir del API en qué expone y cómo. Los datos son públicos, así que no hay caso de uso para acceso privilegiado.

## Decisión

El servidor MCP es un cliente delgado del API público de FastAPI: nunca habla directo a la base. Corre como Cloudflare Worker con transporte HTTP con streaming, y se publica en npm como paquete que corre local o apunta al remoto según variable de entorno. Expone solo 4 herramientas (`buscar_entidad`, `explicar_estructura`, `rastrear_dinero`, `consultar_fundamento_legal`), y cada respuesta incluye siempre la cita: fuente, fecha de captura y enlace al documento. Lleva rate limit desde el día uno y no requiere autenticación.

## Alternativas descartadas

- **MCP con acceso directo a Postgres**: duplica la lógica de consulta, expone la base a un cliente más y permite que el MCP devuelva datos que el API no publica — dos verdades divergentes.
- **Veinte herramientas granulares**: más superficie que mantener y peor experiencia para el modelo cliente; cuatro herramientas bien nombradas cubren los casos y caben en cualquier contexto.
- **Solo servidor local (stdio)**: obligaría a cada usuario a instalar y sincronizar datos; el remoto en Workers sirve a cualquiera al instante, y el paquete npm conserva la opción local.

## Consecuencias

El MCP hereda gratis todo lo que el API garantiza: read-only, `sources[]` en cada respuesta, y cualquier corrección de datos aplica a ambos canales sin trabajo extra. Los 100k requests/día del free tier de Workers alcanzan gracias al rate limit; un agente en bucle no tumba el servicio. La limitante es latencia doble (Worker → API → respuesta) y que el MCP no puede ofrecer nada que el API no exponga — lo cual es deliberado: presiona a que toda capacidad nueva entre primero por el contrato público.
