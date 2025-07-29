import pandas as pd
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)

# Configuración de la base de datos (usamos SQLite por simplicidad)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo para la base de datos
class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zona = db.Column(db.String(50))
    numero_documento = db.Column(db.String(50))  # Cambiado a String para manejar ceros iniciales
    apellidos_nombres = db.Column(db.String(200))
    nombre_canton = db.Column(db.String(100))
    nombre_provincia = db.Column(db.String(100))
    funcion = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.String(20))

# Crear la base de datos (si no existe)
with app.app_context():
    db.create_all()

# Ruta para subir datos desde un archivo CSV
@app.route('/subir', methods=['POST'])
def subir_datos():
    # Leemos la hoja de cálculo CSV
    file = request.files['file']
    
    # Asegurarnos de que el archivo sea CSV
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Solo se permiten archivos CSV"}), 400
    
    # Leemos el archivo CSV usando pandas
    df = pd.read_csv(file)

    # Eliminar los registros actuales de la base de datos antes de insertar nuevos
    db.session.query(Registro).delete()
    db.session.commit()

    # Subir los nuevos datos a la base de datos
    for index, row in df.iterrows():
        # Insertar los datos del archivo CSV en la base de datos
        registro = Registro(
            zona=row['ZONA'],
            numero_documento=str(row['NUMERO_DOCUMENTO']),  # Aseguramos que 'numero_documento' sea tratado como texto
            apellidos_nombres=row['APELLIDOS_NOMBRES'],
            nombre_canton=row['NOMBRE_CANTON'],
            nombre_provincia=row['NOMBRE_PROVINCIA'],
            funcion=row['FUNCION'],
            fecha_nacimiento=row['FECHA_NACIMIENTO']
        )
        db.session.add(registro)
    
    db.session.commit()
    return jsonify({"message": "Datos subidos correctamente"}), 200

# Ruta para consultar los datos por cédula (numero_documento)
@app.route('/consultar', methods=['GET'])
def consultar_datos():
    # Obtener el parámetro 'cedula' desde la consulta URL
    cedula = request.args.get('cedula')

    if cedula:
        # Si la cédula es proporcionada, se filtran los registros por cédula (asegurándonos de que sea texto)
        registros = Registro.query.filter(Registro.numero_documento == cedula).all()
    else:
        # Si no se proporciona cédula, se obtienen todos los registros
        registros = Registro.query.all()

    # Si no se encontraron registros, se devuelve un mensaje de error
    if not registros:
        return jsonify({"message": "No se encontraron registros con esa cédula"}), 404

    result = []
    for registro in registros:
        result.append({
            "zona": registro.zona,
            "numero_documento": registro.numero_documento,
            "apellidos_nombres": registro.apellidos_nombres,
            "nombre_canton": registro.nombre_canton,
            "nombre_provincia": registro.nombre_provincia,
            "funcion": registro.funcion,
            "fecha_nacimiento": registro.fecha_nacimiento
        })

    # Asegurarse de que el JSON se devuelve correctamente con los caracteres especiales
    return Response(json.dumps(result, ensure_ascii=False), mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)
