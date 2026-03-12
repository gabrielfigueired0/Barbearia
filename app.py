from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# telefone administrador
ADMIN = "74999999999"

# lista de agendamentos
agendamentos = []


# função para gerar horários
def gerar_horarios():
    horarios = []
    hora = 7
    minuto = 30

    while hora < 19 or (hora == 19 and minuto <= 30):
        horarios.append(f"{hora:02d}:{minuto:02d}")

        minuto += 30
        if minuto == 60:
            minuto = 0
            hora += 1

    return horarios


# página de login
@app.route('/', methods=["GET", "POST"])
def login():

    mensagem = ""
    tipo = ""

    if request.method == "POST":
        telefone = request.form.get("telefone")

        if telefone == ADMIN:
            return redirect(url_for("agenda"))
        else:
            mensagem = "Telefone não cadastrado!"
            tipo = "erro"

    return render_template("agendamento.html", mensagem=mensagem, tipo=tipo)


# página de agendamento
@app.route('/agenda', methods=["GET", "POST"])
def agenda():

    mensagem = ""
    horarios = gerar_horarios()

    if request.method == "POST":

        servico = request.form.get("servico")
        horario = request.form.get("horario")

        ocupado = False

        for a in agendamentos:
            if a["horario"] == horario:
                ocupado = True

        if ocupado:
            mensagem = "Esse horário já foi agendado!"
        else:
            agendamentos.append({
                "servico": servico,
                "horario": horario
            })
            mensagem = "Agendamento realizado!"

    return render_template(
        "agendamento.html",
        horarios=horarios,
        mensagem=mensagem
    )
if __name__ == "__main__":
    app.run(debug=True)