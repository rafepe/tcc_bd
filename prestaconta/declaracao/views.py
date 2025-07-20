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
        messages.error(request, "projeto não encontrado.")
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
        messages.error(request, "projeto não encontrado.")
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
        messages.error(request, "projeto não encontrado.")
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
        messages.error(request, "projeto não encontrado.")
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

##################################
from django.shortcuts import render
from contrapartida.models import projeto 

def declaracoes_menu(request):
    projetos = projeto.objects.all()  

    projeto_nome = request.GET.get('projeto')
    projeto_selecionado = None
    if projeto_nome:
        projeto_selecionado = projeto.objects.filter(nome=projeto_nome).first()

    return render(request, 'declaracao/menu.html', {
        'projetos': projetos,
        'projeto': projeto_selecionado,
        'mes': request.GET.get('mes'),
        'ano': request.GET.get('ano'),
    })




##################################
from django.http import HttpResponse
from docx import Document
from datetime import datetime
import os
from django.conf import settings
from .models import declaracao_contrapartida_rh
from .models import declaracao_contrapartida_rh_item

def gerar_docx(request, ano, mes):
    # Nome do mês por extenso
    mes_nome = datetime(ano, mes, 1).strftime('%B').capitalize()

    # Tenta buscar a declaração correspondente
    declaracao = declaracao_contrapartida_rh.objects.filter(ano=ano, mes=mes).first()
    declaracao_id = declaracao.id
    declaracao_itens = declaracao_contrapartida_rh_item.objects.filter(declaracao_id=declaracao_id)

    if not declaracao:
        return HttpResponse("Nenhuma declaração encontrada para esse mês e ano.")

    projeto_nome = declaracao.projeto
    total_valor_cp = declaracao.total

    # Caminho para o base.docx
    caminho_docx = os.path.join(settings.BASE_DIR, 'contrapartida', 'static', 'base.docx')
    doc = Document(caminho_docx)

    # Substitui os campos no texto
    for p in doc.paragraphs:
        p.text = (
            p.text
            .replace('{{mes_selecionado}}', mes_nome)
            .replace('{{ano_selecionado}}', str(ano))
            .replace('{{nome_projeto}}', projeto_nome)
            .replace('{{valor_total}}', f"R$ {total_valor_cp:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
        )
    itens = declaracao.itens.all() if declaracao else []
   
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    # Encontra o marcador {{tabela_itens}} e substitui pelo conteúdo da tabela
    for i, paragraph in enumerate(doc.paragraphs):
        if '{{tabela_itens}}' in paragraph.text:
            # Remove o marcador
            paragraph.text = paragraph.text.replace('{{tabela_itens}}', '')


            # Insere a tabela logo depois
            table = doc.add_table(rows=1, cols=7) if hasattr(doc, 'tables') else doc.add_table(rows=1, cols=7)
            table.style = 'Table Grid'

            # Cabeçalho
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Nome do Bolsista'
            hdr_cells[1].text = 'CPF'
            hdr_cells[2].text = 'Função'
            hdr_cells[3].text = 'Horas alocadas'
            hdr_cells[4].text = 'Salário'
            hdr_cells[5].text = 'Valor CP'
            hdr_cells[6].text = 'Valor Hora'

            # Preenche as linhas
            for item in itens:
                row_cells = table.add_row().cells
                row_cells[0].text = item.nome
                row_cells[1].text = item.cpf
                row_cells[2].text = item.funcao
                row_cells[3].text = str(item.horas_alocadas)
                row_cells[4].text = f"R$ {item.salario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                row_cells[5].text = f"R$ {item.valor_cp:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                row_cells[6].text = f"R$ {item.valor_hora:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            break  # Para após inserir a tabela
    p = doc.add_paragraph('(*) Valor das horas é o produto da multiplicação entre o nº de horas e o quociente da divisão do valor do salário por 160.')
    p = doc.add_paragraph('(**) Mês da competência do contracheque.')
    p = doc.add_paragraph('')
    p = doc.add_paragraph('')
    p = doc.add_paragraph('')
    p = doc.add_paragraph('')
    p = doc.add_paragraph('')
    p = doc.add_paragraph('')

    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

    # Adiciona uma tabela 2x2
    table = doc.add_table(rows=2, cols=2)
    table.style = 'Table Grid'  # ou outro estilo, ou personalize

    # Primeira linha (nomes)
    row = table.rows[0]
    row.cells[0].text = "Anderson Soares"
    row.cells[1].text = "Telma Woerle de Lima Soares"

    # Segunda linha (cargos)
    row = table.rows[1]
    row.cells[0].text = "Coordenador do projeto"
    row.cells[1].text = "Diretora da Unidade Embrapii - CEIA/UFG"

    # Ajusta alinhamento
    for r in table.rows:
        for cell in r.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # centraliza verticalmente
                # Se quiser alinhamento esquerdo/direito, pode usar LEFT ou RIGHT

    # Remove bordas para tabela invisível (opcional)
    tbl = table._tbl
    for cell in tbl.iter_tcs():
        tcPr = cell.tcPr
        for border in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            element = OxmlElement(f'w:{border}')
            element.set(qn('w:val'), 'nil')
            tcPr.append(element)



    # Resposta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="RH_{projeto_nome}_{mes}_{ano}.docx"'
    doc.save(response)
    return response

