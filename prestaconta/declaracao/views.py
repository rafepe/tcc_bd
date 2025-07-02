from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib import messages
from django_tables2 import RequestConfig
from django.urls import reverse
from .models import declaracao_contrapartida_pesquisa, declaracao_contrapartida_pesquisa_item,declaracao_contrapartida_so,declaracao_contrapartida_rh,declaracao_contrapartida_rh_item,declaracao_contrapartida_equipamento,declaracao_contrapartida_equipamento_item
from contrapartida.models import contrapartida_pesquisa,projeto,contrapartida_so_projeto,contrapartida_rh,contrapartida_equipamento
from .tables import declaracao_contrapartida_pesquisa_item_table,declaracao_contrapartida_rh_item_table,declaracao_contrapartida_equipamento_item_table
from django.http import HttpResponse, FileResponse,HttpResponseRedirect,HttpResponseNotAllowed
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView,View


def gerar_declaracoes(request):
    nome_projeto = request.GET.get('projeto')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    projeto_obj = None
    if nome_projeto:
        projeto_obj = projeto.objects.filter(nome=nome_projeto).first()

    contexto = {
        'projeto': projeto_obj,
        'mes': mes,
        'ano': ano,
    }

    print(contexto)
    return render(request, 'declaracao/gerar_declaracoes.html', contexto)

def declaracoes_menu(request):
    nome_projeto = request.GET.get('projeto')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    projeto_obj = None
    if nome_projeto:
        projeto_obj = projeto.objects.filter(nome=nome_projeto).first()

    declaracoes = {}
    if projeto_obj and mes and ano:
        declaracoes = {
            'pesquisa': declaracao_contrapartida_pesquisa.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'rh': declaracao_contrapartida_rh.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'so': declaracao_contrapartida_so.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'equipamento': declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first(),
        }

    tipos = ["pesquisa","so","rh","equipamento"]    

    contexto = {
        'projeto': projeto_obj,
        'mes': mes,
        'ano': ano,
        'declaracoes': declaracoes,
        'tipos':tipos,
    }

    return render(request, 'declaracao/menu.html', contexto)
###############
# PESQUISA    #
###############
def gerar_declaracao_contrapartida_pesquisa(request, projeto_id, mes, ano):

    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "Projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_pesquisa.objects.filter(
        projeto=projeto_obj, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_obj.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

    # Criar declaração
    declaracao = declaracao_contrapartida_pesquisa.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_obj.nome,
        codigo=projeto_obj.peia,
        mes=mes,    	
        ano=ano,
    )

    registros = contrapartida_pesquisa.objects.filter(
        id_projeto=projeto_obj,
        id_salario__mes=mes,
        id_salario__ano=ano
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')
    
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

    messages.success(request, f"Declaração gerada para {projeto_obj.nome} - {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

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
        # Substitui {projeto}, {mes}, {ano} no success_url usando os atributos do objeto
        print(self.object)
        return self.success_url.format(
            projeto=self.object.projeto,
            mes=self.object.mes,
            ano=self.object.ano
        )

###############
#     SO      #
###############

def gerar_declaracao_contrapartida_so(request, projeto_id, mes, ano):

    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "Projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_so.objects.filter(
        projeto=projeto_obj, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_obj.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

    # Criar declaração
    declaracao = declaracao_contrapartida_so.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_obj.nome,
        codigo=projeto_obj.peia,
        mes=mes,    	
        ano=ano,
    )
    print(declaracao.id_projeto)

    registros = contrapartida_so_projeto.objects.filter(
        id_projeto=projeto_obj,
        mes=mes,
        ano=ano
    )
    print(projeto_obj)

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')
    
    total=0

    for r in registros:
        total += r.valor
    declaracao.total = total
    declaracao.save()

    messages.success(request, f"Declaração gerada para {projeto_obj.nome} - {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

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
        # Substitui {projeto}, {mes}, {ano} no success_url usando os atributos do objeto
        print(self.object)
        return self.success_url.format(
            projeto=self.object.projeto,
            mes=self.object.mes,
            ano=self.object.ano
        )

###############
#     RH      #
###############
def gerar_declaracao_contrapartida_rh(request, projeto_id, mes, ano):

    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "Projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_rh.objects.filter(
        projeto=projeto_obj, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_obj.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

    # Criar declaração
    declaracao = declaracao_contrapartida_rh.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_obj.nome,
        codigo=projeto_obj.peia,
        mes=mes,    	
        ano=ano,
    )

    registros = contrapartida_rh.objects.filter(
        id_projeto=projeto_obj,
        id_salario__mes=mes,
        id_salario__ano=ano
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')
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

    messages.success(request, f"Declaração gerada para {projeto_obj.nome} - {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

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
        # Substitui {projeto}, {mes}, {ano} no success_url usando os atributos do objeto
        print(self.object)
        return self.success_url.format(
            projeto=self.object.projeto,
            mes=self.object.mes,
            ano=self.object.ano
        )

###############
# EQUIPAMENTO #
###############
def gerar_declaracao_contrapartida_equipamento(request, projeto_id, mes, ano):

    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "Projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_equipamento.objects.filter(
         mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

    # Criar declaração
    declaracao = declaracao_contrapartida_equipamento.objects.create(
        mes=mes,    	
        ano=ano,
    )

    registros = contrapartida_equipamento.objects.filter(
        mes=mes,
        ano=ano
    )

    if not registros.exists():
        messages.warning(request, "Nenhum dado encontrado para gerar a declaração.")
        declaracao.delete()
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')


    for r in registros:
        declaracao_contrapartida_equipamento_item.objects.create(
            declaracao=declaracao,
            codigo=r.id_projeto.peia,
            projeto=r.id_projeto.nome,
            equipamento=r.id_equipamento.nome,
            descricao=r.descricao,
            horas_alocadas=r.horas_alocadas,
            valor_cp=r.valor_cp
        )


    messages.success(request, f"Declaração gerada para {mes}/{ano}.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={projeto_obj.nome}&mes={mes}&ano={ano}')

class declaracao_contrapartida_equipamento_view(TemplateView):
    template_name = 'declaracao/declaracao_contrapartida_equipamento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_declaracao = self.kwargs.get('id_declaracao')
        declaracao = get_object_or_404(declaracao_contrapartida_equipamento, id=id_declaracao)

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