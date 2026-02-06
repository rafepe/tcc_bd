from datetime import datetime,date

def format_br(value):
    if value is None:
        return "0,00"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_meses_entre(inicio: date, fim: date) -> list[date]:
    meses = []
    ano, mes = inicio.year, inicio.month

    fim_ano, fim_mes = fim.year, fim.month
    if fim.day < 15:
        if fim_mes == 1:
            fim_mes = 12
            fim_ano -= 1
        else:
            fim_mes -= 1

    while (ano, mes) <= (fim_ano, fim_mes):
        meses.append(date(ano, mes, 1))

        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1

    return meses