from django.shortcuts import render
from declaracao.models import projeto, declaracao_contrapartida_pesquisa, declaracao_contrapartida_so, declaracao_contrapartida_rh, declaracao_contrapartida_equipamento
from datetime import date

def declaracoes_menu(request):
    print('views_folder/declaracoes_menu.py')
    print('declaracoes_menu')

    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    if semestre_atual == 1:
        semestre = 2
        ano = ano_atual - 1
    else:
        semestre = 1
        ano = ano_atual

    ano = int(request.GET.get('ano', ano))
    semestre = int(request.GET.get('semestre', semestre))

    if semestre == 1:
        data_ini_semestre = date(ano, 1, 1)
        data_fim_semestre = date(ano, 6, 30)
        meses = list(range(1, 7))
    else:
        data_ini_semestre = date(ano, 7, 1)
        data_fim_semestre = date(ano, 12, 31)
        meses = list(range(7, 13))

    projetos = projeto.objects.filter(
        ativo=True,
        data_inicio__lte=data_fim_semestre,
        data_fim__gte=data_ini_semestre
    ).order_by('nome')

    # Adaptação: permitir seleção de projeto, mês e ano, e mostrar declarações do mês/ano/projeto
    nome_projeto = request.GET.get('projeto')
    mes = request.GET.get('mes')
    if mes is not None:
        try:
            mes = int(mes)
        except ValueError:
            mes = None
    projeto_obj = None
    declaracoes = {}
    tipos = ["pesquisa", "so", "rh", "equipamento"]
    if nome_projeto:
        projeto_obj = projeto.objects.filter(nome=nome_projeto).first()
    if projeto_obj and mes and ano:
        declaracoes = {
            'pesquisa': declaracao_contrapartida_pesquisa.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'rh': declaracao_contrapartida_rh.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'so': declaracao_contrapartida_so.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'equipamento': declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first(),
        }

    contexto = {
        'ano': ano,
        'semestre': semestre,
        'projetos': projetos,
        'meses': meses,
        'projeto': projeto_obj,
        'mes': mes,
        'declaracoes': declaracoes,
        'tipos': tipos,
    }

    return render(request, 'declaracao/declaracoes_menu.html', contexto)
