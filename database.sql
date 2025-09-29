-- 1. Crear la Base de Datos 'PG' si no existe
CREATE DATABASE IF NOT EXISTS PG;

-- 2. Seleccionar la Base de Datos 'PG' para usarla
USE PG;

-- 3. Estructura de la tabla productos
CREATE TABLE IF NOT EXISTS productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL
);

