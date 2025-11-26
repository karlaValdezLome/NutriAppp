from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import requests

app = Flask(__name__)
app.secret_key = 'contaseña'

API_KEY = "3f9hknPFUPlm5kFjIJ2d75AfXmlUyU5E7M1Ktd9a"
API_URL = "https://api.nal.usda.gov/fdc/v1/"

USUARIOS_REGISTRADOS = {
    'usuario@ejemplo.com': {
        'password': 'contraseña',
        'nombre': 'Usuario Ejemplo',
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/iniciode')
def inicio_de_sesion():
    return render_template('iniciode.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/education')
def education():
    return render_template('educacion.html')

@app.route('/calculadora.html')
def herramientas():
    return render_template('plantilla.html')

@app.route('/plantilla')
def plantilla():
    return render_template('plantilla.html')

@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    resultados = {}
    datos_usuario = None
    
    if session.get('user'):
        usuario_correo = session.get('user')
        if usuario_correo in USUARIOS_REGISTRADOS:
            datos_usuario = USUARIOS_REGISTRADOS[usuario_correo]
    
    if request.method == 'POST':
        if 'calcular_imc' in request.form:
            try:
                peso = float(request.form.get('imc_peso', 0))
                altura_cm = float(request.form.get('imc_altura', 0))
                
                if peso > 0 and altura_cm > 0:
                    altura_m = altura_cm / 100
                    imc = peso / (altura_m * altura_m)
                    
                    if imc < 18.5:
                        clasificacion = 'Bajo peso'
                    elif imc < 25:
                        clasificacion = 'Peso normal'
                    elif imc < 30:
                        clasificacion = 'Sobrepeso'
                    elif imc < 35:
                        clasificacion = 'Obesidad grado I'
                    elif imc < 40:
                        clasificacion = 'Obesidad grado II'
                    else:
                        clasificacion = 'Obesidad grado III'
                    
                    resultados['imc'] = {
                        'valor': round(imc, 2),
                        'clasificacion': clasificacion
                    }
            except ValueError:
                resultados['imc_error'] = 'Por favor ingresa valores válidos'

        elif 'calcular_tmb' in request.form:
            try:
                sexo = request.form.get('tmb_sexo', 'female')
                peso = float(request.form.get('tmb_peso', 0))
                altura_cm = float(request.form.get('tmb_altura', 0))
                edad = int(request.form.get('tmb_edad', 0))
                
                if peso > 0 and altura_cm > 0 and edad > 0:
                    if sexo == 'male':
                        tmb = (10 * peso) + (6.25 * altura_cm) - (5 * edad) + 5
                    else:
                        tmb = (10 * peso) + (6.25 * altura_cm) - (5 * edad) - 161
                    
                    resultados['tmb'] = round(tmb)
                    session['tmb_calculada'] = round(tmb)
            except ValueError:
                resultados['tmb_error'] = 'Por favor ingresa valores válidos'

        elif 'calcular_gct' in request.form:
            try:
                factor_actividad = float(request.form.get('gct_actividad', 1.2))
                tmb_manual = float(request.form.get('gct_manual', 0))
                
                if tmb_manual > 0:
                    gct = tmb_manual * factor_actividad
                    resultados['gct'] = round(gct)
            except ValueError:
                resultados['gct_error'] = 'Por favor ingresa una TMB válida'

        elif 'calcular_peso_ideal' in request.form:
            try:
                sexo = request.form.get('pi_sexo', 'female')
                altura_cm = float(request.form.get('pi_altura', 0))
                metodo = request.form.get('pi_metodo', 'devine')
                
                if altura_cm > 0:
                    if metodo == 'devine':
                        if sexo == 'male':
                            peso_ideal = 50 + 2.3 * ((altura_cm / 2.54) - 60)
                        else:
                            peso_ideal = 45.5 + 2.3 * ((altura_cm / 2.54) - 60)
                    else:
                        if sexo == 'male':
                            peso_ideal = 48 + 2.7 * ((altura_cm / 2.54) - 60)
                        else:
                            peso_ideal = 45.5 + 2.2 * ((altura_cm / 2.54) - 60)
                    
                    resultados['peso_ideal'] = round(peso_ideal, 1)
            except ValueError:
                resultados['peso_ideal_error'] = 'Por favor ingresa una altura válida'
        
        elif 'calcular_macros' in request.form:
            try:
                calorias = float(request.form.get('macro_kcal', 0))
                prot_pct = float(request.form.get('macro_prot', 20))
                carbs_pct = float(request.form.get('macro_carbs', 50))
                
                if calorias > 0:
                    if prot_pct + carbs_pct > 100:
                        resultados['macro_error'] = 'La suma de proteínas y carbohidratos no puede exceder 100%'
                    else:
                        fat_pct = 100 - prot_pct - carbs_pct
                        prot_g = (calorias * (prot_pct / 100)) / 4
                        carbs_g = (calorias * (carbs_pct / 100)) / 4
                        fat_g = (calorias * (fat_pct / 100)) / 9
                        
                        resultados['macros'] = {
                            'prot_g': round(prot_g, 1),
                            'prot_pct': prot_pct,
                            'carbs_g': round(carbs_g, 1),
                            'carbs_pct': carbs_pct,
                            'fat_g': round(fat_g, 1),
                            'fat_pct': round(fat_pct, 1)
                        }
            except ValueError:
                resultados['macro_error'] = 'Por favor ingresa valores válidos'
        
        elif 'calcular_receta' in request.form:
            try:
                total_calorias = 0
                total_proteinas = 0
                total_grasas = 0
                total_carbohidratos = 0
                
                i = 0
                while True:
                    calorias = request.form.get(f'receta_calorias_{i}')
                    if calorias is None:
                        break
                    
                    try:
                        total_calorias += float(calorias or 0)
                        total_proteinas += float(request.form.get(f'receta_proteinas_{i}', 0))
                        total_grasas += float(request.form.get(f'receta_grasas_{i}', 0))
                        total_carbohidratos += float(request.form.get(f'receta_carbs_{i}', 0))
                    except ValueError:
                        pass
                    
                    i += 1
                
                if i > 0:
                    resultados['receta'] = {
                        'calorias': round(total_calorias, 1),
                        'proteinas': round(total_proteinas, 1),
                        'grasas': round(total_grasas, 1),
                        'carbohidratos': round(total_carbohidratos, 1)
                    }
                else:
                    resultados['receta_error'] = 'Agrega al menos un ingrediente'
                    
            except Exception as e:
                resultados['receta_error'] = 'Error al calcular la receta'
    
    return render_template('calculadora.html', resultados=resultados, datos_usuario=datos_usuario)

@app.route('/usar_tmb')
def usar_tmb():
    tmb_calculada = session.get('tmb_calculada')
    if tmb_calculada:
        return redirect(url_for('calculadora', tmb_manual=tmb_calculada))
    return redirect(url_for('calculadora'))

@app.route('/auto_macros')
def auto_macros():
    return redirect(url_for('calculadora', macro_prot=25, macro_carbs=50))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[username]['password'] == password:
        session['user'] = username
        return redirect(url_for('index'))

    return redirect(url_for('inicio_de_sesion'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/buscar", methods=["POST"])
def buscar_alimento():
    nombre_comida = request.form.get("comida")
    
    if not nombre_comida:
        return redirect("/")
    
    try:
        params = {
            'api_key': API_KEY,
            'query': nombre_comida,
            'pageSize': 10
        }
        
        response = requests.get(f"{API_URL}foods/search", params=params)
        
        if response.status_code == 200:
            datos = response.json()
            alimentos = datos.get('foods', [])
            return render_template("index.html", alimentos=alimentos, busqueda=nombre_comida)
            
    except Exception as e:
        print(f"Error: {e}")
    
    return redirect("/")

@app.route("/api/buscar", methods=["POST"])
def api_buscar():
    nombre_comida = request.json.get("comida")
    
    if not nombre_comida:
        return jsonify({"error": "No se proporcionó el nombre del alimento"}), 400
    
    params = {
        'api_key': API_KEY,
        'query': nombre_comida,
        'pageSize': 10
    }
    
    response = requests.get(f"{API_URL}foods/search", params=params)
    
    if response.status_code == 200:
        datos = response.json()
        alimentos = datos.get('foods', [])
        return jsonify(alimentos)
    
    return jsonify({"error": "Error al consultar la API"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)