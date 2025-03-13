from .models import *
from .tables import *
from datetime import datetime
from django_tables2 import SingleTableView
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
import csv
from django.http import JsonResponse
import io
import locale
    
from django.contrib import messages

def index(request):
    usuario = request.POST.get('username')
    senha = request.POST.get('password')
    user = authenticate(username=usuario, password=senha)
    if (user is not None):
        login(request, user)
        request.session['username'] = usuario
        request.session['password'] = senha
        request.session['usernamefull'] = user.get_full_name()

        return redirect('projeto_menu')
    else:       
        return render(request, 'index.html')

def meu_logout(request):
    logout(request)
    return redirect('logout')


def importar_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        model_choice = request.POST.get('model_choice')  # Pegando a escolha do modelo
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            return HttpResponse("O arquivo não é CSV", status=400)
        
        decoded_file = csv_file.read().decode('latin1')  # Decodificando o arquivo para 'latin1'
        io_string = io.StringIO(decoded_file)
        csv_reader = csv.reader(io_string, delimiter=',')
        
        # Importar para o modelo escolhido
        if model_choice == 'pessoa':
            for row in csv_reader:
                id, nome, ativo = row
                pessoa.objects.create(id=id, nome=nome, ativo=ativo)
            return HttpResponse("Arquivo CSV importado para o modelo Pessoa com sucesso!")
        
        elif model_choice == 'projeto':
            for row in csv_reader:
                id,nome,peia,data_inicio_str,data_fim_str,valor_total,valor_financiado,valor_so_ptr,valor_funape,tx_adm_ue,contrapartida,ativo = row

                try:
                    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
                except ValueError:
                    return HttpResponse(f"Formato de data inválido: {data_inicio_str}", status=400)
                
                try:
                    data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y").date()
                except ValueError:
                    return HttpResponse(f"Formato de data inválido: {data_fim_str}", status=400)
                #valor_total = float(valor_total_str.replace(",", "."))
                projeto.objects.create(id=id, nome=nome, peia=peia,data_inicio=data_inicio, data_fim=data_fim,
                                        valor_total=valor_total, valor_financiado=valor_financiado, valor_so_ptr=valor_so_ptr,
                                        valor_funape=valor_funape, tx_adm_ue=tx_adm_ue, contrapartida=contrapartida, ativo=ativo)
            return HttpResponse("Arquivo CSV importado para o modelo Projeto com sucesso!")
        
        elif model_choice == 'equipamento':
            for row in csv_reader:
                id, nome, valor_aquisicao, quantidade_nos, cvc, cma, ativo = row
                equipamento.objects.create(id=id, nome=nome, valor_aquisicao=valor_aquisicao, quantidade_nos=quantidade_nos, cvc=cvc, cma=cma, ativo=ativo)
            return HttpResponse("Arquivo CSV importado para o modelo Equipamento com sucesso!")
        
        elif model_choice == 'salario':
            for row in csv_reader:
                id,id_pessoa, mes, ano, valor, horas, anexo = row
                salario.objects.create(id=id,id_pessoa_id=id_pessoa,
                                        mes=mes, ano=ano, valor=valor, horas=horas, anexo=anexo)

            return HttpResponse("Arquivo CSV importado para o modelo Salário com sucesso!")


    return render(request, 'importar_csv.html')

###########
# PROJETO #
###########

class projeto_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(request, "Você não tem permissão para ver projetos.")
            return redirect('logout')

    model = projeto
    table_class = projeto_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'projeto_menu.html'

