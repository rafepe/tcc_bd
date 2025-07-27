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
#from .views_folder.declaracoes_menu import declaracoes_menu


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

    print(contexto)
    return render(request, 'declaracao/gerar_declaracoes.html', contexto)


###############

def declaracoes_menu(request):
    from datetime import date
    
    # Obter parâmetros da requisição
    nome_projeto = request.GET.get('projeto')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    # Definir semestre e ano padrão se não fornecidos
    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    if semestre_atual == 1:
        semestre = 2
        ano_default = ano_atual - 1
    else:
        semestre = 1
        ano_default = ano_atual

    ano = int(request.GET.get('ano', ano_default))
    semestre = int(request.GET.get('semestre', semestre))

    # Filtrar projetos ativos no semestre
    if semestre == 1:
        data_ini_semestre = date(ano, 1, 1)
        data_fim_semestre = date(ano, 6, 30)
    else:
        data_ini_semestre = date(ano, 7, 1)
        data_fim_semestre = date(ano, 12, 31)

    projetos = projeto.objects.filter(
        ativo=True,
        data_inicio__lte=data_fim_semestre,
        data_fim__gte=data_ini_semestre
    ).order_by('nome')

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
        'semestre': semestre,
        'declaracoes': declaracoes,
        'tipos': tipos,
        'projetos': projetos,
    }

    return render(request, 'declaracao/declaracoes_menu.html', contexto)

