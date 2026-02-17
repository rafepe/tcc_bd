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



def aplicar_filtro(queryset, request,filtros):
    for nome_filtro ,nome_model in filtros.items():
        valor = request.get(nome_filtro, "").strip()
        if valor:
            queryset = queryset.filter(**{f"{nome_model}__icontains": valor})
    return queryset

def aplicar_filtro_data(queryset, request,filtros):
    for nome_filtro,nome_model in filtros.items():
        valor = request.get(nome_filtro, "").strip()
        if valor:
            queryset = queryset.filter(**{f"{nome_model}": valor})
    return queryset


def contexto_filtros(params, campos):
    """
    Retorna apenas os filtros ativos definidos em `campos`.
    Ex:
        contexto_filtros(request.GET, ["nome", "ano", "mes"])
    """
    return {
        campo: params.get(campo, "").strip()
        for campo in campos
    }