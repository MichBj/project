from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import os
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps  # For login_required decorator

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta')

db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '1230'),
    'database': os.environ.get('DB_NAME', 'PG')
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        flash(f"Error de conexión a la base de datos: {e}", 'danger')
        return None

# Decorador para rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username', ''))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Email y contraseña son obligatorios!', 'danger')
            return render_template('login.html')

        connection = get_db_connection()
        if connection is None:
            return render_template('login.html')

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT id_usuario, nombre_usuario, password FROM usuarios WHERE email = %s', (email,))
                user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id_usuario']
                session['username'] = user['nombre_usuario']
                flash(f'¡Bienvenido, {user["nombre_usuario"]}!', 'success')
                return redirect(url_for('productos'))
            else:
                flash('Email o contraseña incorrectos.', 'danger')
        except Error as e:
            flash(f'Error al verificar usuario: {e}', 'danger')
        finally:
            connection.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('login'))

@app.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']

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

            with connection.cursor() as cursor:
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
            flash(f'Error al crear producto en DB: {e}', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        finally:
            if 'connection' in locals() and connection:
                connection.close()
    
    return render_template('formulario.html', action='Crear', product=None)

@app.route('/productos')
@login_required
def productos():
    connection = get_db_connection()
    if connection is None:
        return render_template('productos.html', productos=[])

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM productos')
            productos = cursor.fetchall()
        return render_template('productos.html', productos=productos)
    except Error as e:
        flash(f'Error al cargar productos: {e}', 'danger')
        productos = []
    finally:
        if connection:
            connection.close()
    return render_template('productos.html', productos=productos)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    product = None
    connection = None
    cursor = None

    if request.method == 'GET':
        connection = get_db_connection()
        if connection is None:
            return redirect(url_for('productos'))

        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
                product = cursor.fetchone()
            if not product:
                flash('Producto no encontrado!', 'danger')
                return redirect(url_for('productos'))
        except Error as e:
            flash(f'Error al buscar producto: {e}', 'danger')
            return redirect(url_for('productos'))
        finally:
            if connection:
                connection.close()
        return render_template('formulario.html', action='Editar', product=product)

    nombre = request.form['nombre']
    precio = request.form['precio']
    stock = request.form['stock']

    if not nombre or not precio or not stock:
        connection = get_db_connection()
        if connection:
            try:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
                    product = cursor.fetchone()
            except Error:
                pass
            finally:
                if connection:
                    connection.close()
        flash('Todos los campos son obligatorios!', 'danger')
        return render_template('formulario.html', action='Editar', product=product)

    try:
        precio = float(precio)
        stock = int(stock)
        if precio < 0 or stock < 0:
            flash('El precio y el stock no pueden ser negativos!', 'danger')
            return render_template('formulario.html', action='Editar', product=product)

        connection = get_db_connection()
        if connection is None:
            return redirect(url_for('productos'))

        with connection.cursor() as cursor:
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
        if connection:
            connection.close()

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
                product = cursor.fetchone()
        finally:
            connection.close()
    return render_template('formulario.html', action='Editar', product=product)

@app.route('/eliminar/<int:id>', methods=['GET', 'POST'])
@login_required
def eliminar(id):
    product = None
    connection = get_db_connection()
    if connection is None:
        return redirect(url_for('productos'))

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
            product = cursor.fetchone()

        if not product:
            flash('Producto no encontrado!', 'danger')
            return redirect(url_for('productos'))

        if request.method == 'POST':
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM productos WHERE id_producto = %s', (id,))
            connection.commit()
            flash('Producto eliminado exitosamente!', 'success')
            return redirect(url_for('productos'))
    
    except Error as e:
        flash(f'Error al operar en DB: {e}', 'danger')
    except Exception as e:
        flash(f'Ocurrió un error inesperado: {e}', 'danger')
    finally:
        if connection:
            connection.close()

    return render_template('formulario.html', action='Eliminar', product=product)

@app.route('/crear_usuario', methods=['GET', 'POST'])
@login_required  # Restringido solo para usuarios logueados
def crear_usuario():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        email = request.form['email']
        password = request.form['password']

        if not nombre_usuario or not email or not password:
            flash('Todos los campos son obligatorios!', 'danger')
            return render_template('crear_usuario.html', user=None)

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('crear_usuario.html', user=None)

        try:
            hashed_password = generate_password_hash(password)
            connection = get_db_connection()
            if connection is None:
                return redirect(url_for('productos'))

            with connection.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO usuarios (nombre_usuario, email, password) VALUES (%s, %s, %s)',
                    (nombre_usuario, email, hashed_password)
                )
            connection.commit()
            flash('Usuario creado exitosamente!', 'success')
            return redirect(url_for('productos'))
        
        except mysql.connector.IntegrityError as e:
            if 'Duplicate entry' in str(e):
                flash('El email ya está registrado.', 'danger')
            else:
                flash(f'Error al crear usuario: {e}', 'danger')
        except Error as e:
            flash(f'Error en DB: {e}', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        finally:
            if 'connection' in locals() and connection:
                connection.close()
    
    return render_template('crear_usuario.html', user=None)

@app.route('/ventas')
@login_required
def ventas():
    connection = get_db_connection()
    if connection is None:
        return render_template('ventas.html', ventas=[])

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT v.id_venta, v.cantidad, v.fecha, v.total, p.nombre as producto_nombre, p.precio
                FROM ventas v JOIN productos p ON v.id_producto = p.id_producto
                ORDER BY v.fecha DESC
            """)
            ventas = cursor.fetchall()
        return render_template('ventas.html', ventas=ventas)
    except Error as e:
        flash(f'Error al cargar ventas: {e}', 'danger')
        ventas = []
    finally:
        if connection:
            connection.close()
    return render_template('ventas.html', ventas=ventas)

@app.route('/venta', methods=['GET', 'POST'])
@login_required
def venta():
    productos = []
    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT id_producto, nombre, precio, stock FROM productos WHERE stock > 0')
                productos = cursor.fetchall()
        except Error as e:
            flash(f'Error al cargar productos: {e}', 'danger')
        finally:
            connection.close()

    if request.method == 'POST':
        id_producto = int(request.form['id_producto'])
        cantidad = int(request.form['cantidad'])

        if cantidad <= 0:
            flash('La cantidad debe ser mayor a 0.', 'danger')
            return render_template('venta.html', productos=productos)

        try:
            connection = get_db_connection()
            if connection is None:
                return redirect(url_for('ventas'))

            with connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT precio, stock FROM productos WHERE id_producto = %s', (id_producto,))
                product = cursor.fetchone()
                if not product or product['stock'] < cantidad:
                    flash('Producto no encontrado o stock insuficiente.', 'danger')
                    return redirect(url_for('ventas'))

                total = product['precio'] * cantidad
                fecha = date.today()

                cursor.execute(
                    'INSERT INTO ventas (id_producto, cantidad, fecha, total) VALUES (%s, %s, %s, %s)',
                    (id_producto, cantidad, fecha, total)
                )

                new_stock = product['stock'] - cantidad
                cursor.execute(
                    'UPDATE productos SET stock = %s WHERE id_producto = %s',
                    (new_stock, id_producto)
                )

            connection.commit()
            flash(f'Venta registrada exitosamente! Total: ${total:.2f}', 'success')
            return redirect(url_for('ventas'))
        
        except ValueError:
            flash('Datos inválidos.', 'danger')
        except Error as e:
            flash(f'Error al registrar venta: {e}', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        finally:
            if connection:
                connection.close()

    return render_template('venta.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')