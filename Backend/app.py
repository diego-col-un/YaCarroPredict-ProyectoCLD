from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/prediccion", methods=["POST"])
def prediccion():

    datos = request.get_json()

    print("Datos recibidos:")
    print(datos)

    # Obtener los datos del pasajero
    pclass = datos["Pclass"]
    sex = datos["Sex"]
    age = datos["Age"]
    sibsp = datos["SibSp"]
    parch = datos["Parch"]
    fare = datos["Fare"]

    print("Pclass:", pclass)
    print("Sex:", sex)
    print("Age:", age)
    print("SibSp:", sibsp)
    print("Parch:", parch)
    print("Fare:", fare)

    return jsonify({
        "mensaje": "Datos recibidos correctamente",
        "datos": {
            "Pclass": pclass,
            "Sex": sex,
            "Age": age,
            "SibSp": sibsp,
            "Parch": parch,
            "Fare": fare
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
