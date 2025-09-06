from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, func, or_
from datetime import datetime, date, timedelta
from db import db
from tablas.actividades import Actividades
from tablas.usuarios import Usuarios
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USER = os.getenv('DB_USER', 'root')
PASS = os.getenv('DB_PASS', 'root')
HOST = os.getenv('DB_HOST', '127.0.0.1')
PORT = os.getenv('DB_PORT', '8889')
NAME = os.getenv('DB_NAME', 'priority_pulse')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{USER}:{PASS}@{HOST}:{PORT}/{NAME}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def _has_completion_on(uid, d):
    return db.session.query(Actividades.id).filter(
        Actividades.usuario_id == uid,
        Actividades.estado == 1,
        Actividades.completada == True,
        func.date(Actividades.completada_en) == d
    ).first() is not None

def _compute_streak_and_totals(uid):
    today = date.today()
    streak = 0
    cur = today
    while _has_completion_on(uid, cur):
        streak += 1
        cur = cur - timedelta(days=1)
    total_days = db.session.query(func.count(func.distinct(func.date(Actividades.completada_en)))).filter(
        Actividades.usuario_id == uid,
        Actividades.estado == 1,
        Actividades.completada == True
    ).scalar() or 0
    today_completed = _has_completion_on(uid, today)
    return streak, total_days, today_completed

@app.route('/debug/db')
def debug_db():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        return f"DB_ERROR: {e}", 500
    uid = session.get('usuario_id')
    if not uid:
        return "OK-NO-SESSION", 200
    total = Actividades.query.filter_by(usuario_id=uid, estado=1).count()
    return f"OK uid={uid} actividades={total}", 200