class projeto_create(CreateView):
    model = projeto
    fields = ['nome', 'peia', 'data_inicio', 'data_fim', 'valor_total', 'valor_financiado', 'valor_so_ptr', 'valor_funape', 'tx_adm_ue', 'contrapartida', 'ativo']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:          
            messages.error(self.request, "Usuário sem permissão para criar projetos.")
            return redirect('projeto_menu')
 
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Projeto criado com sucesso!")
        return response

    def form_invalid(self, form):
        print(form.errors)  # Exibe os erros no console do servidor
        messages.error(self.request, "Erro ao salvar o projeto. Verifique os dados.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('projeto_menu')

class projeto_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para atualizar projetos.")
            return redirect('projeto_menu')
   
    model = projeto
    fields = ['nome', 'peia', 'data_inicio', 'data_fim', 'valor_total', 'valor_financiado', 'valor_so_ptr', 'valor_funape', 'tx_adm_ue', 'contrapartida', 'ativo']
    def get_success_url(self):
        return reverse_lazy('projeto_menu')   

class projeto_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para excluir projetos.")
            return redirect('projeto_menu')

    model = projeto
    fields = ['nome','data_inicio', 'data_fim', 'valor']
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('projeto_menu')

###############
# EQUIPAMENTO #
###############

class equipamento_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para ver equipamentos.")
            return redirect('projeto_menu')

    model = equipamento
    table_class = equipamento_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'equipamento_menu.html'


class equipamento_create(CreateView):
    model = equipamento
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma', 'ativo']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para criar equipamentos.")
            return redirect('equipamento_menu')
        
    def form_invalid(self, form):
        # Se o formulário for inválido, imprime os erros no terminal
        print(form.errors)  # Exibe os erros no console
        messages.error(self.request, "Erro ao salvar o projeto. Verifique os campos.")
        return super().form_invalid(form)        

    def get_success_url(self):
        return reverse_lazy('equipamento_menu')

class equipamento_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para atualizar equipamentos.")
            return redirect('equipamento_menu')
   
    model = equipamento
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma', 'ativo']
    def get_success_url(self):
        return reverse_lazy('equipamento_menu')   

class equipamento_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para excluir equipamentos.")
            return redirect('equipamento_menu')

    model = equipamento
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma']
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('equipamento_menu')

##########
# PESSOA #
##########

class pessoa_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_pessoa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para ver pessoas")

    model = pessoa
    table_class = pessoa_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'pessoa_menu.html'

class pessoa_create(CreateView):
    model = pessoa
    fields = ['nome', 'ativo']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_pessoa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para criar pessoas.")
            return redirect('pessoa_menu')

    def get_success_url(self):
        return reverse_lazy('pessoa_menu')

class pessoa_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_pessoa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para atualizar pessoas.")
            return redirect('pessoa_menu')
   
    model = pessoa
    fields = ['nome', 'ativo']
    def get_success_url(self):
        return reverse_lazy('pessoa_menu')   

class pessoa_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_pessoa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para excluir pessoas.")
            return redirect('pessoa_menu')

    model = pessoa
    fields = ['nome', 'ativo']
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('pessoa_menu')
    
  
###########
# SALARIO #
###########
   

class salario_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para ver salários.")
            return redirect('projeto_menu')

    model = salario
    table_class = salario_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'salario_menu.html'

class salario_create(CreateView):
    model = salario
    fields = ['id_pessoa','ano', 'mes', 'valor', 'horas']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar salários", status=403)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            return HttpResponse("Erro: O salário para esta pessoa e referência já existe.")


    def form_invalid(self, form):
        errors = form.errors.as_text()  # Converte os erros para texto
        messages.error(self.request, f"Erro ao salvar o projeto: {errors}")  
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('salario_menu')

class salario_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar salarios")
   
    model = salario
    fields = ['id_pessoa','ano', 'mes', 'valor', 'horas']

    def get_success_url(self):
        return reverse_lazy('salario_menu')   

class salario_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir salarios")

    model = salario
    fields = []
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('salario_menu')
    

#######################
# PROJETOS SEMESTRAIS #
#######################

def get_semestre_atual():
    """Retorna o ano e o semestre atual"""
    hoje = now().date()
    ano = hoje.year
    semestre = 1 if hoje.month <= 6 else 2
    return ano, semestre

class projetos_semestre(ListView):
    model = projeto
    template_name = "contrapartida/projetos_semestre.html"
    context_object_name = "projetos"

    def get_queryset(self):
        """Filtra os projetos que se encerram no semestre selecionado"""
        ano = self.request.GET.get("ano")
        semestre = self.request.GET.get("semestre")

        if not ano or not semestre:
            ano, semestre = get_semestre_atual()

        try:
            ano = int(ano)
            semestre = int(semestre)
        except ValueError:
            ano, semestre = get_semestre_atual()

        # Definir intervalo do semestre
        if semestre == 1:
            data_inicio = datetime(ano, 1, 1)
            data_fim = datetime(ano, 6, 30)
        else:
            data_inicio = datetime(ano, 7, 1)
            data_fim = datetime(ano, 12, 31)

        #print(projeto.objects.filter(data_fim__range=(data_inicio, data_fim)))
        qs = projeto.objects.filter(data_fim__range=(data_inicio, data_fim))
        #print(qs.query)

        return projeto.objects.filter(data_fim__range=(data_inicio, data_fim))

    def get_context_data(self, **kwargs):
        """Adiciona os filtros ao contexto"""
        context = super().get_context_data(**kwargs)
        context["ano_atual"], context["semestre_atual"] = get_semestre_atual()
        context["ano_selecionado"] = self.request.GET.get("ano", context["ano_atual"])
        context["semestre_selecionado"] = self.request.GET.get("semestre", context["semestre_atual"])
        #print(context)
        return context

##########################
# CONTRAPARTIDA PESQUISA #
##########################

class contrapartida_pesquisa_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para ver contrapartida")

    model = contrapartida_pesquisa
    table_class = contrapartida_pesquisa_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'contrapartida_pesquisa_menu.html'




class contrapartida_pesquisa_create(CreateView):
    model = contrapartida_pesquisa
    fields = ['id_projeto', 'id_salario', 'horas_alocadas']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar cp pesquisa", status=403)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            return HttpResponse("Erro: O salário para esta pessoa e referência já existe.")


    def form_invalid(self, form):
        errors = form.errors.as_text()  # Converte os erros para texto
        messages.error(self.request, f"Erro ao salvar o projeto: {errors}")  
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('contrapartida_pesquisa_menu')



class contrapartida_pesquisa_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida_pesquisas")
   
    model = contrapartida_pesquisa
    fields =  ['id_projeto', 'id_salario', 'horas_alocadas']

    def get_success_url(self):
        return reverse_lazy('contrapartida_pesquisa_menu')   

class contrapartida_pesquisa_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir contrapartida_pesquisas")

    model = contrapartida_pesquisa
    fields = []
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('contrapartida_pesquisa_menu')     



##############################
# CONTRAPARTIDA EQUIPAMENTOS #
##############################

class contrapartida_equipamento_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para ver contrapartida")

    model = contrapartida_equipamento
    table_class = contrapartida_equipamento_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'contrapartida_equipamento_menu.html'




class contrapartida_equipamento_create(CreateView):
    model = contrapartida_equipamento
    fields = ['id_projeto', 'ano', 'mes', 'id_equipamento', 'horas_alocadas']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar cp pesquisa", status=403)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            return HttpResponse("Erro: O salário para esta pessoa e referência já existe.")


    def form_invalid(self, form):
        errors = form.errors.as_text()  # Converte os erros para texto
        messages.error(self.request, f"Erro ao salvar o projeto: {errors}")  
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('contrapartida_equipamento_menu')



class contrapartida_equipamento_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida_equipamentos")
   
    model = contrapartida_equipamento
    fields =  ['id_projeto', 'ano', 'mes', 'id_equipamento', 'horas_alocadas']

    def get_success_url(self):
        return reverse_lazy('contrapartida_equipamento_menu')   

class contrapartida_equipamento_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir contrapartida_equipamentos")

    model = contrapartida_equipamento
    fields = []
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('contrapartida_equipamento_menu')     

##############################
# CONTRAPARTIDA REALIZADA    #
##############################
class contrapartida_realizada_list(ListView):
    model = projeto  # Define o modelo explicitamente
    template_name = "contrapartida/contrapartida_realizada_list.html"
    context_object_name = "projetos"
    paginate_by = 10  # Paginação para melhor navegação

    def get_queryset(self):
        """Filtra os projetos por nome, data de fim ou por um dropdown"""
        queryset = projeto.objects.all()
        nome = self.request.GET.get("nome")
        data_fim = self.request.GET.get("data_fim")

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        if data_fim:
            queryset = queryset.filter(data_fim=data_fim)

        return queryset

from django.shortcuts import render, get_object_or_404
from datetime import datetime
from collections import defaultdict
from .models import projeto, contrapartida_pesquisa, contrapartida_equipamento #, contrapartidaSO


def contrapartida_realizada_detalhes(request, projeto_id):
    proj = get_object_or_404(projeto, id=projeto_id)

    # Calcula número de meses do projeto
    num_meses = (proj.data_fim.year - proj.data_inicio.year) * 12 + (proj.data_fim.month - proj.data_inicio.month)
    vlr_cp_max=proj.valor_total-proj.valor_financiado
    # Calcula Valor Mensal Devido
    vlr_mensal_devido = (vlr_cp_max ) /num_meses  if num_meses else 0.0
    # Dicionário para armazenar os totais por mês

    # Formata os valores antes de enviar ao template
    vlr_cp_max_formatado = locale.format_string('%.2f', vlr_cp_max, grouping=True)
    vlr_mensal_devido_formatado = locale.format_string('%.2f', vlr_mensal_devido, grouping=True)

    contrapartidas_por_mes = defaultdict(lambda: {
        'equipamento': 0.0,
        'pesquisa': 0.0,
        'so': 0.0,
        'total': 0.0,
        'diferenca': 0.0
    })
    
    # Processa contrapartida de pesquisa
    for c in contrapartida_pesquisa.objects.filter(id_projeto=proj):
        key = f"{c.id_salario.ano}-{c.id_salario.mes:02d}"
        value = round(c.horas_alocadas * c.id_salario.valor/ c.id_salario.horas, 2)
        contrapartidas_por_mes[key]['pesquisa'] += value

    # Processa contrapartida de equipamento
    for ce in contrapartida_equipamento.objects.filter(id_projeto=proj):
        key = f"{ce.ano}-{ce.mes:02d}"
        if ce.id_equipamento.nome in ['DGX-1', 'DGX-A100', 'DGX-H100']:
            value_valor_hora = (
                ((0.1 * float(ce.id_equipamento.valor_aquisicao)) +
                 float(ce.id_equipamento.cvc) + float(ce.id_equipamento.cma)) / 1200
            ) / float(ce.id_equipamento.quantidade_nos)
        else:
            value_valor_hora = (
                ((0.1 * float(ce.id_equipamento.valor_aquisicao)) +
                 float(ce.id_equipamento.cvc) + float(ce.id_equipamento.cma)) / 1440
            ) / float(ce.id_equipamento.quantidade_nos)
        value = round(float(ce.horas_alocadas) * value_valor_hora, 2)
        #print(ce.id_equipamento.nome, value)        
        contrapartidas_por_mes[key]['equipamento'] += value

    # Processa contrapartida de SO
    #for so in contrapartidaSO.objects.filter(projeto=proj):
    #    key = f"{so.ano_alocacao}-{so.mes_alocacao:02d}"
    #    contrapartidas_por_mes[key]['so'] += float(so.valor_financiado or 0)

    # Calcula total por mês e diferença
    for key, valores in contrapartidas_por_mes.items():
        valores['total'] = valores['equipamento'] + valores['pesquisa'] + valores['so']
        valores['diferenca'] = valores['total'] - float(vlr_mensal_devido) 

    # Ordena os meses do mais antigo para o mais recente
    contrapartidas_ordenadas = dict(sorted(contrapartidas_por_mes.items()))

    context = {
           'projeto': proj,
           'num_meses': num_meses,
           'vlr_cp_max': vlr_cp_max_formatado,  # Adicionado ao contexto
           'vlr_mensal_devido': vlr_mensal_devido_formatado,  # Adicionado ao contexto
           'contrapartidas_por_mes': contrapartidas_ordenadas,
    }

    return render(request, 'contrapartida/contrapartida_realizada_detalhes.html', context)




def contrapartida_realizada_detalhes_old(request, projeto_id):
    # Obtém o projeto pelo ID
    proj = get_object_or_404(projeto, id=projeto_id)

    # Calcula o número de meses do projeto
    num_meses = (proj.data_fim.year - proj.data_inicio.year) * 12 + (proj.data_fim.month - proj.data_inicio.month)

    # Dicionário para armazenar os totais por mês
    contrapartidas_por_mes = defaultdict(lambda: {'total': 0, 'saldo': 0})

    # Soma os valores de contrapartida_pesquisa
    for c in contrapartida_pesquisa.objects.filter(id_projeto=proj):
        key = f"{c.id_salario.ano}-{c.id_salario.mes:02d}"
        value = round(c.horas_alocadas * c.id_salario.valor/ c.id_salario.horas, 2)
        contrapartidas_por_mes[key]['total'] += value  # Exemplo, pode mudar para outro cálculo



    # Soma os valores de contrapartida_equipamento
    for ce in contrapartida_equipamento.objects.filter(id_projeto=proj):
        key = f"{ce.ano}-{ce.mes:02d}"
        value_valor_hora = (((0.1 * float(ce.id_equipamento.valor_aquisicao)) + 
        float(ce.id_equipamento.cvc) + float(ce.id_equipamento.cma)) /
        (1200 if ce.id_equipamento.nome in ['DGX-1', 'DGX-A100', 'DGX-H100'] else 1440)) / float(ce.id_equipamento.quantidade_nos)
        value = round(float(ce.horas_alocadas) * value_valor_hora, 2)
        formatted_value = locale.currency(value, grouping=True)    
        contrapartidas_por_mes[key]['total'] += formatted_value  or 0  # Evita None

    # Soma os valores de contrapartidaSO
 #   for so in contrapartidaSO.objects.filter(projeto=proj):
 #      key = f"{so.ano_alocacao}-{so.mes_alocacao:02d}"
 #       contrapartidas_por_mes[key]['total'] += so.valor_financiado or 0  # Evita None

    # Calculando saldo (exemplo: saldo = valor total do projeto - total por mês)
    for key, valores in contrapartidas_por_mes.items():
        valores['saldo'] = float(proj.valor_total) - float(valores['total'])

    context = {
        'projeto': proj,
        'num_meses': num_meses,
        'contrapartidas_por_mes': dict(contrapartidas_por_mes),
    }

    return render(request, 'contrapartida/contrapartida_realizada_detalhes.html', context)