def gerar_declaracao_contrapartida_pesquisa(request, projeto_id, mes, ano):

    try:
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_pesquisa.objects.filter(
        projeto=projeto_selecionado, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_selecionado.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    # Criar declaração
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
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_so.objects.filter(
        projeto=projeto_selecionado, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_selecionado.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    # Criar declaração
    declaracao = declaracao_contrapartida_so.objects.create(
        id_projeto=projeto_id,
        projeto=projeto_selecionado.nome,
        codigo=projeto_selecionado.peia,
        mes=mes,    	
        ano=ano,
    )
    print('declaracao')
    print(declaracao.id_projeto)

    registros = contrapartida_so_projeto.objects.filter(
        id_projeto=projeto_selecionado,
        mes=mes,
        ano=ano
    )
    print('registros')
    print(projeto_selecionado)

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
        projeto_selecionado = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        messages.error(request, "projeto não encontrado.")
        return redirect('declaracoes_menu')

    # Verificar se já existe declaração
    declaracao_existente = declaracao_contrapartida_rh.objects.filter(
        projeto=projeto_selecionado.nome, mes=mes, ano=ano
    ).first()

    if declaracao_existente:
        messages.info(request, f"Já existe uma declaração para {projeto_selecionado.nome} - {mes}/{ano}.")
        url = reverse('declaracoes_menu')
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

    # Criar declaração
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
        # Substitui {projeto}, {mes}, {ano} no success_url usando os atributos do objeto
        print('get_success')
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
        projeto_selecionado = projeto.objects.get(id=projeto_id)
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
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

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
        return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')


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
    return redirect(f'{url}?projeto={projeto_selecionado.nome}&mes={mes}&ano={ano}')

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
from .models import projeto, declaracao_contrapartida_rh, declaracao_contrapartida_equipamento  # e outros modelos
from datetime import datetime


######################
from datetime import date
def menutai(request):
    print('menutai')
    nome_projeto = request.GET.get('projeto')
    mes = request.GET.get('mes')
    #ano = request.GET.get('ano')
    
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
    #print(projetos)

    projeto_obj = None
    if nome_projeto:
        projeto_obj = projeto.objects.filter(nome=nome_projeto).first()

    declaracoes = {}
    if projeto_obj and mes and ano:
        declaracoes = {
            'pesquisa': declaracao_contrapartida_pesquisa.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'rh': declaracao_contrapartida_rh.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'so': declaracao_contrapartida_so.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
            'equipamento': declaracao_contrapartida_equipamento.objects.filter(id_projeto=projeto_obj.id, mes=mes, ano=ano).first(),
        }

    tipos = ["pesquisa","so","rh","equipamento"]    

    contexto = {
        'projeto': projeto_obj,
        'mes': mes,
        'ano': ano,
        'semestre': semestre,
        'declaracoes': declaracoes,
        'tipos':tipos,
        'projetos': projetos

    }

    return render(request, 'declaracao/menutai.html', contexto)



##################################
from django.http import HttpResponse
from docx import Document
from datetime import datetime
import os
from django.conf import settings
from .models import declaracao_contrapartida_rh
from .models import declaracao_contrapartida_rh_item
from django.db.models import Sum

def gerar_docx(request, declaracao_id):
    declaracao_itens = declaracao_contrapartida_rh_item.objects.filter(declaracao_id=declaracao_id)
    ano = declaracao_itens.first().salario_ano if declaracao_itens.exists() else None
    mes = declaracao_itens.first().salario_mes if declaracao_itens.exists() else None

    # Nome do mês por extenso
    mes_nome = datetime(ano, mes, 1).strftime('%B').capitalize()

    if not declaracao_itens:
        return HttpResponse("Nenhuma declaração encontrada para esse mês e ano.")
    
    if declaracao_itens.exists():
        projeto_nome = declaracao_itens.first().declaracao.projeto
        total_valor_cp = declaracao_itens.aggregate(total=Sum('valor_cp'))['total'] or 0

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
    #itens = declaracao_itens.itens.all() if declaracao_itens else []
    itens = list(declaracao_itens) if declaracao_itens.exists() else []
   
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

from django.db.models.functions import ExtractMonth
from django.db.models import Q

def central_declaracoes(request):
    projeto_id = request.GET.get('projeto_id')
    ano = request.GET.get('ano')
    semestre = request.GET.get('semestre')
    print('central_dec')

    if not (projeto_id and ano and semestre):
        # caso queira, retorne vazio ou erro
        meses_data = []
    else:
        # meses do semestre
        meses_semestre = [1, 2, 3, 4, 5, 6] if semestre == '1' else [7, 8, 9, 10, 11, 12]

        meses_data = []
        for mes in meses_semestre:
            registros_mes = declaracao_contrapartida_rh.objects.filter(
                projeto_id=projeto_id,
                data__year=ano,
                data__month=mes,
            )

            # Você pode montar um dict com as informações necessárias para a tabela.
            # Exemplo simplificado:
            meses_data.append({
                'mes': mes,
                'contrapartidas': registros_mes,  # pode ajustar conforme a estrutura
            })

    context = {
        'meses_data': meses_data,
        'ano': ano,
        'projeto_id': projeto_id,
        'semestre': semestre,
    }
    return render(request, 'declaracao/central.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.db.models.functions import ExtractMonth
from django.db.models import Q
from django.template.loader import get_template
from django.conf import settings
import os


# Views auxiliares que estavam faltando
def visualizar_declaracao(request, declaracao_id):
    print('entrou em visualizar_declaracao')
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
    
    # Implementação básica - você pode usar reportlab, weasyprint, etc.
    try:
        # Se você tem reportlab instalado
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
        # Fallback para HTML se não tiver biblioteca de PDF
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
        # Lógica de edição aqui
        # Por exemplo, atualizar valores dos itens
        for item in itens:
            novo_valor = request.POST.get(f'valor_cp_{item.id}')
            if novo_valor:
                try:
                    item.valor_cp = float(novo_valor)
                    item.save()
                except ValueError:
                    pass
        
        # Recalcular total
        declaracao.total = sum(item.valor_cp for item in itens)
        declaracao.save()
        
        messages.success(request, "Declaração atualizada com sucesso!")
        return redirect('visualizar_declaracao', declaracao_id=declaracao.id)
    
    context = {
        'declaracao': declaracao,
        'itens': itens,
    }
    
    return render(request, 'declaracao/editar.html', context)



# Funções auxiliares
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
    
    print(f'{url}{params}')
        
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


######

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def ajax_dados_projeto(request):
    print('entrou ajax_dados')
    """
    View AJAX para carregar dados de um projeto específico por semestre
    """
    projeto_id = request.GET.get('projeto_id')
    semestre = int(request.GET.get('semestre', 1))
    ano = int(request.GET.get('ano'))
    print(projeto_id)
    
    if not projeto_id:
        return JsonResponse({'error': 'Projeto não especificado'}, status=400)
    
    try:
        projeto_obj = projeto.objects.get(id=projeto_id)
    except projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    
    # Determinar meses do semestre
    meses_semestre = [1, 2, 3, 4, 5, 6] if semestre == 1 else [7, 8, 9, 10, 11, 12]
    
    dados_meses = {}
    print('projeto_obj completo')
    print(projeto_obj)
    print('------ agora projeto_obj.id')
    print(projeto_obj.id)
    
    for mes in meses_semestre:
        dados_meses[mes] = {
            'rh': verificar_declaracao_rh(projeto_obj.id, mes, ano),
            'pesquisa': verificar_declaracao_pesquisa(projeto_obj.id, mes, ano),
            'so': verificar_declaracao_so(projeto_obj.id, mes, ano),
            'equipamentos': verificar_declaracao_equipamentos(projeto_obj, mes, ano),
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
    # Verificar se já existe declaração
    #print(projeto_obj)
    declaracao_existente = declaracao_contrapartida_rh.objects.filter(
        id_projeto=projeto_obj,
        mes=mes,
        ano=ano
    ).first()
    print('verificar declaracao_rh')
    print(declaracao_existente)
    #rint(declaracao_existente.id_projeto)
    
    if declaracao_existente:
        return {
            'existe': True,
            'pode_gerar': False,
            'valor': float(declaracao_existente.total or 0),
            'declaracao_id': declaracao_existente.id,
            'data_criacao': declaracao_existente.data_geracao.strftime('%d/%m/%Y %H:%M') if declaracao_existente.data_geracao else None
        }
    
    # Verificar se existem dados para gerar declaração
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
    # Verificar se já existe declaração
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
    
    # Verificar se existem dados para gerar declaração
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
    # Verificar se já existe declaração
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
    
    # Verificar se existem dados para gerar declaração
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

def verificar_declaracao_equipamentos(projeto_obj, mes, ano):
    """
    Verifica status da declaração de contrapartida Equipamentos para um mês específico
    """
    # Verificar se já existe declaração para o mês e ano
    declaracao_existente = declaracao_contrapartida_equipamento.objects.filter(
        mes=mes,
        ano=ano
    ).first()
    
    if declaracao_existente:
        # Verificar se há itens associados ao projeto específico
        itens_projeto = declaracao_contrapartida_equipamento_item.objects.filter(
            declaracao=declaracao_existente,
            projeto=projeto_obj.nome
        )
        valor_total = sum(item.valor_cp for item in itens_projeto) if itens_projeto.exists() else 0
        
        return {
            'existe': itens_projeto.exists(),
            'pode_gerar': False,
            'valor': float(valor_total),
            'declaracao_id': declaracao_existente.id,
            'data_criacao': declaracao_existente.data_geracao.strftime('%d/%m/%Y %H:%M') if declaracao_existente.data_geracao else None
        }
    
    # Verificar se existem dados para gerar declaração
    registros_contrapartida = contrapartida_equipamento.objects.filter(
        id_projeto=projeto_obj,
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
    
    # Buscar todas as declarações do mês
    declaracoes = {
        'rh': declaracao_contrapartida_rh.objects.filter(
            id_projeto=projeto_id, mes=mes, ano=ano
        ).first(),
        'custeio': None,  # Adapte conforme seus modelos
        'equipamentos': None,  # Adapte conforme seus modelos
    }
    
    # Se você tem apenas RH por enquanto, redirecione para o PDF específico
    if declaracoes['rh']:
        return redirect('download_declaracao', declaracao_id=declaracoes['rh'].id)
    
    # Caso contrário, retorne erro
    return JsonResponse({'error': 'Nenhuma declaração encontrada para este mês'}, status=404)