@app.route('/rutinas', methods=['GET'])
def rutinas():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    rutinas = [
        {
            'id': 1,
            'title': 'Mañanas Productivas',
            'objective': 'Arranca el día con foco y energía',
            'img': 'img/rutinas/morning.jpg',
            'category': 'Hábitos',
            'level': 'Inicial',
            'activities': ['Levantarse 06:30', 'Hidratarse 500ml', 'Estiramientos 10 min', 'Plan del día']
        },
        {
            'id': 2,
            'title': 'Fitness Express',
            'objective': 'Mover el cuerpo y despejar la mente',
            'img': 'img/rutinas/fitness.jpg',
            'category': 'Salud',
            'level': 'Intermedio',
            'activities': ['Calentamiento 5 min', 'Circuito 20 min', 'Enfriamiento 5 min']
        },
        {
            'id': 3,
            'title': 'Lectura Nocturna',
            'objective': 'Cierra el día aprendiendo',
            'img': 'img/rutinas/reading.jpg',
            'category': 'Crecimiento',
            'level': 'Light',
            'activities': ['Silenciar notificaciones', 'Lectura 30 min', 'Notas rápidas']
        }
    ]
    chips = ['Bienestar', 'Productividad', 'Estudio', 'Fitness', 'Mindfulness']
    streak, _, _ = _compute_streak_and_totals(session['usuario_id'])
    return render_template('rutinas.html', rutinas=rutinas, chips=chips, racha=streak, color_racha='#ff9800')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        usuario = Usuarios.query.filter_by(email=email).first()
        if usuario and usuario.contrasena == password:
            session['usuario_id'] = usuario.id
            return redirect(url_for('actividades'))
        error = "Credenciales incorrectas"
        return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    errores = {}
    error = None
    if request.method == 'POST':
        nombre = request.form.get('Nombre', '').strip()
        apellido = request.form.get('Apellido', '').strip()
        email = request.form.get('Email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not nombre:
            errores['Nombre'] = 'Nombre obligatorio'
        if not apellido:
            errores['Apellido'] = 'Apellido obligatorio'
        if not email:
            errores['Email'] = 'Email obligatorio'
        if password != confirm_password:
            error = 'Las contraseñas no coinciden'
        if not errores and not error:
            nuevo_usuario = Usuarios(nombre=nombre, apellido=apellido, email=email, contrasena=password)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario registrado correctamente', 'success')
            return redirect(url_for('login'))
        return render_template('registrarse.html', errores=errores, error=error)
    return render_template('registrarse.html', errores=errores)

@app.route('/nueva_actividad', methods=['GET'])
def NvActividad():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    errores = {}
    streak, _, _ = _compute_streak_and_totals(session['usuario_id'])
    return render_template('NvActividad.html', racha=streak, color_racha='default', errores=errores)

@app.route('/nueva_actividad', methods=['POST'])
def PostNvActividad():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    errores = {}
    titulo = request.form.get('nombre', '').strip()
    fecha = request.form.get('fecha', '').strip()
    repeticion = request.form.get('repetir', '').strip()
    hora = request.form.get('hora', '').strip()
    prioridad = request.form.get('prioridad', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    rutaImagen = request.form.get('rutaImagen', '').strip()
    if rutaImagen and not rutaImagen.startswith('/'):
        rutaImagen = '/' + rutaImagen.lstrip('/')
    if not titulo or not fecha or not repeticion or not hora or not prioridad or not descripcion or not rutaImagen:
        errores['emptyValues'] = "Hay campos vacíos"
        streak, _, _ = _compute_streak_and_totals(session['usuario_id'])
        return render_template('NvActividad.html', racha=streak, color_racha='default', errores=errores)
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        hora_obj = datetime.strptime(hora, '%H:%M').time()
    except ValueError:
        errores['fechaError'] = 'Formato de fecha incorrecto. Use YYYY-MM-DD.'
        streak, _, _ = _compute_streak_and_totals(session['usuario_id'])
        return render_template('NvActividad.html', racha=streak, color_racha='default', errores=errores)
    try:
        usuario_id = session.get('usuario_id')
        nueva_tarea = Actividades(
            titulo=titulo,
            fecha=fecha_obj,
            repetir=repeticion,
            hora=hora_obj,
            prioridad=prioridad,
            descripcion=descripcion,
            imagen=rutaImagen,
            usuario_id=usuario_id,
            estado=1,
            completada=False,
            completada_en=None,
            creada_en=datetime.utcnow()
        )
        db.session.add(nueva_tarea)
        db.session.commit()
        flash('Actividad agregada correctamente')
        return redirect(url_for('actividades'))
    except SQLAlchemyError:
        errores['dbError'] = 'Error al guardar actividad en la base de datos'
        db.session.rollback()
    except Exception:
        errores['dbError'] = 'Error al guardar actividad'
    streak, _, _ = _compute_streak_and_totals(session['usuario_id'])
    return render_template('NvActividad.html', racha=streak, color_racha='default', errores=errores)

@app.route('/editar_actividad/<int:id>', methods=['GET', 'POST'])
def editar_actividad(id):
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    errores = {}
    actividad = Actividades.query.get_or_404(id)
    if request.method == 'POST':
        titulo = request.form.get('nombre', '').strip()
        fecha = request.form.get('fecha', '').strip()
        repeticion = request.form.get('repetir', '').strip()
        hora = request.form.get('hora', '').strip()
        prioridad = request.form.get('prioridad', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        rutaImagen = request.form.get('rutaImagen', '').strip()
        if rutaImagen and not rutaImagen.startswith('/'):
            rutaImagen = '/' + rutaImagen.lstrip('/')
        if not titulo or not fecha or not repeticion or not hora or not prioridad or not descripcion or not rutaImagen:
            errores['emptyValues'] = "Hay campos vacíos"
            return render_template('editar_actividad.html', actividad=actividad, errores=errores)
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            hora_obj = datetime.strptime(hora, '%H:%M').time()
        except ValueError:
            errores['fechaError'] = 'Formato de fecha incorrecto. Use YYYY-MM-DD.'
            return render_template('editar_actividad.html', actividad=actividad, errores=errores)
        try:
            actividad.titulo = titulo
            actividad.fecha = fecha_obj
            actividad.repetir = repeticion
            actividad.hora = hora_obj
            actividad.prioridad = prioridad
            actividad.descripcion = descripcion
            actividad.imagen = rutaImagen
            db.session.commit()
            flash('Actividad actualizada correctamente')
            return redirect(url_for('actividades'))
        except SQLAlchemyError:
            errores['dbError'] = 'Error al actualizar la actividad en la base de datos'
            db.session.rollback()
        except Exception:
            errores['dbError'] = 'Error al actualizar la actividad'
        return render_template('editar_actividad.html', actividad=actividad, errores=errores)
    return render_template('editar_actividad.html', actividad=actividad, errores=errores)

@app.route('/eliminar_actividad/<int:id>')
def eliminar_actividad(id):
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    actividad = Actividades.query.get_or_404(id)
    try:
        actividad.estado = 0
        db.session.commit()
        flash('Actividad eliminada correctamente')
        return redirect(url_for('actividades'))
    except SQLAlchemyError:
        flash('Error al eliminar la actividad', 'error')
        db.session.rollback()
    except Exception:
        flash('Error al eliminar la actividad', 'error')
    return redirect(url_for('actividades'))

@app.route('/actividades', methods=['GET'])
def actividades():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    errores = {}
    usuario_id = session.get('usuario_id')
    q = request.args.get('q', '').strip()
    try:
        query = Actividades.query.filter_by(usuario_id=usuario_id, estado=1)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Actividades.titulo.ilike(like), Actividades.descripcion.ilike(like)))
        actividades_usuario = query.order_by(Actividades.fecha, Actividades.hora).all()
        tareas = []
        for a in actividades_usuario:
            tareas.append({
                'id': a.id,
                'titulo': a.titulo,
                'descripcion': a.descripcion,
                'hora': a.hora.strftime('%H:%M') if a.hora else '',
                'imagen': a.imagen if a.imagen.startswith('/') else '/' + a.imagen,
                'completada': bool(getattr(a, 'completada', False)),
                'prioridad': a.prioridad,
                'repetir': a.repetir
            })
        racha, _, _ = _compute_streak_and_totals(usuario_id)
        return render_template('actividades.html', tareas_importantes=tareas, racha=racha, color_racha='default', errores=errores, q=q)
    except SQLAlchemyError:
        errores['actividades_error'] = 'Error al obtener actividades de la base de datos'
        return render_template('actividades.html', tareas_importantes=[], racha=0, color_racha='default', errores=errores, q=q)
    except Exception:
        errores['actividades_error'] = 'Error al obtener actividades'
        return render_template('actividades.html', tareas_importantes=[], racha=0, color_racha='default', errores=errores, q=q)

@app.route('/api/tareas/<int:tid>/toggle', methods=['POST'])
def api_toggle_tarea(tid):
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'no-auth'}), 401
    act = Actividades.query.filter_by(id=tid, usuario_id=usuario_id, estado=1).first()
    if not act:
        return jsonify({'error': 'not-found'}), 404
    value = request.json.get('completada')
    if isinstance(value, bool):
        act.completada = value
        act.completada_en = datetime.utcnow() if value else None
        try:
            db.session.commit()
            racha, dias_totales, today_completed = _compute_streak_and_totals(usuario_id)
            return jsonify({'ok': True, 'racha': racha, 'dias_totales': dias_totales, 'today_completed': today_completed})
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({'error': 'db'}), 500
    return jsonify({'error': 'bad-payload'}), 400

