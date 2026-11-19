const form = document.querySelector("form");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const data = {
        Pclass: Number(document.getElementById("pclass").value),
        Sex: Number(document.getElementById("sex").value),
        Age: Number(document.getElementById("age").value),
        SibSp: Number(document.getElementById("sibsp").value),
        Parch: Number(document.getElementById("parch").value),
        Fare: Number(document.getElementById("fare").value)
    };

    console.log("Datos que voy a enviar:", data);

    try {
        const response = await fetch("http://localhost:5000/prediccion", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        console.log("Status HTTP:", response.status);

        if (!response.ok) {
            const textoError = await response.text();
            throw new Error(
                `Error HTTP ${response.status}: ${textoError}`
            );
        }

        const resultado = await response.json();

        console.log("Respuesta de la API:", resultado);

        alert(
            "Resultado de la predicción:\n" +
            JSON.stringify(resultado, null, 2)
        );

    } catch (error) {
        console.error("Error al realizar la predicción:", error);

        alert(
            "No se pudo realizar la predicción.\n\n" +
            error.message
        );
    }
});
