from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'clave_secreta'

def get_db():
    import mysql.connector
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="datos_bd",
        port=3306
    )

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensaje = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conexion = get_db()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
        if usuario:
            session['usuario_id'] = usuario['id']
            session['rol_id'] = usuario['rol_id']
            # Redirige según el rol
            if usuario['rol_id'] == 1:
                return redirect(url_for('admin_dashboard'))
            elif usuario['rol_id'] == 2:
                return redirect(url_for('docente_dashboard'))
            elif usuario['rol_id'] == 3:
                return redirect(url_for('estudiante_dashboard'))
            elif usuario['rol_id'] == 4:
                return redirect(url_for('padre_dashboard'))
        else:
            mensaje = "Usuario o contraseña incorrectos."
    return render_template('login.html', mensaje=mensaje)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('rol_id') != 1:
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/docente/dashboard')
def docente_dashboard():
    if session.get('rol_id') != 2:
        return redirect(url_for('login'))
    docente_id = session.get('usuario_id')
    conexion = get_db()
    cursor = conexion.cursor()
    # Busca los grupos donde el docente está asignado
    cursor.execute("""
        SELECT g.id, g.nombre, g.grado
        FROM grupos g
        JOIN grupo_usuario gu ON g.id = gu.grupo_id
        WHERE gu.user_id = %s
    """, (docente_id,))
    grupos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('docente_dashboard.html', grupos=grupos)

@app.route('/docente/grupo/<int:grupo_id>/alumnos')
def ver_alumnos_grupo(grupo_id):
    if session.get('rol_id') != 2:
        return redirect(url_for('login'))
    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido, u.username
        FROM users u
        JOIN grupo_usuario gu ON u.id = gu.user_id
        WHERE gu.grupo_id = %s AND u.rol_id = 3
    """, (grupo_id,))
    alumnos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('alumnos_grupo.html', alumnos=alumnos, grupo_id=grupo_id)

@app.route('/estudiante/dashboard')
def estudiante_dashboard():
    if session.get('rol_id') != 3:
        return redirect(url_for('login'))
    return render_template('estudiante_dashboard.html')

@app.route('/padre/dashboard')
def padre_dashboard():
    if session.get('rol_id') != 4:
        return redirect(url_for('login'))
    return render_template('padre_dashboard.html')

@app.route('/admin/nueva_institucion', methods=['GET', 'POST'])
def nueva_institucion():
    if session.get('rol_id') != 1:
        return redirect(url_for('login'))
    mensaje = None
    if request.method == 'POST':
        nombre = request.form['nombre']
        conexion = get_db()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO instituciones (nombre) VALUES (%s)", (nombre,))
        conexion.commit()
        cursor.close()
        conexion.close()
        mensaje = "Institución registrada correctamente."
    return render_template('nueva_institucion.html', mensaje=mensaje)

@app.route('/admin/nuevo_grupo', methods=['GET', 'POST'])
def nuevo_grupo():
    if session.get('rol_id') != 1:
        return redirect(url_for('login'))
    mensaje = None
    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM instituciones")
    instituciones = cursor.fetchall()
    if request.method == 'POST':
        nombre = request.form['nombre']
        grado = request.form['grado']
        institucion_id = request.form['institucion_id']
        cursor.execute("INSERT INTO grupos (nombre, grado, institucion_id) VALUES (%s, %s, %s)", (nombre, grado, institucion_id))
        conexion.commit()
        mensaje = "Grupo registrado correctamente."
    cursor.close()
    conexion.close()
    return render_template('nuevo_grupo.html', mensaje=mensaje, instituciones=instituciones)

@app.route('/admin/nueva_asignatura', methods=['GET', 'POST'])
def nueva_asignatura():
    if session.get('rol_id') != 1:
        return redirect(url_for('login'))
    mensaje = None
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        conexion = get_db()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO asignaturas (nombre, descripcion) VALUES (%s, %s)", (nombre, descripcion))
        conexion.commit()
        cursor.close()
        conexion.close()
        mensaje = "Asignatura registrada correctamente."
    return render_template('nueva_asignatura.html', mensaje=mensaje)

@app.route('/admin/nuevo_usuario', methods=['GET', 'POST'])
def nuevo_usuario():
    if session.get('rol_id') != 1:
        return redirect(url_for('login'))
    mensaje = None
    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM roles_user")
    roles = cursor.fetchall()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        rol_id = request.form['rol_id']
        cursor.execute(
            "INSERT INTO users (username, password, email, nombre, apellido, rol_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, password, email, nombre, apellido, rol_id)
        )
        conexion.commit()
        mensaje = "Usuario registrado correctamente."
    cursor.close()
    conexion.close()
    return render_template('nuevo_usuario.html', mensaje=mensaje, roles=roles)

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    mensaje = None
    rol_nombre = None
    institucion_nombre = None
    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM roles_user")
    roles = cursor.fetchall()
    cursor.execute("SELECT id, nombre FROM instituciones")
    instituciones = cursor.fetchall()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        rol_id = request.form['rol_id']
        institucion_id = request.form['institucion_id']
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, nombre, apellido, rol_id, institucion_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (username, password, email, nombre, apellido, rol_id, institucion_id)
            )
            conexion.commit()  # ¡IMPORTANTE!
            # Busca los nombres para mostrar en el mensaje
            cursor.execute("SELECT nombre FROM roles_user WHERE id=%s", (rol_id,))
            rol_nombre = cursor.fetchone()[0]
            cursor.execute("SELECT nombre FROM instituciones WHERE id=%s", (institucion_id,))
            institucion_nombre = cursor.fetchone()[0]
            mensaje = "¡Registro exitoso!"
        except Exception as e:
            mensaje = "Error: " + str(e)
    cursor.close()
    conexion.close()
    return render_template('registrarse.html', mensaje=mensaje, roles=roles, instituciones=instituciones, rol_nombre=rol_nombre, institucion_nombre=institucion_nombre)

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/apoyo')
def apoyo():
    return render_template('apoyo.html')

@app.route('/olvidaste', methods=['GET', 'POST'])
def olvidaste():
    mensaje = None
    if request.method == 'POST':
        email = request.form['email']
        # Aquí podrías buscar el usuario y enviar un correo real
        mensaje = "Si el correo existe en el sistema, recibirás instrucciones para restablecer tu contraseña."
    return render_template('olvidaste.html', mensaje=mensaje)

@app.route('/docente/grupo/<int:grupo_id>/asistencias', methods=['GET', 'POST'])
def registrar_asistencias(grupo_id):
    if session.get('rol_id') != 2:
        return redirect(url_for('login'))
    conexion = get_db()
    cursor = conexion.cursor()
    # Obtener alumnos del grupo
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido
        FROM users u
        JOIN grupo_usuario gu ON u.id = gu.user_id
        WHERE gu.grupo_id = %s AND u.rol_id = 3
    """, (grupo_id,))
    alumnos = cursor.fetchall()
    mensaje = None
    if request.method == 'POST':
        fecha = request.form['fecha']
        for alumno in alumnos:
            presente = request.form.get(f'presente_{alumno[0]}', 'off') == 'on'
            cursor.execute(
                "INSERT INTO asistencias (estudiante_id, fecha, presente) VALUES (%s, %s, %s)",
                (alumno[0], fecha, presente)
            )
        conexion.commit()
        mensaje = "Asistencias registradas correctamente."
    cursor.close()
    conexion.close()
    return render_template('registrar_asistencias.html', alumnos=alumnos, grupo_id=grupo_id, mensaje=mensaje)