@app.route('/api/metrics/today', methods=['GET'])
def api_metrics_today():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'no-auth'}), 401
    hoy = date.today()
    q = Actividades.query.filter(
        Actividades.usuario_id == usuario_id,
        Actividades.estado == 1,
        Actividades.fecha == hoy
    )
    total = q.count()
    hechas = q.filter(Actividades.completada == True).count()
    pendientes = max(total - hechas, 0)
    pct = int((hechas * 100) / total) if total > 0 else 0
    return jsonify({'date': hoy.isoformat(), 'total': total, 'completadas': hechas, 'pendientes': pendientes, 'porcentaje': pct})

@app.route('/api/metrics/week', methods=['GET'])
def api_metrics_week():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'no-auth'}), 401
    hoy = date.today()
    inicio = hoy - timedelta(days=hoy.weekday())
    fin = inicio + timedelta(days=6)
    acts = Actividades.query.filter(
        Actividades.usuario_id == usuario_id,
        Actividades.estado == 1,
        Actividades.fecha >= inicio,
        Actividades.fecha <= fin
    ).all()
    days = []
    for i in range(7):
        d = inicio + timedelta(days=i)
        del_dia = [a for a in acts if a.fecha == d]
        total = len(del_dia)
        hechas = sum(1 for a in del_dia if getattr(a, 'completada', False))
        pct = int((hechas * 100) / total) if total > 0 else 0
        days.append({'date': d.isoformat(), 'weekday': i, 'total': total, 'completadas': hechas, 'porcentaje': pct})
    return jsonify({'week_start': inicio.isoformat(), 'week_end': fin.isoformat(), 'days': days})

@app.route('/api/metrics/streak', methods=['GET'])
def api_metrics_streak():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'error': 'no-auth'}), 401
    racha, dias_totales, today_completed = _compute_streak_and_totals(usuario_id)
    return jsonify({'racha': racha, 'dias_totales': dias_totales, 'today_completed': today_completed})

@app.route('/perfil')
def perfil():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    usuario = Usuarios.query.get_or_404(session['usuario_id'])
    return render_template('perfil.html', usuario=usuario)

@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    usuario = Usuarios.query.get_or_404(session['usuario_id'])
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    contrasena = request.form.get('contrasena', '').strip()
    confirmar_contrasena = request.form.get('confirmar_contrasena', '').strip()
    email = request.form.get('email', '').strip()
    if contrasena != confirmar_contrasena:
        flash('Las contraseñas no coinciden', 'error')
        return redirect(url_for('perfil'))
    if nombre and apellido and contrasena and email:
        usuario.nombre = nombre
        usuario.apellido = apellido
        usuario.contrasena = contrasena
        usuario.email = email
        db.session.commit()
        flash('Perfil actualizado con éxito')
    else:
        flash('Por favor, completa todos los campos')
    return redirect(url_for('perfil'))

@app.route('/eliminar_cuenta')
def eliminar_cuenta():
    if not session.get('usuario_id'):
        flash('Debes iniciar sesión para continuar')
        return redirect(url_for('login'))
    usuario = Usuarios.query.get_or_404(session['usuario_id'])
    try:
        Actividades.query.filter_by(usuario_id=usuario.id).delete()
        db.session.delete(usuario)
        db.session.commit()
        flash('Cuenta eliminada con éxito', 'success')
        session.pop('usuario_id', None)
        return redirect(url_for('login'))
    except SQLAlchemyError:
        db.session.rollback()
        flash('Error al eliminar la cuenta', 'error')
    return redirect(url_for('perfil'))

if __name__ == '__main__':
    app.run(debug=True)