# Migraciones

Archivos numerados `NNNN_descripcion.sql`, aplicados en orden con `psql -v ON_ERROR_STOP=1`. Una migración mergeada es inmutable: corregir el esquema = nueva migración. CI las aplica contra Postgres real (imagen supabase/postgres) en cada PR que toque este directorio.
