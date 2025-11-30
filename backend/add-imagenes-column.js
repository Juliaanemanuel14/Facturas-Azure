require('dotenv').config();
const db = require('./db');

async function addImagenesColumn() {
  try {
    console.log('Agregando columna imagenes a la tabla pagos...');

    // Agregar columna imagenes como TEXT[] (array de texto)
    const alterTableSQL = `
      ALTER TABLE pagos
      ADD COLUMN IF NOT EXISTS imagenes TEXT[];
    `;

    await db.query(alterTableSQL);

    console.log('✓ Columna imagenes agregada exitosamente');
    console.log('La columna almacenará un array de URLs de imágenes de Supabase Storage');

    process.exit(0);
  } catch (error) {
    console.error('Error al agregar columna imagenes:', error);
    process.exit(1);
  }
}

addImagenesColumn();
