# Instrucciones para completar la implementación de imágenes

## Estado actual
✅ Dependencias instaladas (multer, @supabase/supabase-js)
✅ Variables de entorno agregadas al .env local
✅ Script de migración de base de datos creado (backend/add-imagenes-column.js)
✅ Formulario HTML actualizado con campo de imágenes
✅ Estilos CSS agregados
✅ JavaScript del frontend actualizado para manejar imágenes

## Pasos pendientes

### 1. Agregar variables de entorno en Railway

Ve a Railway → formulario-pagos → Variables y agrega:

```
SUPABASE_URL=https://jkbmiuihyrigddvkydpx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprYm1pdWloeXJpZ2Rkdmt5ZHB4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NDYxNDAsImV4cCI6MjA4MDAyMjE0MH0.kT8R92SWA24BFOo227fXNbep606uEy0pt3xW44TG5Dw
SUPABASE_STORAGE_BUCKET=gastos-imagenes
```

### 2. Ejecutar migración de base de datos en Railway

Opción A - Usando Railway CLI:
```bash
railway run node backend/add-imagenes-column.js
```

Opción B - Ejecutar SQL manualmente en la consola de PostgreSQL de Railway:
```sql
ALTER TABLE pagos ADD COLUMN IF NOT EXISTS imagenes TEXT[];
```

### 3. Crear bucket en Supabase Storage

1. Ve a https://supabase.com/dashboard/project/jkbmiuihyrigddvkydpx/storage/buckets
2. Click en "New bucket"
3. Nombre: `gastos-imagenes`
4. **IMPORTANTE**: Marcar como "Public bucket" para que las URLs sean accesibles
5. Click en "Create bucket"

### 4. Configurar políticas de acceso en Supabase

Ve a Storage → gastos-imagenes → Policies y crea estas políticas:

**Política 1: Allow public read access**
```sql
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'gastos-imagenes' );
```

**Política 2: Allow authenticated uploads**
```sql
CREATE POLICY "Authenticated uploads"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'gastos-imagenes' );
```

### 5. Modificar backend/server-pg.js

Agregar al inicio del archivo (después de los requires existentes):

```javascript
const multer = require('multer');
const { createClient } = require('@supabase/supabase-js');

// Configurar Supabase
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

// Configurar multer para manejar uploads en memoria
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB
    files: 5
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Solo se permiten imágenes'), false);
    }
  }
});
```

### 6. Modificar el endpoint POST /api/pagos

Reemplazar la línea:
```javascript
app.post('/api/pagos', requireAuth, async (req, res) => {
```

Por:
```javascript
app.post('/api/pagos', requireAuth, upload.array('imagenes', 5), async (req, res) => {
```

Y modificar el contenido de la función para manejar imágenes:

```javascript
app.post('/api/pagos', requireAuth, upload.array('imagenes', 5), async (req, res) => {
  try {
    // Extraer datos del body
    let locales, proveedor, fechaPago, fechaServicio, moneda, concepto, importe, observacion;

    // Si hay archivos, los datos vienen como strings en req.body
    if (req.files && req.files.length > 0) {
      locales = JSON.parse(req.body.locales);
      proveedor = req.body.proveedor;
      fechaPago = req.body.fechaPago;
      fechaServicio = req.body.fechaServicio;
      moneda = req.body.moneda;
      concepto = req.body.concepto;
      importe = req.body.importe;
      observacion = req.body.observacion;
    } else {
      // Sin archivos, viene como JSON normal
      ({ locales, proveedor, fechaPago, fechaServicio, moneda, concepto, importe, observacion } = req.body);
    }

    const usuario = req.session.user.username;

    // ... (mantener todas las validaciones existentes) ...

    // Array para almacenar URLs de imágenes subidas
    const imagenesUrls = [];

    // Subir imágenes a Supabase Storage si existen
    if (req.files && req.files.length > 0) {
      for (const file of req.files) {
        const fileName = `${Date.now()}-${Math.random().toString(36).substring(7)}-${file.originalname}`;
        const filePath = `gastos/${fileName}`;

        const { data, error } = await supabase.storage
          .from(process.env.SUPABASE_STORAGE_BUCKET)
          .upload(filePath, file.buffer, {
            contentType: file.mimetype,
            cacheControl: '3600',
            upsert: false
          });

        if (error) {
          console.error('Error al subir imagen a Supabase:', error);
          continue; // Continuar con las demás imágenes
        }

        // Obtener URL pública
        const { data: publicData } = supabase.storage
          .from(process.env.SUPABASE_STORAGE_BUCKET)
          .getPublicUrl(filePath);

        imagenesUrls.push(publicData.publicUrl);
      }
    }

    // Array para almacenar los IDs de pagos creados
    const pagoIds = [];

    // Insertar un pago para cada local (modificar el SQL para incluir imagenes)
    const insertPagoSQL = `
      INSERT INTO pagos (local, proveedor, fecha_pago, fecha_servicio, moneda, concepto, importe, observacion, usuario_registro, imagenes)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING id
    `;

    for (const local of locales) {
      const result = await db.query(insertPagoSQL, [
        local,
        proveedor,
        fechaPago,
        fechaServicio,
        moneda,
        concepto,
        importePorLocal,
        observacion || '',
        usuario,
        imagenesUrls.length > 0 ? imagenesUrls : null  // Guardar array de URLs
      ]);

      const pagoId = result.rows[0].id;
      pagoIds.push(pagoId);
      console.log(`Gasto registrado con ID: ${pagoId} para local ${local} por ${usuario}`);
    }

    // ... (código del email - continúa abajo) ...
```

### 7. Modificar el HTML del email para incluir imágenes

En la sección donde se prepara el email, agregar antes del cierre del HTML:

```javascript
    // Agregar imágenes al email si existen
    let imagenesHTML = '';
    if (imagenesUrls.length > 0) {
      imagenesHTML = `
        <h3 style="color: #4f46e5; margin-top: 30px; margin-bottom: 15px;">Imágenes Adjuntas</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-top: 16px;">
          ${imagenesUrls.map(url => `
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
              <img src="${url}" alt="Imagen del gasto" style="width: 100%; height: 200px; object-fit: cover;">
            </div>
          `).join('')}
        </div>
      `;
    }

    const htmlContent = `
      <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        ... (mantener todo el HTML existente) ...

        ${imagenesHTML}

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">

        <p style="color: #6b7280; font-size: 14px; text-align: center;">
          <em>Registro generado automáticamente el ${new Date().toLocaleString('es-ES')}</em>
        </p>
      </div>
    `;
```

### 8. Actualizar historial.js para mostrar imágenes

En la función `renderPagos`, agregar después de mostrar los detalles del pago:

```javascript
// Mostrar imágenes si existen
let imagenesHTML = '';
if (pago.imagenes && pago.imagenes.length > 0) {
  imagenesHTML = `
    <div style="margin-top: 16px;">
      <h5 style="margin: 0 0 12px 0; color: #4f46e5;">Imágenes:</h5>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px;">
        ${pago.imagenes.map(url => `
          <a href="${url}" target="_blank" style="display: block; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <img src="${url}" alt="Imagen del gasto" style="width: 100%; height: 150px; object-fit: cover;">
          </a>
        `).join('')}
      </div>
    </div>
  `;
}
```

Y agregarlo dentro del `detailRow.innerHTML` en la sección de detalles.

### 9. Commit y deploy

```bash
git add .
git commit -m "Implementar subida de imágenes con Supabase Storage"
git push origin main
```

Railway desplegará automáticamente los cambios.

## Pruebas

1. Intenta registrar un gasto con 1-3 imágenes
2. Verifica que las imágenes aparezcan en la vista previa
3. Confirma el envío
4. Verifica que el email incluya las imágenes
5. Revisa el historial y verifica que las imágenes se muestren
6. Haz click en una imagen en el historial para verla en tamaño completo

## Solución de problemas

- **Error al subir imágenes**: Verifica que el bucket sea público en Supabase
- **Imágenes no se ven**: Verifica las políticas de acceso en Supabase Storage
- **Error 413 Payload Too Large**: Verifica que las imágenes no excedan 5MB
- **Error de conexión a Supabase**: Verifica las variables de entorno en Railway