@app.route('/docente/grupo/<int:grupo_id>/calificaciones', methods=['GET', 'POST'])
def registrar_calificaciones(grupo_id):
    if session.get('rol_id') != 2:
        return redirect(url_for('login'))
    conexion = get_db()
    cursor = conexion.cursor()
    # Obtener alumnos del grupo
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido
        FROM users u
        JOIN grupo_usuario gu ON u.id = gu.user_id
        WHERE gu.grupo_id = %s AND u.rol_id = 3
    """, (grupo_id,))
    alumnos = cursor.fetchall()
    # Obtener asignaturas
    cursor.execute("SELECT id, nombre FROM asignaturas")
    asignaturas = cursor.fetchall()
    mensaje = None
    if request.method == 'POST':
        fecha = request.form['fecha']
        asignatura_id = request.form['asignatura_id']
        for alumno in alumnos:
            calificacion = request.form.get(f'calificacion_{alumno[0]}')
            if calificacion:
                cursor.execute(
                    "INSERT INTO calificaciones (estudiante_id, asignatura_id, calificacion, fecha) VALUES (%s, %s, %s, %s)",
                    (alumno[0], asignatura_id, calificacion, fecha)
                )
        conexion.commit()
        mensaje = "Calificaciones registradas correctamente."
    cursor.close()
    conexion.close()
    return render_template('registrar_calificaciones.html', alumnos=alumnos, grupo_id=grupo_id, asignaturas=asignaturas, mensaje=mensaje)

@app.route('/docente/grupo/<int:grupo_id>/alertas', methods=['GET', 'POST'])
def registrar_alertas(grupo_id):
    if session.get('rol_id') != 2:
        return redirect(url_for('login'))
    docente_id = session.get('usuario_id')
    conexion = get_db()
    cursor = conexion.cursor()
    # Obtener alumnos del grupo
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido
        FROM users u
        JOIN grupo_usuario gu ON u.id = gu.user_id
        WHERE gu.grupo_id = %s AND u.rol_id = 3
    """, (grupo_id,))
    alumnos = cursor.fetchall()
    mensaje = None
    if request.method == 'POST':
        fecha = request.form['fecha']
        for alumno in alumnos:
            alerta = request.form.get(f'alerta_{alumno[0]}')
            if alerta:
                cursor.execute(
                    "INSERT INTO alertas (estudiante_id, docente_id, grupo_id, mensaje, fecha) VALUES (%s, %s, %s, %s, %s)",
                    (alumno[0], docente_id, grupo_id, alerta, fecha)
                )
        conexion.commit()
        mensaje = "Alertas registradas correctamente."
    cursor.close()
    conexion.close()
    return render_template('registrar_alertas.html', alumnos=alumnos, grupo_id=grupo_id, mensaje=mensaje)

if __name__ == '__main__':
    app.run(debug=True)