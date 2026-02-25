from ..models import *
from ..tables import *
from contrapartida.models import *

from decimal import Decimal
from itertools import groupby

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django_tables2 import RequestConfig
from django.views.generic import TemplateView
from django.views.generic.edit import DeleteView


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
            horas_alocadas=horas_total,
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
