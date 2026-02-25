from .models import *
from .tables import *
from contrapartida.models import *

import os
import zipfile
from itertools import groupby
from threading import Lock
from datetime import datetime, date
from decimal import Decimal

from django_tables2 import RequestConfig

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.edit import DeleteView

from .gerar_docx import (
    gerar_docx_rh as _gerar_docx_rh,
    gerar_docx_pesquisa as _gerar_docx_pesquisa,
    gerar_docx_so as _gerar_docx_so,
    gerar_docx_equipamento as _gerar_docx_equipamento,
    _pasta_declaracoes_semestre,
    _caminho_docx_declaracao,
    _caminho_docx_equipamento,
)


def gerar_declaracoes(request):
    nome_projeto = request.GET.get('projeto')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    projeto_selecionado = None
    if nome_projeto:
        projeto_selecionado = projeto.objects.filter(nome=nome_projeto).first()

    contexto = {
        'projeto': projeto_selecionado,
        'mes': mes,
        'ano': ano,
    }

    return render(request, 'declaracao/gerar_declaracoes.html', contexto)

def gerar_declaracao_contrapartida_pesquisa(request, projeto_id, mes, ano):

    try:
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    declaracao_existente = declaracao_contrapartida_pesquisa.objects.filter(
        projeto=projeto_selecionado, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_selecionado.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    declaracao = declaracao_contrapartida_pesquisa.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_selecionado.nome,
        codigo=projeto_selecionado.peia,
        mes=mes,
        ano=ano,
    )

    registros = contrapartida_pesquisa.objects.filter(
        id_projeto=projeto_selecionado,
        id_salario__mes=mes,
        id_salario__ano=ano
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    total=0

    for r in registros:
        pessoa_obj = r.id_salario.id_pessoa
        declaracao_contrapartida_pesquisa_item.objects.create(
            declaracao=declaracao,
            nome=pessoa_obj.nome,
            cpf=pessoa_obj.cpf,
            funcao=r.funcao,
            horas_alocadas=r.horas_alocadas,
            salario=r.id_salario.valor,
            valor_cp=r.valor_cp
        )

        total += r.valor_cp
    declaracao.total = total
    declaracao.save()

    messages.success(request, f"Declaração gerada para {projeto_selecionado.nome} - {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

class declaracao_contrapartida_pesquisa_view(TemplateView):
    template_name = 'declaracao/declaracao_contrapartida_pesquisa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_declaracao = self.kwargs.get('id_declaracao')
        declaracao = get_object_or_404(declaracao_contrapartida_pesquisa, id=id_declaracao)

        itens = declaracao_contrapartida_pesquisa_item.objects.filter(declaracao=declaracao)

        tabela = declaracao_contrapartida_pesquisa_item_table(itens)
        RequestConfig(self.request).configure(tabela)

        context['declaracao'] = declaracao
        context['tabela'] = tabela

        return context

class declaracao_contrapartida_pesquisa_delete(DeleteView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("declaracao.declaracao_contrapartida_pesquisa_delete"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir declaracoes de contrapartida_pesquisa")

    model = declaracao_contrapartida_pesquisa
    fields = []
    template_name_suffix = '_delete'
    context_object_name = 'declaracao'
    success_url='/declaracao/menu/?projeto={projeto}&mes={mes}&ano={ano}'

    def get_success_url(self):
        return self.success_url.format(
            projeto=self.object.projeto,
            mes=self.object.mes,
            ano=self.object.ano
        )

def gerar_declaracao_contrapartida_so(request, projeto_id, mes, ano):

    try:
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    declaracao_existente = declaracao_contrapartida_so.objects.filter(
        projeto=projeto_selecionado, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_selecionado.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    declaracao = declaracao_contrapartida_so.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_selecionado.nome,
        codigo=projeto_selecionado.peia,
        mes=mes,
        ano=ano,
    )


    registros = contrapartida_so_projeto.objects.filter(
        id_projeto=projeto_selecionado,
        mes=mes,
        ano=ano
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    total=0

    for r in registros:
        total += r.valor
    declaracao.total = total
    declaracao.save()

    messages.success(request, f"Declaração gerada para {projeto_selecionado.nome} - {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

class declaracao_contrapartida_so_view(TemplateView):
    template_name = 'declaracao/declaracao_contrapartida_so.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_declaracao = self.kwargs.get('id_declaracao')
        declaracao = get_object_or_404(declaracao_contrapartida_so, id=id_declaracao)

        context['declaracao'] = declaracao
        return context

class declaracao_contrapartida_so_delete(DeleteView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("declaracao.declaracao_contrapartida_so_delete"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir declaracoes de contrapartida_so")

    model = declaracao_contrapartida_so
    fields = []
    template_name_suffix = '_delete'
    context_object_name = 'declaracao'
    success_url='/declaracao/menu/?projeto={projeto}&mes={mes}&ano={ano}'

    def get_success_url(self):
        return self.success_url.format(
            projeto=self.object.projeto,
            mes=self.object.mes,
            ano=self.object.ano
        )

def gerar_declaracao_contrapartida_rh(request, projeto_id, mes, ano):

    try:
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    declaracao_existente = declaracao_contrapartida_rh.objects.filter(
        projeto=projeto_selecionado.nome, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_selecionado.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    declaracao = declaracao_contrapartida_rh.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_selecionado.nome,
        codigo=projeto_selecionado.peia,
        mes=mes,
        ano=ano,
    )

    registros = contrapartida_rh.objects.filter(
        id_projeto=projeto_selecionado,
        id_salario__mes=mes,
        id_salario__ano=ano
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')
    total=0

    for r in registros:
        pessoa_obj = r.id_salario.id_pessoa
        declaracao_contrapartida_rh_item.objects.create(
            declaracao=declaracao,
            nome=pessoa_obj.nome,
            cpf=pessoa_obj.cpf,
            funcao=r.funcao,
            horas_alocadas=r.horas_alocadas,
            salario=r.id_salario.valor,
            salario_mes=r.id_salario.mes,
            salario_ano=r.id_salario.ano,
            valor_cp=r.valor_cp,
            valor_hora=r.id_salario.valor_hora
        )

        total += r.valor_cp
    declaracao.total = total
    declaracao.save()

    messages.success(request, f"Declaração gerada para {projeto_selecionado.nome} - {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

class declaracao_contrapartida_rh_view(TemplateView):
    template_name = 'declaracao/declaracao_contrapartida_rh.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_declaracao = self.kwargs.get('id_declaracao')
        declaracao = get_object_or_404(declaracao_contrapartida_rh, id=id_declaracao)

        itens = declaracao_contrapartida_rh_item.objects.filter(declaracao=declaracao)

        tabela = declaracao_contrapartida_rh_item_table(itens)
        RequestConfig(self.request).configure(tabela)

        context['declaracao'] = declaracao
        context['tabela'] = tabela

        return context

class declaracao_contrapartida_rh_delete(DeleteView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("declaracao.declaracao_contrapartida_rh_delete"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir declaracoes de contrapartida_rh")

    model = declaracao_contrapartida_rh
    fields = []
    template_name_suffix = '_delete'
    context_object_name = 'declaracao'
    success_url='/declaracao/menu/?projeto={projeto}&mes={mes}&ano={ano}'

    def get_success_url(self):
        return self.success_url.format(
            projeto=self.object.projeto,
            mes=self.object.mes,
            ano=self.object.ano
        )

def gerar_declaracao_contrapartida_equipamento(request, projeto_id, mes, ano):
    try:
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    declaracao_existente = declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first()
    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    declaracao = declaracao_contrapartida_equipamento.objects.create(mes=mes, ano=ano)

    registros = (
        contrapartida_equipamento.objects
        .filter(mes=mes, ano=ano)
        .select_related("id_projeto", "id_equipamento")
        .order_by("id_equipamento__nome", "id_projeto__id")
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    for (equip_nome, proj_id), grupo in groupby(
        registros,
        key=lambda r: (r.id_equipamento.nome, r.id_projeto_id)
    ):
        grupo = list(grupo)

        horas_total = sum(Decimal(g.horas_alocadas or 0) for g in grupo)
        valor_total = sum(Decimal(g.valor_cp or 0) for g in grupo)

        # junta descrições únicas (se quiser)
        descricoes = []
        for g in grupo:
            d = (g.descricao or "").strip()
            if d and d not in descricoes:
                descricoes.append(d)
        descricao_final = "; ".join(descricoes)

        p0 = grupo[0].id_projeto

        declaracao_contrapartida_equipamento_item.objects.create(
            declaracao=declaracao,
            codigo=p0.peia,
            projeto=p0.nome,
            equipamento=equip_nome,
            descricao=descricao_final,
            horas_alocadas=horas_total,   # se seu campo for IntegerField, use int(horas_total)
            valor_cp=valor_total
        )

    messages.success(request, f"Declaração gerada para {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

class declaracao_contrapartida_equipamento_view(TemplateView):
    template_name = 'declaracao/declaracao_contrapartida_equipamento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id = self.kwargs.get('id_declaracao')
        declaracao = get_object_or_404(declaracao_contrapartida_equipamento, id=id)

        itens = declaracao_contrapartida_equipamento_item.objects.filter(declaracao=declaracao)

        tabela = declaracao_contrapartida_equipamento_item_table(itens)
        RequestConfig(self.request).configure(tabela)

        context['declaracao'] = declaracao
        context['tabela'] = tabela

        return context

class declaracao_contrapartida_equipamento_delete(DeleteView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("declaracao.declaracao_contrapartida_equipamento_delete"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir declaracoes de contrapartida_equipamento")

    model = declaracao_contrapartida_equipamento
    fields = []
    template_name_suffix = '_delete'
    context_object_name = 'declaracao'

    def get_success_url(self):
        return reverse_lazy('declaracoes_menu')

def central_declaracoes(request):
    projeto_id = request.GET.get('projeto_id')
    ano = request.GET.get('ano')
    semestre = request.GET.get('semestre')

    if not (projeto_id and ano and semestre):
        meses_data = []
    else:
        meses_semestre = [1, 2, 3, 4, 5, 6] if semestre == '1' else [7, 8, 9, 10, 11, 12]

        meses_data = []
        for mes in meses_semestre:
            registros_mes = declaracao_contrapartida_so.objects.filter(
                projeto_id=projeto_id,
                data__year=ano,
                data__month=mes,
            )

            meses_data.append({
                'mes': mes,
                'contrapartidas': registros_mes,
            })

    context = {
        'meses_data': meses_data,
        'ano': ano,
        'projeto_id': projeto_id,
        'semestre': semestre,
    }
    return render(request, 'declaracao/central.html', context)

def visualizar_declaracao(request, declaracao_id):
    """
    View para visualizar uma declaração específica
    """
    declaracao = get_object_or_404(declaracao_contrapartida_rh, id=declaracao_id)
    itens = declaracao_contrapartida_rh_item.objects.filter(declaracao=declaracao).order_by('nome')

    context = {
        'declaracao': declaracao,
        'itens': itens,
    }

    return render(request, 'declaracao/visualizar.html', context)

def download_declaracao(request, declaracao_id):
    """
    View para download da declaração em PDF (implementação básica)
    """
    declaracao = get_object_or_404(declaracao_contrapartida_rh, id=declaracao_id)
    itens = declaracao_contrapartida_rh_item.objects.filter(declaracao=declaracao).order_by('nome')

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from django.http import HttpResponse
        import io

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Cabeçalho
        p.drawString(100, 750, f"Declaração de Contrapartida RH")
        p.drawString(100, 730, f"Projeto: {declaracao.projeto}")
        p.drawString(100, 710, f"Período: {declaracao.mes}/{declaracao.ano}")
        p.drawString(100, 690, f"Total: R$ {declaracao.total:.2f}")

        # Itens
        y_position = 650
        for item in itens:
            p.drawString(100, y_position, f"{item.nome} - {item.funcao} - R$ {item.valor_cp:.2f}")
            y_position -= 20
            if y_position < 100:
                p.showPage()
                y_position = 750

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="declaracao_{declaracao.id}.pdf"'
        return response

    except ImportError:
        messages.warning(request, "Biblioteca de PDF não disponível. Mostrando versão HTML.")
        return render(request, 'declaracao/pdf.html', {
            'declaracao': declaracao,
            'itens': itens,
        })

def editar_declaracao(request, declaracao_id):
    """
    View para editar uma declaração
    """
    declaracao = get_object_or_404(declaracao_contrapartida_rh, id=declaracao_id)
    itens = declaracao_contrapartida_rh_item.objects.filter(declaracao=declaracao).order_by('nome')

    if request.method == 'POST':
        for item in itens:
            novo_valor = request.POST.get(f'valor_cp_{item.id}')
            if novo_valor:
                try:
                    item.valor_cp = float(novo_valor)
                    item.save()
                except ValueError:
                    pass

        declaracao.total = sum(item.valor_cp for item in itens)
        declaracao.save()

        messages.success(request, "Declaração atualizada com sucesso!")
        return redirect('visualizar_declaracao', declaracao_id=declaracao.id)

    context = {
        'declaracao': declaracao,
        'itens': itens,
    }

    return render(request, 'declaracao/editar.html', context)

def redirect_to_central(projeto_id, ano, semestre, projeto_nome=None, mes=None):
    """
    Função auxiliar para redirecionamento para a central
    """
    url = reverse('central_declaracoes')
    params = f'?projeto_id={projeto_id}&ano={ano}&semestre={semestre}'

    if projeto_nome:
        params += f'&projeto={projeto_nome}'
    if mes:
        params += f'&mes={mes}'

    return redirect(f'{url}{params}')

def get_nome_mes(numero_mes):

    """
    Função auxiliar para converter número do mês em nome
    """
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    return meses.get(numero_mes, f'Mês {numero_mes}')

@login_required
def ajax_dados_projeto(request):
    """
    View AJAX para carregar dados de um projeto específico por semestre
    """
    projeto_id = request.GET.get('projeto_id')
    semestre = int(request.GET.get('semestre', 1))
    ano = int(request.GET.get('ano'))

    if not projeto_id:
        return JsonResponse({'error': 'Projeto não especificado'}, status=400)

    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)

    meses_semestre = [1, 2, 3, 4, 5, 6] if semestre == 1 else [7, 8, 9, 10, 11, 12]

    dados_meses = {}

    for mes in meses_semestre:
        dados_meses[mes] = {
            'rh': verificar_declaracao_rh(projeto_obj.id, mes, ano),
            'pesquisa': verificar_declaracao_pesquisa(projeto_obj.id, mes, ano),
            'so': verificar_declaracao_so(projeto_obj.id, mes, ano),
            'equipamentos': verificar_declaracao_equipamentos(mes, ano),
            }

    resposta = {
        'projeto': {
            'id': projeto_obj.id,
            'nome': projeto_obj.nome,
            'codigo': projeto_obj.peia,
        },
        'semestre': semestre,
        'ano': ano,
        'meses': dados_meses
    }

    return JsonResponse(resposta)

def verificar_declaracao_rh(projeto_obj, mes, ano):
    """
    Verifica status da declaração de contrapartida RH para um mês específico
    """
    declaracao_existente = declaracao_contrapartida_rh.objects.filter(
        id_projeto=projeto_obj,
        mes=mes,
        ano=ano
    ).first()

    if declaracao_existente:
        return {
            'existe': True,
            'pode_gerar': False,
            'valor': float(declaracao_existente.total or 0),
            'declaracao_id': declaracao_existente.id,
            'data_criacao': declaracao_existente.data_geracao.strftime('%d/%m/%Y %H:%M') if declaracao_existente.data_geracao else None
        }

    registros_contrapartida = contrapartida_rh.objects.filter(
        id_projeto=projeto_obj,
        id_salario__mes=mes,
        id_salario__ano=ano
    )

    pode_gerar = registros_contrapartida.exists()
    valor_potencial = sum(r.valor_cp for r in registros_contrapartida) if pode_gerar else 0

    return {
        'existe': False,
        'pode_gerar': pode_gerar,
        'valor': 0,
        'valor_potencial': float(valor_potencial),
        'quantidade_registros': registros_contrapartida.count()
    }

def verificar_declaracao_pesquisa(projeto_obj, mes, ano):
    """
    Verifica status da declaração de contrapartida Pesquisa para um mês específico
    """
    declaracao_existente = declaracao_contrapartida_pesquisa.objects.filter(
        id_projeto=projeto_obj,
        mes=mes,
        ano=ano
    ).first()
    if declaracao_existente:
        return {
            'existe': True,
            'pode_gerar': False,
            'valor': float(declaracao_existente.total or 0),
            'declaracao_id': declaracao_existente.id,
            'data_criacao': declaracao_existente.data_geracao.strftime('%d/%m/%Y %H:%M') if declaracao_existente.data_geracao else None
        }

    registros_contrapartida = contrapartida_pesquisa.objects.filter(
        id_projeto=projeto_obj,
        id_salario__mes=mes,
        id_salario__ano=ano
    )

    pode_gerar = registros_contrapartida.exists()
    valor_potencial = sum(r.valor_cp for r in registros_contrapartida) if pode_gerar else 0

    return {
        'existe': False,
        'pode_gerar': pode_gerar,
        'valor': 0,
        'valor_potencial': float(valor_potencial),
        'quantidade_registros': registros_contrapartida.count()
    }

def verificar_declaracao_so(projeto_obj, mes, ano):
    """
    Verifica status da declaração de contrapartida SO para um mês específico
    """
    declaracao_existente = declaracao_contrapartida_so.objects.filter(
        id_projeto=projeto_obj,
        mes=mes,
        ano=ano
    ).first()

    if declaracao_existente:
        return {
            'existe': True,
            'pode_gerar': False,
            'valor': float(declaracao_existente.total or 0),
            'declaracao_id': declaracao_existente.id,
            'data_criacao': declaracao_existente.data_geracao.strftime('%d/%m/%Y %H:%M') if declaracao_existente.data_geracao else None
        }

    registros_contrapartida = contrapartida_so_projeto.objects.filter(
        id_projeto=projeto_obj,
        mes=mes,
        ano=ano
    )

    pode_gerar = registros_contrapartida.exists()
    valor_potencial = sum(r.valor for r in registros_contrapartida) if pode_gerar else 0

    return {
        'existe': False,
        'pode_gerar': pode_gerar,
        'valor': 0,
        'valor_potencial': float(valor_potencial),
        'quantidade_registros': registros_contrapartida.count()
    }

def verificar_declaracao_equipamentos(mes, ano):
    """
    Verifica status da declaração de contrapartida Equipamentos para um mês específico
    """
    declaracao_existente = declaracao_contrapartida_equipamento.objects.filter(
        mes=mes,
        ano=ano
    ).first()

    if declaracao_existente:
        itens_projeto = declaracao_contrapartida_equipamento_item.objects.filter(
            declaracao=declaracao_existente,
        )
        valor_total = sum(item.valor_cp for item in itens_projeto) if itens_projeto.exists() else 0

        return {
            'existe': itens_projeto.exists(),
            'pode_gerar': False,
            'valor': float(valor_total),
            'declaracao_id': declaracao_existente.id,
            'data_criacao': declaracao_existente.data_geracao.strftime('%d/%m/%Y %H:%M') if declaracao_existente.data_geracao else None
        }

    registros_contrapartida = contrapartida_equipamento.objects.filter(
        mes=mes,
        ano=ano
    )

    pode_gerar = registros_contrapartida.exists()
    valor_potencial = sum(r.valor_cp for r in registros_contrapartida) if pode_gerar else 0

    return {
        'existe': False,
        'pode_gerar': pode_gerar,
        'valor': 0,
        'valor_potencial': float(valor_potencial),
        'quantidade_registros': registros_contrapartida.count()
    }

@login_required
def download_declaracao_mes(request):
    """
    View para download de todas as declarações de um mês específico
    """
    projeto_id = request.GET.get('projeto_id')
    mes = int(request.GET.get('mes'))
    ano = int(request.GET.get('ano'))

    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)

    declaracoes = {
        'rh': declaracao_contrapartida_rh.objects.filter(
            id_projeto=projeto_id, mes=mes, ano=ano
        ).first(),
        'custeio': None,
        'equipamentos': None,
    }

    if declaracoes['rh']:
        return redirect('download_declaracao', declaracao_id=declaracoes['rh'].id)

    return JsonResponse({'error': 'Nenhuma declaração encontrada para este mês'}, status=404)


# =========================================================
# HTTP WRAPPERS PARA GERAR DOCX
# =========================================================

@login_required
def gerar_docx_rh(request, declaracao_id):
    decl = get_object_or_404(declaracao_contrapartida_rh, id=declaracao_id)
    _gerar_docx_rh(decl)
    messages.success(request, "DOCX RH gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={decl.projeto}&mes={decl.mes}&ano={decl.ano}')

@login_required
def gerar_docx_pesquisa(request, declaracao_id):
    decl = get_object_or_404(declaracao_contrapartida_pesquisa, id=declaracao_id)
    _gerar_docx_pesquisa(decl)
    messages.success(request, "DOCX Pesquisa gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={decl.projeto}&mes={decl.mes}&ano={decl.ano}')

@login_required
def gerar_docx_so(request, declaracao_id):
    decl = get_object_or_404(declaracao_contrapartida_so, id=declaracao_id)
    _gerar_docx_so(decl)
    messages.success(request, "DOCX SO gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={decl.projeto}&mes={decl.mes}&ano={decl.ano}')

@login_required
def gerar_docx_equipamento(request, id):
    decl = get_object_or_404(declaracao_contrapartida_equipamento, id=id)
    _gerar_docx_equipamento(decl)
    messages.success(request, "DOCX Equipamento gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?mes={decl.mes}&ano={decl.ano}')


def gerar_declaracoes_semestre(request):
    """
    Página para:
      - mostrar qtd de projetos no semestre
      - indicar se o semestre está completo (todas as declarações existem)
      - gerar declarações pendentes
      - gerar ZIP com as declarações DOCX existentes
    """
    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    # semestre padrão: anterior
    if semestre_atual == 1:
        semestre_default = 2
        ano_default = ano_atual - 1
    else:
        semestre_default = 1
        ano_default = ano_atual

    ano = int(request.GET.get("ano", ano_default))
    semestre = int(request.GET.get("semestre", semestre_default))
    meses_semestre = [1, 2, 3, 4, 5, 6] if semestre == 1 else [7, 8, 9, 10, 11, 12]

    # projetos ativos no semestre
    data_ini = date(ano, 1 if semestre == 1 else 7, 1)
    mes_fim = 6 if semestre == 1 else 12
    dia_fim = 30 if semestre == 1 else 31
    data_fim = date(ano, mes_fim, dia_fim)

    projetos = projeto.objects.filter(
        ativo=True,
        data_inicio__lte=data_fim,
        data_fim__gte=data_ini
    ).order_by("nome")

    projetos_qtd = projetos.count()

    # ---- contagem de declarações existentes ----
    total_existente = 0
    total_esperado = (projetos_qtd * 3 * len(meses_semestre)) + len(meses_semestre)

    for p in projetos:
        for mes in meses_semestre:
            if declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                total_existente += 1
            if declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                total_existente += 1
            if declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                total_existente += 1

    for mes in meses_semestre:
        if declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).exists():
            total_existente += 1

    semestre_completo = (total_existente == total_esperado)

    # ---- gerar declarações pendentes ----
    if request.GET.get("gerar") == "1":
        total_pesq = total_rh = total_so = total_equip = 0

        for p in projetos:
            for mes in meses_semestre:

                # PESQUISA
                if not declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_pesquisa(request, p.id, mes, ano)
                decl_p = declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_p:
                    _gerar_docx_pesquisa(decl_p)
                    total_pesq += 1

                # RH
                if not declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_rh(request, p.id, mes, ano)
                decl_rh = declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_rh:
                    _gerar_docx_rh(decl_rh)
                    total_rh += 1

                # SO
                if not declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_so(request, p.id, mes, ano)
                decl_so = declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_so:
                    _gerar_docx_so(decl_so)
                    total_so += 1

        # EQUIPAMENTO (1 por mês, global)
        for mes in meses_semestre:
            if not declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).exists():
                gerar_declaracao_contrapartida_equipamento(request, p.id, mes, ano)
            decl_eq = declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first()
            if decl_eq:
                _gerar_docx_equipamento(decl_eq)
                total_equip += 1

        messages.success(
            request,
            f"Declarações (e DOCX) gerados. Pesquisa={total_pesq}, RH={total_rh}, SO={total_so}, Equip={total_equip}"
        )

        request.session["ultima_geracao_zip"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        return redirect(reverse("gerar_declaracoes_semestre") + f"?ano={ano}&semestre={semestre}")

    # ---- ZIP do semestre ----
    pasta_semestre = _pasta_declaracoes_semestre(ano, semestre)
    zip_filename = f"declaracoes_{ano}-{semestre}.zip"
    zip_path = os.path.join(pasta_semestre, zip_filename)
    zip_exists = os.path.exists(zip_path)

    if request.GET.get("zip") == "1":
        # recria o ZIP sempre, com o que existir
        if os.path.exists(zip_path):
            os.remove(zip_path)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 1) arquivos por projeto
            for p in projetos:
                peia = p.peia
                nome_proj = p.nome

                for mes in meses_semestre:
                    caminho_rh = _caminho_docx_declaracao(ano, semestre, peia, nome_proj, "rh", mes)
                    if os.path.exists(caminho_rh):
                        zipf.write(caminho_rh, os.path.relpath(caminho_rh, pasta_semestre))

                    caminho_pesq = _caminho_docx_declaracao(ano, semestre, peia, nome_proj, "pesquisa", mes)
                    if os.path.exists(caminho_pesq):
                        zipf.write(caminho_pesq, os.path.relpath(caminho_pesq, pasta_semestre))

                    caminho_so = _caminho_docx_declaracao(ano, semestre, peia, nome_proj, "so", mes)
                    if os.path.exists(caminho_so):
                        zipf.write(caminho_so, os.path.relpath(caminho_so, pasta_semestre))

            # 2) equipamentos (1 por mês, global) — fora do loop de projetos
            for mes in meses_semestre:
                caminho_eq = _caminho_docx_equipamento(ano, semestre, mes)
                if os.path.exists(caminho_eq):
                    zipf.write(caminho_eq, os.path.relpath(caminho_eq, pasta_semestre))

        messages.success(request, "ZIP criado com sucesso!")
        return redirect(reverse("gerar_declaracoes_semestre") + f"?ano={ano}&semestre={semestre}")

    ultima_data = request.session.get("ultima_geracao_zip")

    return render(request, "declaracao/gerar_declaracoes_semestre.html", {
        "ano": ano,
        "semestre": semestre,
        "projetos_qtd": projetos_qtd,
        "semestre_completo": semestre_completo,
        "zip_exists": os.path.exists(zip_path),
        "zip_filename": zip_filename,
        "ultima_data": ultima_data,
    })


# =========================================================
# PROGRESSO GLOBAL (DEIXE SÓ ESTE, UMA ÚNICA VEZ NO ARQUIVO)
# =========================================================
progresso_lock = Lock()
progresso = {
    "status": "aguardando",   # aguardando | gerando | finalizado | erro
    "percentual": 0,
    "mensagem": "",
    "ano": None,
    "semestre": None,
    "finalizado": False,
}

def _set_progresso(**kwargs):
    with progresso_lock:
        progresso.update(kwargs)

def _no_cache_json(data, status=200):
    resp = JsonResponse(data, status=status)
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    return resp

@never_cache
@login_required
def progresso_semestre(request):
    with progresso_lock:
        return _no_cache_json(progresso)

@never_cache
@login_required
def gerar_semestre_ajax(request):
    print("Entrou no gerar_semestre_ajax")
    """
    Gera declarações + DOCX no disco, atualizando o dict global 'progresso'.
    O front faz polling em /progresso_semestre/ pra atualizar a barra.
    """
    try:
        ano = int(request.GET.get("ano"))
        semestre = int(request.GET.get("semestre"))
    except (TypeError, ValueError):
        _set_progresso(status="erro", mensagem="Parâmetros inválidos (ano/semestre).", finalizado=True)
        return _no_cache_json({"ok": False, "erro": "Parâmetros inválidos."}, status=400)

    meses = [1, 2, 3, 4, 5, 6] if semestre == 1 else [7, 8, 9, 10, 11, 12]

    data_ini = date(ano, 1 if semestre == 1 else 7, 1)
    data_fim = date(ano, 6 if semestre == 1 else 12, 30 if semestre == 1 else 31)

    projetos = projeto.objects.filter(
        ativo=True,
        data_inicio__lte=data_fim,
        data_fim__gte=data_ini
    ).order_by("nome")

    projetos_qtd = projetos.count()

    # total de "passos" pra barra:
    # 3 docx por projeto/mês (pesq, rh, so) + 1 docx de equipamento por mês
    total_ops = (projetos_qtd * 3 * len(meses)) + len(meses)
    if total_ops <= 0:
        _set_progresso(
            status="finalizado",
            percentual=100,
            mensagem="Nada a gerar (sem projetos no semestre).",
            ano=ano,
            semestre=semestre,
            finalizado=True,
        )
        return _no_cache_json({"ok": True, "vazio": True})

    atual = 0

    _set_progresso(
        status="gerando",
        percentual=0,
        mensagem="Iniciando geração...",
        ano=ano,
        semestre=semestre,
        finalizado=False,
    )
    def _msg_projeto(tipo: str, ano: int, mes: int, p) -> str:
        return f"Gerando {tipo} - {ano} - {mes:02d} - {p.peia} - {p.nome}"

    def _msg_equip(tipo: str, ano: int, mes: int) -> str:
        return f"Gerando {tipo} - {ano} - {mes:02d}"


    # log opcional (ajuda a debugar travas)
    logdir = os.path.join(settings.MEDIA_ROOT, "logs")
    os.makedirs(logdir, exist_ok=True)
    logpath = os.path.join(logdir, f"geracao_{ano}_{semestre}.log")

    def log(msg):
        with open(logpath, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - {msg}\n")

    log(f"Início geração semestre {semestre}/{ano}, projetos={projetos_qtd}")

    # pega um projeto "fallback" para a declaração de equipamento (sua função exige projeto_id)
    p_fallback = projetos.first()

    try:
        print("Entrou no try")
        # -------------------------
        # LOOP PROJETOS / MESES
        # -------------------------
        for p in projetos:
            for mes in meses:


                # ===== PESQUISA =====
                if not declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_pesquisa(request, p.id, mes, ano)



                decl_p = declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_p:
                    path = _gerar_docx_pesquisa(decl_p)
                    log(f"SALVO PESQUISA: {path}")


                atual += 1
                _set_progresso(
                    percentual=int(100 * atual / total_ops),
                    mensagem=_msg_projeto("Pesquisa", ano, mes, p)
                )


                # ===== RH =====

                if not declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_rh(request, p.id, mes, ano)

                decl_rh = declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_rh:
                    path = _gerar_docx_rh(decl_rh)
                    log(f"SALVO RH: {path}")


                atual += 1
                _set_progresso(
                    percentual=int(100 * atual / total_ops),
                    mensagem=_msg_projeto("RH", ano, mes, p)
                )


                # ===== SO =====
                if not declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_so(request, p.id, mes, ano)


                decl_so = declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_so:
                    path = _gerar_docx_so(decl_so)
                    log(f"SALVO SO: {path}")

                atual += 1
                _set_progresso(
                    percentual=int(100 * atual / total_ops),
                    mensagem=_msg_projeto("SO", ano, mes, p)
                )


        # -------------------------
        # EQUIPAMENTOS (1 por mês)
        # -------------------------
        for mes in meses:
            if not declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).exists():
                if p_fallback:
                    gerar_declaracao_contrapartida_equipamento(request, p_fallback.id, mes, ano)

            decl_eq = declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first()
            if decl_eq:
                path = _gerar_docx_equipamento(decl_eq)
                log(f"SALVO EQUIPAMENTO: {path}")



            atual += 1
            _set_progresso(
                percentual=int(100 * atual / total_ops),
                mensagem=_msg_equip("Equipamento", ano, mes)
            )


        _set_progresso(status="finalizado", percentual=100, mensagem="Geração concluída!", finalizado=True)
        log("Finalizado com sucesso.")
        return _no_cache_json({"ok": True})

    except Exception as e:
        log(f"ERRO: {repr(e)}")
        _set_progresso(status="erro", mensagem=f"Erro: {e}", finalizado=True)
        return _no_cache_json({"ok": False, "erro": str(e)}, status=500)
