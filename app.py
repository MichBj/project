from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
# Usar una variable de entorno o una clave más segura en producción
app.secret_key = 'tu_clave_secreta' 

# Configuración de MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',  # Reemplaza con tu usuario de MySQL
    'password': '1230',  # Reemplaza con tu contraseña de MySQL
    'database': 'PG'  # Nombre de la base de datos
}

# Función para conectar a MySQL
def get_db_connection():
    try:
        # Usa el método get_db_connection() en todas las rutas para asegurar que la conexión se abre y se cierra correctamente
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        # En caso de fallo en la conexión, se muestra el error en la terminal
        flash(f"Error de conexión a la base de datos: {e}", 'danger')
        return None

# Ruta principal (Ahora muestra la nueva página de inicio)
@app.route('/')
def index():
    return render_template('index.html') 
# Crear Producto
@app.route('/crear', methods=['GET', 'POST'])
def crear():
    connection = None
    cursor = None
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']

        # Validar campos vacíos
        if not nombre or not precio or not stock:
            flash('Todos los campos son obligatorios!', 'danger')
            return render_template('formulario.html', action='Crear', product=None)

        try:
            precio = float(precio)
            stock = int(stock)
            if precio < 0 or stock < 0:
                flash('El precio y el stock no pueden ser negativos!', 'danger')
                return render_template('formulario.html', action='Crear', product=None)

            connection = get_db_connection()
            if connection is None:
                return redirect(url_for('productos'))

            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)',
                (nombre, precio, stock)
            )
            connection.commit()
            flash('Producto creado exitosamente!', 'success')
            return redirect(url_for('productos'))
        
        except ValueError:
            flash('El precio y el stock deben ser números válidos.', 'danger')
        except Error as e:
            # Captura errores específicos de MySQL (duplicados, etc.)
            flash(f'Error al crear producto en DB: {e}', 'danger')
        except Exception as e:
            # Captura cualquier otro error
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        
        finally:
            # Asegura que el cursor y la conexión se cierren, incluso si hubo un error en la conexión/cursor
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    # Si es GET o si hubo un error de validación/DB, muestra el formulario
    return render_template('formulario.html', action='Crear', product=None)

# Leer Productos
@app.route('/productos')
def productos():
    connection = get_db_connection()
    if connection is None:
        return render_template('productos.html', productos=[])

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM productos')
        productos = cursor.fetchall()
        return render_template('productos.html', productos=productos)
    except Error as e:
        flash(f'Error al cargar productos: {e}', 'danger')
        return render_template('productos.html', productos=[])
    finally:
        cursor.close()
        connection.close()

# Actualizar Producto
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    connection = get_db_connection()
    if connection is None:
        return redirect(url_for('productos'))

    cursor = connection.cursor(dictionary=True)
    product = None
    try:
        cursor.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
        product = cursor.fetchone()

        if not product:
            flash('Producto no encontrado!', 'danger')
            return redirect(url_for('productos'))
    
    except Error as e:
        flash(f'Error al buscar producto: {e}', 'danger')
        return redirect(url_for('productos'))
    finally:
        # La conexión se mantiene abierta para el POST o se cierra en el GET si hay error.
        pass

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']

        if not nombre or not precio or not stock:
            flash('Todos los campos son obligatorios!', 'danger')
            return render_template('formulario.html', action='Editar', product=product)

        try:
            precio = float(precio)
            stock = int(stock)
            if precio < 0 or stock < 0:
                flash('El precio y el stock no pueden ser negativos!', 'danger')
                return render_template('formulario.html', action='Editar', product=product)

            cursor.execute(
                'UPDATE productos SET nombre = %s, precio = %s, stock = %s WHERE id_producto = %s',
                (nombre, precio, stock, id)
            )
            connection.commit()
            flash('Producto actualizado exitosamente!', 'success')
            return redirect(url_for('productos'))
        
        except ValueError:
            flash('El precio y el stock deben ser números válidos.', 'danger')
        except Error as e:
            flash(f'Error al actualizar producto en DB: {e}', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Cierre de conexión para el método GET exitoso
    cursor.close()
    connection.close()
    return render_template('formulario.html', action='Editar', product=product)

# Eliminar Producto
@app.route('/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar(id):
    connection = get_db_connection()
    if connection is None:
        return redirect(url_for('productos'))

    cursor = connection.cursor(dictionary=True)
    product = None
    try:
        cursor.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
        product = cursor.fetchone()

        if not product:
            flash('Producto no encontrado!', 'danger')
            return redirect(url_for('productos'))

        if request.method == 'POST':
            # Solo se ejecuta DELETE si el método es POST (confirmación)
            cursor.execute('DELETE FROM productos WHERE id_producto = %s', (id,))
            connection.commit()
            flash('Producto eliminado exitosamente!', 'success')
            return redirect(url_for('productos'))
        
    except Error as e:
        flash(f'Error al operar en DB: {e}', 'danger')
    except Exception as e:
        flash(f'Ocurrió un error inesperado: {e}', 'danger')
    
    finally:
        # Cierre de conexión después del POST o GET
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    # Si es GET (para mostrar el formulario de confirmación de eliminación)
    return render_template('formulario.html', action='Eliminar', product=product)

if __name__ == '__main__':
    # Nota: Si usas la terminal integrada de VS Code, usa host='0.0.0.0' para acceder desde el navegador.
    app.run(debug=True, host='0.0.0.0')
