from .models import *
from .tables import *
from collections import defaultdict
from datetime import datetime,date
from django_tables2 import SingleTableView,RequestConfig
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, FileResponse, JsonResponse
from django.shortcuts import redirect, render , get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from PyPDF2 import PdfReader
import calendar
import csv
import io
import os
import re
from .forms import ContrapartidaPesquisaFormSet,ContrapartidaRhFormSet,ContrapartidaSOFormSet,ContrapartidaEquipamentoFormSet


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

    def get_queryset(self):
        queryset = super().get_queryset()
        f_nome = self.request.GET.get('nome', '').strip()
        mes_fim = self.request.GET.get('mes', '').strip()
        ano_fim = self.request.GET.get('ano','').strip()
        if f_nome:
            queryset = queryset.filter(nome__icontains=f_nome)
        if mes_fim:
            queryset = queryset.filter(data_fim__month=int(mes_fim))
        if ano_fim:
            queryset = queryset.filter(data_fim__year=int(ano_fim))         
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "mes": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", "")
        }
        return context

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
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma','horas_mensais', 'ativo']

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
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma','horas_mensais', 'ativo']
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

    def get_queryset(self):
        queryset = super().get_queryset()
        pessoa = self.request.GET.get('nome', '').strip()
        email = self.request.GET.get('email', '').strip()
        cpf = self.request.GET.get('cpf','').strip()
        if pessoa:
            queryset = queryset.filter(nome__icontains=pessoa)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)        
        return context    

class pessoa_create(CreateView):
    model = pessoa
    fields = ['nome', 'ativo', 'cpf', 'email']

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
    fields = ['nome', 'ativo', 'cpf', 'email']  
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

    def get_queryset(self):
        queryset = super().get_queryset()
        pessoa = self.request.GET.get('nome', '').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes','').strip()
        if pessoa:
            queryset = queryset.filter(id_pessoa__nome__icontains=pessoa)
        if ano:
            queryset = queryset.filter(ano=ano)
        if mes:
            queryset = queryset.filter(mes=mes)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)        
        return context

class salario_create(CreateView):
    model = salario
    fields = ['id_pessoa', 'ano', 'mes', 'valor', 'horas','horas_limite', 'anexo']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar salários", status=403)

    def form_valid(self, form):
        try:
            messages.success(self.request, "Salário salvo com sucesso!")
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, "Erro: Já existe um salário para esta pessoa e referência (ano/mês).")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('salario_menu')

class salario_update(UpdateView):
    model = salario
    fields = ['id_pessoa', 'ano', 'mes', 'valor', 'horas','horas_limite', 'anexo']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar salários")

    def form_valid(self, form):
        # Remove o arquivo antigo se um novo for enviado
        old_instance = self.get_object()
        if old_instance.anexo and form.cleaned_data.get('anexo') != old_instance.anexo:
            if os.path.isfile(old_instance.anexo.path):
                os.remove(old_instance.anexo.path)
        messages.success(self.request, "Salário atualizado com sucesso!")
        return super().form_valid(form)

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

    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome', '').strip()
        pessoa= self.request.GET.get('pessoa','').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes','').strip()
        if nome:
            queryset = queryset.filter(id_projeto__nome__icontains=nome)
        if pessoa:
            queryset= queryset.filter(id_salario__id_pessoa__nome__icontains=pessoa)
        if ano:
            queryset = queryset.filter(id_salario__ano=ano)
        if mes:
            queryset = queryset.filter(id_salario__mes=mes)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "pessoa": self.request.GET.get("pessoa", ""),
            "ano": self.request.GET.get("ano", ""),
            "mes": self.request.GET.get("mes", ""),
        }
        return context

class contrapartida_pesquisa_create(CreateView):
    model = contrapartida_pesquisa
    fields = ['id_projeto', 'id_salario','funcao', 'horas_alocadas']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar cp pesquisa", status=403)

    def form_valid(self, form):
        # Pegue os dados do formulário necessários para validar
        salario_obj=form.cleaned_data.get('id_salario')

        proj = form.cleaned_data.get('id_projeto')  # ou campo que referencia o projeto
        data = date(salario_obj.ano,salario_obj.mes,proj.data_inicio.day)  # substitua 'data' pelo nome do campo real da data
        if data and proj:
            if not (proj.data_inicio <= data <= proj.data_fim):
                form.add_error('id_salario',f"Data fora do período vigência do projeto de {proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}")
                return self.form_invalid(form)
        
        try:
            return super().form_valid(form)
        except IntegrityError:
            return HttpResponse("Erro: Já existe uma contrapartida de pesquisa para este projeto e salário.")   

    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))
    

    
    def criar_contrapartida_pesquisa(request):
        context = super().get_context_data(**kwargs)

        horas_utilizadas = 0
        horas_mensais = 0
                    
        # Captura o ID do salário selecionado no dropdown (se houver)
        id_salario = self.request.GET.get("id_salario") or self.request.POST.get("id_salario")
        if id_salario:
            try:
                salario_obj = salario.objects.get(id=id_salario)
                pessoa_id = salario_obj.id_pessoa
                mes_ref = salario_obj.mes
                ano_ref = salario_obj.ano
                horas_mensais = (salario_obj.horas_limite or 0)  # Total de horas disponíveis para aquele salário

        

                # Filtra todas as contrapartidas já cadastradas com o mesmo salário
                horas_usadas_pesquisa = contrapartida_pesquisa.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)
                
                horas_usadas_rh =contrapartida_rh.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)


                horas_utilizadas = sum(horas_usadas_pesquisa) + sum(horas_usadas_rh) # Soma as horas já utilizadas

            except salario.DoesNotExist:
                messages.error(self.request, "Salário não encontrado")

        # Adicionando ao contexto
        context["horas_utilizadas"] = horas_utilizadas
        context["horas_mensais"] = horas_mensais
        context["horas_restantes"] = (horas_mensais or 0) - (horas_utilizadas or 0)
        return context

    def get_success_url(self):
        return reverse_lazy('contrapartida_pesquisa_menu')


    def get_success_url(self):
        return reverse_lazy("contrapartida_pesquisa_update", kwargs={"pk": self.object.pk})
    


class contrapartida_pesquisa_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida_pesquisas")
   
    model = contrapartida_pesquisa
    fields =  ['id_projeto', 'id_salario','funcao', 'horas_alocadas']


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        horas_utilizadas = 0
        horas_mensais = 0

        id_pesquisa = context["form"].instance.pk if "form" in context and context["form"].instance.pk else None
       
        if id_pesquisa:
            try:
                contrapartida = contrapartida_pesquisa.objects.get(id=id_pesquisa)
                salario_id=contrapartida.id_salario_id
                salario_obj=salario.objects.get(id =salario_id)  

                pessoa_id = salario_obj.id_pessoa
                mes_ref = salario_obj.mes
                ano_ref = salario_obj.ano
                horas_mensais = (salario_obj.horas_limite or 0)

                # Filtra todas as contrapartidas já cadastradas com o mesmo salário
                horas_usadas_pesquisa = contrapartida_pesquisa.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)

                # Soma as horas já utilizadas

                horas_usadas_rh =contrapartida_rh.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)


                horas_utilizadas = sum(horas_usadas_pesquisa) + sum(horas_usadas_rh)

            except contrapartida_pesquisa.DoesNotExist:
                   messages.error(self.request, "Contrapartida não encontrada")
            except salario.DoesNotExist:
                   messages.error(self.request, "Salário não encontrado")

    # Adicionando ao contexto
        context["horas_utilizadas"] = horas_utilizadas
        context["horas_mensais"] = horas_mensais
        context["horas_restantes"] = horas_mensais - horas_utilizadas

        return context    
    def form_valid(self, form):
        self.object = form.save()

        action = self.request.POST.get("action")

        salario_obj=form.cleaned_data.get('id_salario')
        
        proj = form.cleaned_data.get('id_projeto')  # ou campo que referencia o projeto
        data = date(salario_obj.ano,salario_obj.mes,proj.data_inicio.day)  # substitua 'data' pelo nome do campo real da data
        
        if data and proj:
            if not (proj.data_inicio <= data <= proj.data_fim):
                form.add_error('id_salario',f"Data fora do período vigência do projeto de {proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}")
                return self.form_invalid(form)
                

        if action == "update":
            return redirect("contrapartida_pesquisa_update", pk=self.object.pk)
        elif action == "save_exit":
            return redirect("contrapartida_pesquisa_menu")

        return super().form_valid(form)


    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

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

#################################################################################################################################################
# INSERIR MULTIPLOS
#####################################################################################################################

def contrapartida_pesquisa_criar_multiplos(request):
    """
    View para criar múltiplas contrapartidas de pesquisa
    O projeto é selecionado primeiro e os salários são filtrados por período
    """
    
    projeto_obj = None
    projeto_id = request.POST.get('id_projeto') or request.GET.get('id_projeto')
    
    # Busca o projeto se foi informado
    if projeto_id:
        try:
            projeto_obj = projeto.objects.get(id=projeto_id)
        except projeto.DoesNotExist:
            messages.error(request, 'Projeto não encontrado.')
            projeto_obj = None
    
    if request.method == 'POST':
        # Verifica se é apenas seleção de projeto ou submissão do formset
        tem_dados_formset = any(key.startswith('form-') for key in request.POST.keys())
        
        if not projeto_obj:
            messages.error(request, 'Selecione um projeto para continuar.')
            formset = ContrapartidaPesquisaFormSet(projeto=None)
            
        elif not tem_dados_formset:
            # É apenas seleção de projeto, não valida formset
            # Redireciona para a mesma página com projeto selecionado via GET
            return redirect(f"{request.path}?id_projeto={projeto_id}")
            
        else:
            # Tem dados do formset, processa normalmente
            formset = ContrapartidaPesquisaFormSet(request.POST, projeto=projeto_obj)
            
            if formset.is_valid():
                try:
                    with transaction.atomic():
                        instancias_salvas = []
                        
                        for form in formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                # Cria a instância
                                instance = form.save(commit=False)
                                instance.id_projeto = projeto_obj
                                instance.save()
                                instancias_salvas.append(instance)
                        
                        if instancias_salvas:
                            messages.success(
                                request,
                                f'{len(instancias_salvas)} contrapartida(s) cadastrada(s) '
                                f'com sucesso para o projeto "{projeto_obj.nome}"!'
                            )
                            return redirect('contrapartida_pesquisa_menu')
                        else:
                            messages.warning(request, 'Nenhuma contrapartida foi cadastrada.')
                
                except Exception as e:
                    messages.error(request, f'Erro ao salvar: {str(e)}')
            else:
                # Exibe erros de validação
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, str(error))
                
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, f'Linha {i+1} - {field}: {error}')
    else:
        # GET - exibe formulário
        formset = ContrapartidaPesquisaFormSet(projeto=projeto_obj)
    
    # Lista de projetos para o select
    lista_projetos = projeto.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'formset': formset,
        'projetos': lista_projetos,
        'projeto_obj': projeto_obj,
    }
    
    return render(request, 'contrapartida/contrapartida_pesquisa_form_multiplo.html', context)

def obter_horas_disponiveis(request):
    """
    API para retornar horas disponíveis de um salário (chamada via AJAX)
    """
    salario_id = request.GET.get('salario_id')
    
    if not salario_id:
        return JsonResponse({'error': 'ID do salário não fornecido'}, status=400)
    
    try:
        salario_obj = salario.objects.get(id=salario_id)
        
        # Calcula horas utilizadas
        horas_usadas_pesquisa = contrapartida_pesquisa.objects.filter(
            id_salario__id_pessoa=salario_obj.id_pessoa,
            id_salario__mes=salario_obj.mes,
            id_salario__ano=salario_obj.ano
        ).aggregate(total=Sum('horas_alocadas'))['total'] or 0
        
        horas_usadas_rh = contrapartida_rh.objects.filter(
            id_salario__id_pessoa=salario_obj.id_pessoa,
            id_salario__mes=salario_obj.mes,
            id_salario__ano=salario_obj.ano
        ).aggregate(total=Sum('horas_alocadas'))['total'] or 0
        
        horas_utilizadas = horas_usadas_pesquisa + horas_usadas_rh
        horas_totais = salario_obj.horas_limite or 0
        horas_disponiveis = horas_totais - horas_utilizadas
        
        return JsonResponse({
            'horas_totais': float(horas_totais),
            'horas_utilizadas': float(horas_utilizadas),
            'horas_disponiveis': float(horas_disponiveis),
            'pessoa': str(salario_obj.id_pessoa),
            'periodo': f"{salario_obj.mes}/{salario_obj.ano}"
        })
    
    except salario.DoesNotExist:
        return JsonResponse({'error': 'Salário não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


#####################################################################################################################

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

    def get_queryset(self):
        queryset = super().get_queryset()
        v_nome = self.request.GET.get('nome', '').strip()
        v_ano = self.request.GET.get('ano', '').strip()
        v_mes = self.request.GET.get('mes','').strip()
        if v_nome:
            queryset = queryset.filter(id_projeto__nome__icontains=v_nome)
        if v_ano:
            queryset = queryset.filter(ano=v_ano)
        if v_mes:
            queryset = queryset.filter(mes=v_mes)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "mes": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", ""),
        }
        return context

class contrapartida_equipamento_create(CreateView):
    model = contrapartida_equipamento
    fields = ['id_projeto', 'ano', 'mes', 'id_equipamento','descricao',  'horas_alocadas','valor_manual']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar cp equipamento", status=403)

    def form_valid(self, form):
        ano = form.cleaned_data.get('ano')
        mes = form.cleaned_data.get('mes')
        proj = form.cleaned_data.get('id_projeto')

        # valida ano/mes preenchidos
        if not ano or not mes:
            form.add_error(None, "Ano e mês são obrigatórios.")
            return self.form_invalid(form)

        data = date(ano, mes, proj.data_inicio.day)

        # valida intervalo de datas
        if not (proj.data_inicio <= data <= proj.data_fim):
            msg = (
                f"Vigência do projeto de "
                f"{proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}."
            )

            if data.year < proj.data_inicio.year or data.year > proj.data_fim.year:
                form.add_error('ano', msg)
            else:
                form.add_error('mes', msg)

            return self.form_invalid(form)

        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, "Erro: contrapartida equipamento inválida.")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))
    
    def criar_contrapartida_equipamento(request):
        equipamentos = equipamento.objects.all()
        horas_restantes = None

        id_equipamento = request.GET.get("id_equipamento")
        mes = request.GET.get("mes")
        ano = request.GET.get("ano")


        if id_equipamento and mes and ano:
            try:
                equipamento_obj = equipamento.objects.get(id=id_equipamento)
                horas_mensais = equipamento_obj.horas_mensais

                horas_usadas = contrapartida_equipamento.objects.filter(
                    id_equipamento=id_equipamento, mes=mes
                ).values_list('horas_mensais', flat=True)
            
                horas_utilizadas=sum(horas_usadas)
           

                horas_restantes = max(0, horas_mensais - horas_utilizadas)

            except equipamento.DoesNotExist:
                horas_restantes = "Equipamento não encontrado"

        return render(request, "/contrapartida/contrapartida_equipamento_form.html", {
            "equipamentos": equipamentos,
            "horas_restantes": horas_restantes,
        })


    def get_success_url(self):
        return reverse_lazy("contrapartida_equipamento_update", kwargs={"pk": self.object.pk})

class contrapartida_equipamento_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida_equipamentos")
   
    model = contrapartida_equipamento
    fields =  ['id_projeto', 'ano', 'mes', 'id_equipamento','descricao', 'horas_alocadas','valor_manual']

    def get_success_url(self):
        return reverse_lazy('contrapartida_equipamento_menu') 
    
    def form_valid(self, form):
        ano = form.cleaned_data.get('ano')
        mes = form.cleaned_data.get('mes')
        proj = form.cleaned_data.get('id_projeto')

        # valida ano/mes preenchidos
        if not ano or not mes:
            form.add_error(None, "Ano e mês são obrigatórios.")
            return self.form_invalid(form)

        data = date(ano, mes, proj.data_inicio.day)

        # valida intervalo de datas
        if not (proj.data_inicio <= data <= proj.data_fim):
            msg = (
                f"Vigência do projeto de "
                f"{proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}."
            )

            if data.year < proj.data_inicio.year or data.year > proj.data_fim.year:
                form.add_error('ano', msg)
            else:
                form.add_error('mes', msg)

            return self.form_invalid(form)

        # salva o objeto antes de tratar as ações
        self.object = form.save()

        action = self.request.POST.get("action")
        if action == "update":
            return redirect("contrapartida_equipamento_update", pk=self.object.pk)
        elif action == "save_exit":
            return redirect("contrapartida_equipamento_menu")

        return super().form_valid(form)

    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        horas_utilizadas = 0
        horas_mensais = 0
        if "form" in context and context["form"].instance.pk:
          id_cp_equipamento = context["form"].instance.pk  # Pega o ID real    
        else:
          id_cp_equipamento = None
        
        cp_equipamento_obj=contrapartida_equipamento.objects.get(id=id_cp_equipamento)
        equipamento_id=cp_equipamento_obj.id_equipamento_id
        equipamento_obj=equipamento.objects.get(id=equipamento_id)
        horas_mensais=equipamento_obj.horas_mensais

        horas_usadas=contrapartida_equipamento.objects.filter(id=cp_equipamento_obj.id,ano=cp_equipamento_obj.ano,mes=cp_equipamento_obj.mes)
        for registro in horas_usadas:
            horas_utilizadas+=registro.horas_alocadas
        
        if horas_mensais!=0:
          context["horas_utilizadas"] = horas_utilizadas
          context["horas_mensais"] = horas_mensais
          context["horas_restantes"] = horas_mensais - horas_utilizadas
        else:
          context["horas_restantes"] = 'sem limite definido' 
         
        return context



class contrapartida_equipamento_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_contrapartida_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir contrapartida_equipamentos")

    model = contrapartida_equipamento
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('contrapartida_equipamento_menu')
    

#################################################################################################################################################
# INSERIR MULTIPLOS
#####################################################################################################################

def contrapartida_equipamento_criar_multiplos(request):
    """
    View para criar múltiplas contrapartidas de equipamento
    O projeto é selecionado primeiro
    """
    
    projeto_obj = None
    projeto_id = request.POST.get('id_projeto') or request.GET.get('id_projeto')
    
    # Busca o projeto se foi informado
    if projeto_id:
        try:
            projeto_obj = projeto.objects.get(id=projeto_id)
        except projeto.DoesNotExist:
            messages.error(request, 'Projeto não encontrado.')
            projeto_obj = None
    
    if request.method == 'POST':
        # Verifica se é apenas seleção de projeto ou submissão do formset
        tem_dados_formset = any(key.startswith('form-') for key in request.POST.keys())
        
        if not projeto_obj:
            messages.error(request, 'Selecione um projeto para continuar.')
            formset = ContrapartidaEquipamentoFormSet(projeto=None)
            
        elif not tem_dados_formset:
            # É apenas seleção de projeto, não valida formset
            # Redireciona para a mesma página com projeto selecionado via GET           
            return redirect(f"{request.path}?id_projeto={projeto_id}")
            
        else:
            # Tem dados do formset, processa normalmente
            formset = ContrapartidaEquipamentoFormSet(request.POST,projeto=projeto_obj)
            
            if formset.is_valid():
                try:
                    with transaction.atomic():
                        instancias_salvas = []
                        
                        for form in formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                # Cria a instância
                                instance = form.save(commit=False)
                                instance.id_projeto = projeto_obj
                                instance.save()
                                instancias_salvas.append(instance)
                        
                        if instancias_salvas:
                            messages.success(
                                request,
                                f'{len(instancias_salvas)} contrapartida(s) cadastrada(s) '
                                f'com sucesso para o projeto "{projeto_obj.nome}"!'
                            )
                            return  redirect('contrapartida_equipamento_menu')
                        else:
                            messages.warning(request, 'Nenhuma contrapartida foi cadastrada.')
                
                except Exception as e:
                    messages.error(request, f'Erro ao salvar: {str(e)}')
            else:
                # Exibe erros de validação
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, str(error))
                
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, f'Linha {i+1} - {field}: {error}')
    else:
        # GET - exibe formulário
        formset = ContrapartidaEquipamentoFormSet(projeto=projeto_obj)
    
    # Lista de projetos para o select
    lista_projetos = projeto.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'formset': formset,
        'projetos': lista_projetos,
        'projeto_obj': projeto_obj,
    }
    
    return render(request, 'contrapartida/contrapartida_equipamento_form_multiplo.html', context)

    

##############################
# CONTRAPARTIDA SO           #
##############################

class contrapartida_so_menu(ListView):
    model = projeto  # Define o modelo explicitamente
    template_name = "contrapartida/contrapartida_so_menu.html"
    context_object_name = "projetos"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para ver Contrapartida SO.")
            return redirect('projeto_menu')

    def get_queryset(self):
        queryset = super().get_queryset()
        projeto = self.request.GET.get('nome', '').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes', '').strip()
        if projeto:
            queryset = queryset.filter(nome__icontains=projeto)
        if ano:
            queryset = queryset.filter(ano=ano)
        if mes:
            queryset = queryset.filter(mes=mes)        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contrapartida_so = []
        
        # Iterar sobre os projetos na queryset para acessar os campos
        for projeto in context['projetos']:
            # Realizando os cálculos necessários para a Contrapartida SO
            so_da_ue = round(projeto.valor_total * projeto.tx_adm_ue /100, 2) - projeto.valor_funape
            so_no_ptr = projeto.valor_so_ptr
            num_meses = projeto.num_mes
        
            if num_meses == 0:
                num_meses = 1  # Evita divisão por zero

            cp_ue_so = so_da_ue - so_no_ptr
            cp_mensal_so = round(cp_ue_so / num_meses, 2)

            # Atribuindo os cálculos diretamente ao objeto projeto
            projeto.so_da_ue =  so_da_ue
            projeto.so_no_ptr =  so_no_ptr
            projeto.cp_ue_so =   cp_ue_so
            projeto.cp_mensal_so = cp_mensal_so
            projeto.num_meses =   num_meses

   
        # Filtros para manter a consistência da UI
            context["filtros"] = {
            "projeto": self.request.GET.get("nome", ""),
            "mes": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", "")
            }
        
        return context
    
class contrapartida_so_menu_new(ListView):
    template_name = 'contrapartida/contrapartida_so_menu_new.html'
    model = projeto  # Define o modelo explicitamente
    context_object_name = "projetos"

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para ver Contrapartida SO.")
            return redirect('projeto_menu')

    def get_queryset(self):
        queryset = super().get_queryset()
        projeto = self.request.GET.get('nome', '').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes', '').strip()
        if projeto:
            queryset = queryset.filter(nome__icontains=projeto)
        if ano:
            queryset = queryset.filter(ano=ano)
        if mes:
            queryset = queryset.filter(mes=mes)        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        linhas = []
        
        # Iterar sobre os projetos na queryset para acessar os campos
        for projeto in context['projetos']:
            # Realizando os cálculos necessários para a Contrapartida SO
            so_da_ue = round(projeto.valor_total * projeto.tx_adm_ue /100, 2) - projeto.valor_funape
            so_no_ptr = projeto.valor_so_ptr
            num_meses = projeto.num_mes or 1    

            cp_ue_so = so_da_ue - so_no_ptr
            cp_mensal_so = round(cp_ue_so / num_meses, 2)

            projeto.so_da_ue =  so_da_ue
            projeto.so_no_ptr =  so_no_ptr
            projeto.cp_ue_so =   cp_ue_so
            projeto.cp_mensal_so = cp_mensal_so
            projeto.num_meses =   num_meses

            linhas.append({
                "nome": projeto.nome,
                "valor_total": projeto.valor_total,
                "valor_financiado": projeto.valor_financiado,                
                "so_da_ue": so_da_ue,
                "so_no_ptr": so_no_ptr,
                "cp_ue_so": cp_ue_so,
                "cp_mensal_so": cp_mensal_so,
                "num_meses": num_meses,
                "data_inicio": projeto.data_inicio,
                "taxa_funape": projeto.valor_funape,
                "detalhes": projeto.id,
            })
         
            
    # Filtros para manter a consistência da UI
        context["filtros"] = {
        "projeto": self.request.GET.get("nome", ""),
        "mes": self.request.GET.get("mes", ""),
        "ano": self.request.GET.get("ano", "")
        }

        table = contrapartida_so_table(linhas)
        RequestConfig(self.request, paginate={"per_page": 10}).configure(table)
        context["table"] = table
        return context


class contrapartida_so_proj(TemplateView):
    template_name = 'contrapartida/contrapartida_so_proj.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtendo o ID do projeto
        id_projeto = self.kwargs.get('id_projeto')
        proj = get_object_or_404(projeto, id=id_projeto)

        # Cálculos base para contrapartida
        so_da_ue = round(proj.valor_total * proj.tx_adm_ue / 100, 2) - proj.valor_funape
        so_no_ptr = proj.valor_so_ptr
        num_meses = (proj.data_fim.year - proj.data_inicio.year) * 12 + (
                    proj.data_fim.month - proj.data_inicio.month)
        if num_meses == 0:
            num_meses = 1  # Para evitar divisão por zero

        # Cálculos da contrapartida
        cp_ue_so = so_da_ue - so_no_ptr
        cp_mensal_so = round(cp_ue_so / num_meses, 2)
        cp_so_proj=contrapartida_so_projeto.objects.filter(id_projeto=proj)
        tabela = contrapartida_so_proj_table(cp_so_proj)
        RequestConfig(self.request).configure(tabela)


        # Adicionando os valores ao contexto
        context['projeto'] = proj
        context['so_da_ue'] = so_da_ue
        context['so_no_ptr'] = so_no_ptr
        context['cp_ue_so'] = cp_ue_so
        context['cp_mensal_so'] = cp_mensal_so
        context['num_meses'] = num_meses

        # Adicionando contrapartidas relacionadas ao projeto
        context['contrapartidas'] = contrapartida_so_projeto.objects.filter(id_projeto=proj)
        context['tabela_proj'] = tabela
        return context

class contrapartida_so_create(CreateView):
    model = contrapartida_so_projeto
    fields = ['ano', 'mes', 'valor']
    template_name = 'contrapartida/contrapartida_so_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.projeto = get_object_or_404(projeto, id=kwargs.get('id_projeto'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.id_projeto = self.projeto
        proj = self.projeto
        ano = form.cleaned_data.get('ano')
        mes = form.cleaned_data.get('mes')
        
        # valida ano/mes preenchidos
        if not ano or not mes:
            form.add_error(None, "Ano e mês são obrigatórios.")
            return self.form_invalid(form)

        data = date(ano, mes, proj.data_inicio.day)
        
        # valida intervalo de datas
        if not (proj.data_inicio <= data <= proj.data_fim):
            msg = (
                f"Vigência do projeto de "
                f"{proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}."
            )

            if data.year < proj.data_inicio.year or data.year > proj.data_fim.year:
                form.add_error('ano', msg)
            else:
                form.add_error('mes', msg)

            return self.form_invalid(form)

        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, "Erro: contrapartida rh inválida.")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))
		

    def get_success_url(self):
        return reverse_lazy('contrapartida_so_projeto', kwargs={'id_projeto': self.projeto.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projeto'] = self.projeto
        return context

class contrapartida_so_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("contrapartida.update_contrapartida_so"):
            return HttpResponse("Sem permissão para atualizar contrapartida SO")
        self.object = self.get_object()
        self.projeto = self.object.id_projeto  # Adiciona aqui a referência ao projeto
        return super().dispatch(request, *args, **kwargs)    
   
    model = contrapartida_so_projeto
    fields = ['ano', 'mes', 'valor']
    template_name = 'contrapartida/contrapartida_so_form.html'

    def form_valid(self, form):
        proj = self.projeto  # ou campo que referencia o projeto
        data = date(form.cleaned_data.get('ano'),form.cleaned_data.get('mes'),proj.data_inicio.day)  # substitua 'data' pelo nome do campo real da data
        
        
        if not (proj.data_inicio <= data <= proj.data_fim):
            msg = (
                f"Vigência do projeto de "
                f"{proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}."
            )

            if data.year < proj.data_inicio.year or data.year > proj.data_fim.year:
                form.add_error('ano', msg)
            else:
                form.add_error('mes', msg)

            return self.form_invalid(form) 
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projeto'] = self.object.id_projeto  # pega o projeto relacionado
        return context    

    def get_success_url(self):
        return reverse_lazy('contrapartida_so_projeto', kwargs={'id_projeto': self.projeto.id})

class contrapartida_so_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir contrapartida SO")

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.projeto = self.object.id_projeto
        return self.object

    model = contrapartida_so_projeto
    fields = []
    template_name = 'contrapartida/contrapartida_so_delete.html'
    def get_success_url(self):
        return reverse_lazy('contrapartida_so_projeto', kwargs={'id_projeto': self.object.id_projeto.id})

#################################################################################################################################################
# INSERIR MULTIPLOS
#####################################################################################################################

def contrapartida_so_criar_multiplos(request):
    """
    View para criar múltiplas contrapartidas de so
    O projeto é selecionado primeiro
    """
    
    projeto_obj = None
    projeto_id = request.POST.get('id_projeto') or request.GET.get('id_projeto')
    
    # Busca o projeto se foi informado
    if projeto_id:
        try:
            projeto_obj = projeto.objects.get(id=projeto_id)
        except projeto.DoesNotExist:
            messages.error(request, 'Projeto não encontrado.')
            projeto_obj = None
    
    if request.method == 'POST':
        # Verifica se é apenas seleção de projeto ou submissão do formset
        tem_dados_formset = any(key.startswith('form-') for key in request.POST.keys())
        
        if not projeto_obj:
            messages.error(request, 'Selecione um projeto para continuar.')
            formset = ContrapartidaSOFormSet(projeto=None)
            
        elif not tem_dados_formset:
            # É apenas seleção de projeto, não valida formset
            # Redireciona para a mesma página com projeto selecionado via GET           
            return redirect(f"{request.path}?id_projeto={projeto_id}")
            
        else:
            # Tem dados do formset, processa normalmente
            formset = ContrapartidaSOFormSet(request.POST,projeto=projeto_obj)
            
            if formset.is_valid():
                try:
                    with transaction.atomic():
                        instancias_salvas = []
                        
                        for form in formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                # Cria a instância
                                instance = form.save(commit=False)
                                instance.id_projeto = projeto_obj
                                instance.save()
                                instancias_salvas.append(instance)
                        
                        if instancias_salvas:
                            messages.success(
                                request,
                                f'{len(instancias_salvas)} contrapartida(s) cadastrada(s) '
                                f'com sucesso para o projeto "{projeto_obj.nome}"!'
                            )
                            return  redirect('contrapartida_so_projeto', id_projeto=projeto_id)
                        else:
                            messages.warning(request, 'Nenhuma contrapartida foi cadastrada.')
                
                except Exception as e:
                    messages.error(request, f'Erro ao salvar: {str(e)}')
            else:
                # Exibe erros de validação
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, str(error))
                
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, f'Linha {i+1} - {field}: {error}')
    else:
        # GET - exibe formulário
        formset = ContrapartidaSOFormSet(projeto=projeto_obj)
    
    # Lista de projetos para o select
    lista_projetos = projeto.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'formset': formset,
        'projetos': lista_projetos,
        'projeto_obj': projeto_obj,
    }
    
    return render(request, 'contrapartida/contrapartida_so_form_multiplo.html', context)



##########################
# CONTRAPARTIDA RH   #####
##########################

class contrapartida_rh_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_contrapartida_rh"):
            return super().dispatch(request, *args, **kwargs)
        else:      
            return HttpResponse("Sem permissão para ver contrapartida rh")

    model = contrapartida_rh
    table_class = contrapartida_rh_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'contrapartida_rh_menu.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome', '').strip()
        pessoa= self.request.GET.get('pessoa','').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes','').strip()
        if nome:
            queryset = queryset.filter(id_projeto__nome__icontains=nome)
        if pessoa:
            queryset= queryset.filter(id_salario__id_pessoa__nome__icontains=pessoa)
        if ano:
            queryset = queryset.filter(id_salario__ano=ano)
        if mes:
            queryset = queryset.filter(id_salario__mes=mes)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "pessoa": self.request.GET.get("pessoa", ""),
            "ano": self.request.GET.get("ano", ""),
            "mes": self.request.GET.get("mes", ""),
        }
        return context

class contrapartida_rh_create(CreateView):
    model = contrapartida_rh
    fields = ['id_projeto', 'id_salario','funcao', 'horas_alocadas']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar cp pesquisa", status=403)

    def form_valid(self, form):
        # Pegue os dados do formulário necessários para validar
        salario_obj=form.cleaned_data.get('id_salario')        
        proj = form.cleaned_data.get('id_projeto')  # ou campo que referencia o projeto
        data = date(salario_obj.ano,salario_obj.mes,proj.data_inicio.day)  # substitua 'data' pelo nome do campo real da data
     
        if data and proj:
            if not (proj.data_inicio <= data <= proj.data_fim):
                form.add_error('id_salario',f"Data fora do período vigência do projeto de {proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}")
                return self.form_invalid(form)
        
        try:
            return super().form_valid(form)
        except IntegrityError as e:
            print("DEBUG IntegrityError:", e)
            return HttpResponse("Erro: Já existe uma contrapartida de rh para este projeto e salário.")   

    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))
    
    def criar_contrapartida_rh(request):
        context = super().get_context_data(**kwargs)

        horas_utilizadas = 0
        horas_mensais = 0

        # Captura o ID do salário selecionado no dropdown (se houver)
        id_salario = self.request.GET.get("id_salario") or self.request.POST.get("id_salario")
        if id_salario:
            try:
                salario_obj = salario.objects.get(id=id_salario)
                pessoa_id = salario_obj.id_pessoa
                mes_ref = salario_obj.mes
                ano_ref = salario_obj.ano
                horas_mensais = (salario_obj.horas_limite or 0) # Total de horas disponíveis para aquele salário

                # Filtra todas as contrapartidas já cadastradas com o mesmo salário
                horas_usadas_pesquisa = contrapartida_pesquisa.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)

                # Soma as horas já utilizadas

                horas_usadas_rh =contrapartida_rh.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)


                horas_utilizadas = sum(horas_usadas_pesquisa) + sum(horas_usadas_rh)

            except salario.DoesNotExist:
                messages.error(self.request, "Salário não encontrado")

        # Adicionando ao contexto
        context["horas_utilizadas"] = horas_utilizadas
        context["horas_mensais"] = horas_mensais
        context["horas_restantes"] = (horas_mensais or 0) - (horas_utilizadas or 0)
        return context

    def get_success_url(self):
        return reverse_lazy('contrapartida_rh_menu')


    def get_success_url(self):
        return reverse_lazy("contrapartida_rh_update", kwargs={"pk": self.object.pk})
    


class contrapartida_rh_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_rh"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida rh")
   
    model = contrapartida_rh
    fields =  ['id_projeto', 'id_salario','funcao', 'horas_alocadas']


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        horas_utilizadas = 0
        horas_mensais = 0

        id_pesquisa = context["form"].instance.pk if "form" in context and context["form"].instance.pk else None
       
        if id_pesquisa:
            try:
                contrapartida = contrapartida_rh.objects.get(id=id_pesquisa)
                salario_id=contrapartida.id_salario_id
                salario_obj=salario.objects.get(id =salario_id)  

                pessoa_id = salario_obj.id_pessoa
                mes_ref = salario_obj.mes
                ano_ref = salario_obj.ano
                horas_mensais = (salario_obj.horas_limite or 0)

                # Filtra todas as contrapartidas já cadastradas com o mesmo salário
                horas_usadas_pesquisa = contrapartida_pesquisa.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)

                # Soma as horas já utilizadas

                horas_usadas_rh =contrapartida_rh.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)


                horas_utilizadas = sum(horas_usadas_pesquisa) + sum(horas_usadas_rh)

            except contrapartida_rh.DoesNotExist:
                   messages.error(self.request, "Contrapartida não encontrada")
            except salario.DoesNotExist:
                   messages.error(self.request, "Salário não encontrado")

    # Adicionando ao contexto
        context["horas_utilizadas"] = horas_utilizadas
        context["horas_mensais"] = horas_mensais
        context["horas_restantes"] = horas_mensais - horas_utilizadas

        return context
        
    def form_valid(self, form):
        self.object = form.save()

        salario_obj=form.cleaned_data.get('id_salario')        
        proj = form.cleaned_data.get('id_projeto')  # ou campo que referencia o projeto
        data = date(salario_obj.ano,salario_obj.mes,proj.data_inicio.day)  # substitua 'data' pelo nome do campo real da data
        if data and proj:
            if not (proj.data_inicio <= data <= proj.data_fim):
                form.add_error('id_salario',f"Data fora do período vigência do projeto de {proj.data_inicio.strftime('%m/%Y')} a {proj.data_fim.strftime('%m/%Y')}")
                return self.form_invalid(form)
    
        action = self.request.POST.get("action")
        if action == "update":
            return redirect("contrapartida_rh_update", pk=self.object.pk)
        elif action == "save_exit":
            return redirect("contrapartida_rh_menu")

        return super().form_valid(form)

    def form_invalid(self, form):
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields.get(field).label if field in form.fields else "Erro"
                messages.error(self.request, f"{field_label}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('contrapartida_rh_menu')   

class contrapartida_rh_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_contrapartida_rh"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir contrapartida rh")

    model = contrapartida_rh
    fields = []
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('contrapartida_rh_menu')    

#################################################################################################################################################
# INSERIR MULTIPLOS
#####################################################################################################################

def contrapartida_rh_criar_multiplos(request):
    """
    View para criar múltiplas contrapartidas de rh
    O projeto é selecionado primeiro e os salários são filtrados por período
    """
    
    projeto_obj = None
    projeto_id = request.POST.get('id_projeto') or request.GET.get('id_projeto')
    
    # Busca o projeto se foi informado
    if projeto_id:
        try:
            projeto_obj = projeto.objects.get(id=projeto_id)
        except projeto.DoesNotExist:
            messages.error(request, 'Projeto não encontrado.')
            projeto_obj = None
    
    if request.method == 'POST':
        # Verifica se é apenas seleção de projeto ou submissão do formset
        tem_dados_formset = any(key.startswith('form-') for key in request.POST.keys())
        
        if not projeto_obj:
            messages.error(request, 'Selecione um projeto para continuar.')
            formset = ContrapartidaRhFormSet(projeto=None)
            
        elif not tem_dados_formset:
            # É apenas seleção de projeto, não valida formset
            # Redireciona para a mesma página com projeto selecionado via GET
            return redirect(f"{request.path}?id_projeto={projeto_id}")
            
        else:
            # Tem dados do formset, processa normalmente
            formset = ContrapartidaRhFormSet(request.POST, projeto=projeto_obj)
            
            if formset.is_valid():
                try:
                    with transaction.atomic():
                        instancias_salvas = []
                        
                        for form in formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                # Cria a instância
                                instance = form.save(commit=False)
                                instance.id_projeto = projeto_obj
                                instance.save()
                                instancias_salvas.append(instance)
                        
                        if instancias_salvas:
                            messages.success(
                                request,
                                f'{len(instancias_salvas)} contrapartida(s) cadastrada(s) '
                                f'com sucesso para o projeto "{projeto_obj.nome}"!'
                            )
                            return redirect('contrapartida_rh_menu')
                        else:
                            messages.warning(request, 'Nenhuma contrapartida foi cadastrada.')
                
                except Exception as e:
                    messages.error(request, f'Erro ao salvar: {str(e)}')
            else:
                # Exibe erros de validação
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        messages.error(request, str(error))
                
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            if field != '__all__':
                                for error in errors:
                                    messages.error(request, f'Linha {i+1} - {field}: {error}')
    else:
        # GET - exibe formulário
        formset = ContrapartidaRhFormSet(projeto=projeto_obj)
    
    # Lista de projetos para o select
    lista_projetos = projeto.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'formset': formset,
        'projetos': lista_projetos,
        'projeto_obj': projeto_obj,
    }
    
    return render(request, 'contrapartida/contrapartida_rh_form_multiplo.html', context)


##############################
# CONTRAPARTIDA REALIZADA    #
##############################
class contrapartida_realizada_list(ListView):
    model = projeto  # Define o modelo explicitamente
    template_name = "contrapartida/contrapartida_realizada_list.html"
    context_object_name = "projetos"
    paginate_by = 10  # Paginação para melhor navegação


    def get_queryset(self):
        queryset = super().get_queryset()
        f_nome = self.request.GET.get('nome', '').strip()
        mes_fim = self.request.GET.get('mes', '').strip()
        ano_fim = self.request.GET.get('ano','').strip()
       ## vlr_total=self.request.GET.get('valor_total')
       ## vlr_financiado =self.request.GET.get('valor_financiado')
       ## vlr_cp_max=vlr_total-vlr_financiado
       ## vlr_cp_max_formatado = locale.format_string('%.2f', vlr_cp_max, grouping=True)
        if f_nome:
            queryset = queryset.filter(nome__icontains=f_nome)
        if mes_fim:
            queryset = queryset.filter(data_fim__month=int(mes_fim))
        if ano_fim:
            queryset = queryset.filter(data_fim__year=int(ano_fim))         
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for projeto in context["projetos"]:
            projeto.mensal_devido = (projeto.contrapartida_max  /projeto.num_mes  if projeto.num_mes else projeto.contrapartida_max)

        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "mes": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", "")           
        }
        return context


def gerar_meses_entre(inicio: date, fim: date) -> list[date]:
    meses = []
    ano, mes = inicio.year, inicio.month

    while (ano, mes) <= (fim.year, fim.month):
        meses.append(date(ano, mes, 1))
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1

    return meses



def contrapartida_realizada_detalhes(request, projeto_id): 

    proj = get_object_or_404(projeto, id=projeto_id)

    vlr_mensal_devido = (proj.contrapartida_max ) /proj.num_mes  if proj.num_mes else proj.contrapartida_max

    contrapartidas_por_mes = defaultdict(lambda: {
        'so': Decimal(0.0),
        'rh': Decimal(0.0),
        'pesquisa': Decimal(0.0),
        'equipamento': Decimal(0.0),
        'prospeccao':Decimal(0.0),
        'total': Decimal(0.0),
        'diferenca': Decimal(0.0)
    })
    saldo=Decimal(0.0)
    contrapartidas_ordenadas = {}

    tipos_contrapartida = ['SO','Rh','Pesquisa','Equipamento','Total', 'Diferenca', 'Saldo']

    todos_meses = gerar_meses_entre(proj.data_inicio, proj.data_fim)

    for date in todos_meses:
        key=f"{date.year}-{date.month:02d}"
        contrapartidas_por_mes[key]


    # Processa contrapartida de SO
    for so in contrapartida_so_projeto.objects.filter(id_projeto=proj):
        key = f"{so.ano}-{so.mes:02d}"
        contrapartidas_por_mes[key]['so'] += Decimal(so.valor or 0)

    # Processa contrapartida de pesquisa
    for c in contrapartida_pesquisa.objects.filter(id_projeto=proj):
        key = f"{c.id_salario.ano}-{c.id_salario.mes:02d}"
        contrapartidas_por_mes[key]['pesquisa'] += c.valor_cp

    # Processa contrapartida de rh
    for c in contrapartida_rh.objects.filter(id_projeto=proj):
        key = f"{c.id_salario.ano}-{c.id_salario.mes:02d}" 
        contrapartidas_por_mes[key]['rh'] += c.valor_cp  

    # Processa contrapartida de equipamento
    for ce in contrapartida_equipamento.objects.filter(id_projeto=proj):
        key = f"{ce.ano}-{ce.mes:02d}"               
        contrapartidas_por_mes[key]['equipamento'] += ce.valor_cp


    # Calcula contrapartida prospeccao
    #contrapartidas_por_mes[key]['prospeccao'] += float(so.valor or 0)

    # Calcula total por mês e diferença
    for key, valores in sorted(contrapartidas_por_mes.items()):
        valores['total'] = valores['equipamento'] + valores['pesquisa'] + valores['so'] + valores['rh'] 
        valores['diferenca'] = valores['total'] - Decimal(vlr_mensal_devido)
        saldo += valores['diferenca']
        valores['saldo'] = saldo
        contrapartidas_ordenadas[key] = valores

    # Ordena os meses do mais antigo para o mais recente
    #contrapartidas_ordenadas = dict(sorted(contrapartidas_por_mes.items()))

    ## Inicio do pivot

    ano_mes = sorted(contrapartidas_ordenadas.keys(), key=lambda x: datetime.strptime(x, "%Y-%m"))

    # Estrutura: {'SO': {'2024-07': 0.0, ...}, 'Pesquisa': {...}, ...}
    dados_transpostos = defaultdict(dict)



    for data in ano_mes:
        valores = contrapartidas_ordenadas[data]
        dados_transpostos['SO'][data] = valores['so']
        dados_transpostos['Rh'][data] = valores['rh']
        dados_transpostos['Pesquisa'][data] = valores['pesquisa']
        dados_transpostos['Equipamento'][data] = valores['equipamento']
        dados_transpostos['Prospeccao'][data] = valores['prospeccao']
        dados_transpostos['Total'][data] = valores['total']
        dados_transpostos['Diferenca'][data] = valores['diferenca']
        dados_transpostos['Saldo'][data] = valores['saldo']

    dados_tabela = []

    for tipo in tipos_contrapartida:
        linha = {
            "tipo": tipo,
            "valores": [dados_transpostos[tipo].get(data, 0.0) for data in ano_mes]
        }
        dados_tabela.append(linha)


    context = {
           'projeto': proj,
           'mensal_devido': vlr_mensal_devido,
           'contrapartidas_por_mes': contrapartidas_ordenadas,
           "ano_mes": ano_mes,  # lista de '2024-07', '2024-08', ...
           "dados_tabela": dados_tabela  # lista de dicionários com tipo + valores ordenados
    }

    return render(request, 'contrapartida/contrapartida_realizada_detalhes.html', context)

##############################
# CONTRAPARTIDA GERAL        #
##############################

def contrapartida_realizada_geral(request):
    # ano padrão (atual) se não vier ou vier vazio
    hoje =datetime.today()
    ano_atual = hoje.year

    ano_str = request.GET.get("ano")
    semestre_str = request.GET.get("semestre")
    
    semestre_atual = 1 if datetime.today().month <= 6 else 2

    if semestre_atual == 1:
        semestre = 2
        ano_default = ano_atual - 1
    else:
        semestre = 1
        ano_default = ano_atual

    # semestre padrão (atual) se não vier ou vier vazio
    
    
    semestre = int(semestre_str) if semestre_str and semestre_str.isdigit() else semestre
    ano = int(ano_str) if ano_str and ano_str.isdigit() else ano_default
    # semestre=1
    # ano=2024
    # ano = request.GET.get("ano")
    # semestre = request.GET.get("semestre")
    # Define limites do semestre
    if semestre == 1:
        inicio_semestre = datetime(ano, 1, 1)
        fim_semestre = datetime(ano, 6, 30)
    else:
        inicio_semestre = datetime(ano, 7, 1)
        fim_semestre = datetime(ano, 12, 31)

    
        # Filtra projetos ativos no semestre
    projetos = projeto.objects.filter(
        data_inicio__lte=fim_semestre,
        data_fim__gte=inicio_semestre

    )
    
    projetos=projetos.order_by()


    dados_tabela = []

    for proj in projetos:
        vlr_mensal_devido = (proj.contrapartida_max / proj.num_mes 
                             if proj.num_mes else proj.contrapartida_max)

        contrapartidas_por_mes = defaultdict(lambda: {
            'so': Decimal(0.0),
            'rh': Decimal(0.0),
            'pesquisa': Decimal(0.0),
            'equipamento': Decimal(0.0),
            'prospeccao': Decimal(0.0),
            'total': Decimal(0.0),
            'diferenca': Decimal(0.0),
            'saldo': Decimal(0.0)
        })

        saldo = Decimal(0.0)
        contrapartidas_ordenadas = {}

        tipos_contrapartida = ['SO', 'Rh', 'Pesquisa', 'Equipamento', 'Prospeccao', 'Total', 'Diferenca', 'Saldo']
        todos_meses = gerar_meses_entre(proj.data_inicio, proj.data_fim)

        for date in todos_meses:
            key = f"{date.year}-{date.month:02d}"
            contrapartidas_por_mes[key]

        # SO
        for so in contrapartida_so_projeto.objects.filter(id_projeto=proj):
            key = f"{so.ano}-{so.mes:02d}"
            contrapartidas_por_mes[key]['so'] += Decimal(so.valor or 0)

        # Pesquisa
        for c in contrapartida_pesquisa.objects.filter(id_projeto=proj):
            key = f"{c.id_salario.ano}-{c.id_salario.mes:02d}"
            contrapartidas_por_mes[key]['pesquisa'] += c.valor_cp

        # RH
        for c in contrapartida_rh.objects.filter(id_projeto=proj):
            key = f"{c.id_salario.ano}-{c.id_salario.mes:02d}"
            contrapartidas_por_mes[key]['rh'] += c.valor_cp

        # Equipamento
        for ce in contrapartida_equipamento.objects.filter(id_projeto=proj):
            key = f"{ce.ano}-{ce.mes:02d}"
            contrapartidas_por_mes[key]['equipamento'] += ce.valor_cp

        # Totais, diferença e saldo
        for key, valores in sorted(contrapartidas_por_mes.items()):
            valores['total'] = valores['equipamento'] + valores['pesquisa'] + valores['so'] + valores['rh']
            valores['diferenca'] = valores['total'] - Decimal(vlr_mensal_devido)
            saldo += valores['diferenca']
            valores['saldo'] = saldo
            contrapartidas_ordenadas[key] = valores

        # Meses ordenados
        ano_mes = sorted(contrapartidas_ordenadas.keys(), key=lambda x: datetime.strptime(x, "%Y-%m"))

        # Pivot
        dados_transpostos = defaultdict(dict)
        for data in ano_mes:
            valores = contrapartidas_ordenadas[data]
            dados_transpostos['SO'][data] = valores['so']
            dados_transpostos['Rh'][data] = valores['rh']
            dados_transpostos['Pesquisa'][data] = valores['pesquisa']
            dados_transpostos['Equipamento'][data] = valores['equipamento']
            dados_transpostos['Prospeccao'][data] = valores['prospeccao']
            dados_transpostos['Total'][data] = valores['total']
            dados_transpostos['Diferenca'][data] = valores['diferenca']
            dados_transpostos['Saldo'][data] = valores['saldo']

        linhas = []
        for tipo in tipos_contrapartida:
            linha = {
                "tipo": tipo,
                "valores": [dados_transpostos[tipo].get(data, 0.0) for data in ano_mes]
            }
            linhas.append(linha)

        dados_tabela.append({
            'projeto': proj,
            'ano_mes': ano_mes,
            'linhas': linhas
        })

    context = {
        'ano': ano,
        'semestre': semestre,
        'dados_tabela': dados_tabela
        
    }

    return render(request, 'contrapartida/contrapartida_realizada_geral.html', context)

#######################################
# CONTRAPARTIDA REALIZADA EQUIPAMENTO #
#######################################

def contrapartida_realizada_equipamento(request):
    hoje = datetime.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    ano_str = request.GET.get("ano")
    semestre_str = request.GET.get("semestre")

    if semestre_atual == 1:
        semestre_default = 2
        ano_default = ano_atual - 1
    else:
        semestre_default = 1
        ano_default = ano_atual

    ano = int(ano_str) if ano_str and ano_str.isdigit() else ano_default
    semestre = int(semestre_str) if semestre_str and semestre_str.isdigit() else semestre_default

    # Limites do semestre
    if semestre == 1:
        inicio_semestre = datetime(ano, 1, 1)
        fim_semestre = datetime(ano, 6, 30)
    else:
        inicio_semestre = datetime(ano, 7, 1)
        fim_semestre = datetime(ano, 12, 31)

    # Lista de meses dentro do semestre
    meses_semestre = []
    dt = inicio_semestre
    while dt <= fim_semestre:
        meses_semestre.append(f"{dt.year}-{dt.month:02d}")
        dt = datetime(dt.year + (dt.month // 12), (dt.month % 12) + 1, 1)

    # Projetos ativos no semestre
    projetos = projeto.objects.filter(
        data_inicio__lte=fim_semestre,
        data_fim__gte=inicio_semestre
    ).order_by("data_fim")  # Data fim mais próxima primeiro

    equipamentos_lista = list(equipamento.objects.all())

    # Dados da tabela
    dados_tabela = []
    tabela=[]


    todos_meses = gerar_meses_entre(inicio_semestre, fim_semestre)
       
    for proj in projetos:
        linha = {
            "projeto": proj,
            "meses": []
        }
        valores = []
        total = 0                
        for data  in todos_meses:
            colunas=[]
            total_mes=0
            cp_obj_list=contrapartida_equipamento.objects.filter(id_projeto=proj, ano=data.year, mes=data.month)

            soma = sum( [cp.valor_cp for cp in cp_obj_list]
            )              
            valores.append(soma)
            total_mes += soma

            for equip in equipamentos_lista:
                horas= sum( [cp.horas_alocadas  for cp in cp_obj_list  if cp.id_equipamento==equip ])
                colunas.append(horas)
            linha["meses"].append({
                "data": data,
                "equipamentos": colunas,
                "total_mes": soma,
                })

        tabela.append(linha)

    context = {
    "tabela": tabela,
    'ano': ano,
    'semestre': semestre,
    "meses": todos_meses,
    "equipamentos": equipamentos_lista,
                }

    return render(request,"contrapartida/contrapartida_realizada_equipamento.html", context)

def contrapartida_realizada_pesquisa(request):
    hoje = datetime.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    ano_str = request.GET.get("ano")
    semestre_str = request.GET.get("semestre")

    if semestre_atual == 1:
        semestre_default = 2
        ano_default = ano_atual - 1
    else:
        semestre_default = 1
        ano_default = ano_atual

    ano = int(ano_str) if ano_str and ano_str.isdigit() else ano_default
    semestre = int(semestre_str) if semestre_str and semestre_str.isdigit() else semestre_default

    # Limites do semestre
    if semestre == 1:
        inicio_semestre = datetime(ano, 1, 1)
        fim_semestre = datetime(ano, 6, 30)
    else:
        inicio_semestre = datetime(ano, 7, 1)
        fim_semestre = datetime(ano, 12, 31)

    meses_semestre = gerar_meses_entre(inicio_semestre, fim_semestre)

    projetos = projeto.objects.filter(
        data_inicio__lte=fim_semestre,
        data_fim__gte=inicio_semestre
    ).order_by("nome")

    tabela = []

    for proj in projetos:
        linha = {
            "projeto": proj,
            "pesquisadores": []
        }

        # Pega todos os pesquisadores do projeto
        pessoas = contrapartida_pesquisa.objects.filter(id_projeto=proj).values_list(
            "id_salario__id_pessoa__nome", flat=True
        ).distinct()

        for pessoa in pessoas:
            dados_pessoa = {
                "nome": pessoa,
                "horas_media": 0,
                "meses": []
            }

            horas_totais = 0
            meses_com_horas = 0

            for mes in meses_semestre:
                cp_reg = contrapartida_pesquisa.objects.filter(
                    id_projeto=proj,
                    id_salario__id_pessoa__nome=pessoa,
                    id_salario__ano=mes.year,
                    id_salario__mes=mes.month
                ).first()
                
                if cp_reg: 
                    print(cp_reg.id_salario.id_pessoa)
                    if cp_reg.id_salario.id_pessoa=="Guilherme Tai":
                        print(cp_reg.valor_cp)

                valor_cp = cp_reg.valor_cp if cp_reg else 0
                horas_mes = cp_reg.horas_alocadas if cp_reg else 0

                dados_pessoa["meses"].append(valor_cp)

                if horas_mes:
                    horas_totais += horas_mes
                    meses_com_horas += 1

            dados_pessoa["horas_media"] = round(horas_totais / meses_com_horas, 1) if meses_com_horas else 0

            linha["pesquisadores"].append(dados_pessoa)

        tabela.append(linha)

    context = {
        "ano": ano,
        "semestre": semestre,
        "tabela": tabela,
        "meses": meses_semestre,
    }

    return render(request, "contrapartida/contrapartida_realizada_pesquisa.html", context)

def contrapartida_realizada_rh(request):
    hoje = datetime.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    ano_str = request.GET.get("ano")
    semestre_str = request.GET.get("semestre")

    if semestre_atual == 1:
        semestre_default = 2
        ano_default = ano_atual - 1
    else:
        semestre_default = 1
        ano_default = ano_atual

    ano = int(ano_str) if ano_str and ano_str.isdigit() else ano_default
    semestre = int(semestre_str) if semestre_str and semestre_str.isdigit() else semestre_default

    # Limites do semestre
    if semestre == 1:
        inicio_semestre = datetime(ano, 1, 1)
        fim_semestre = datetime(ano, 6, 30)
    else:
        inicio_semestre = datetime(ano, 7, 1)
        fim_semestre = datetime(ano, 12, 31)

    meses_semestre = gerar_meses_entre(inicio_semestre, fim_semestre)

    projetos = projeto.objects.filter(
        data_inicio__lte=fim_semestre,
        data_fim__gte=inicio_semestre
    ).order_by("nome")

    tabela = []

    for proj in projetos:
        linha = {
            "projeto": proj,
            "pessoas": []
        }

        # Pega todos os pesquisadores do projeto
        pessoas = contrapartida_rh.objects.filter(id_projeto=proj).values_list(
            "id_salario__id_pessoa__nome", flat=True
        ).distinct()

        for pessoa in pessoas:
            dados_pessoa = {
                "nome": pessoa,
                "horas_media": 0,
                "meses": []
            }

            horas_totais = 0
            meses_com_horas = 0

            for mes in meses_semestre:
                cp_reg = contrapartida_rh.objects.filter(
                    id_projeto=proj,
                    id_salario__id_pessoa__nome=pessoa,
                    id_salario__ano=mes.year,
                    id_salario__mes=mes.month
                ).first()
                
                valor_cp = cp_reg.valor_cp if cp_reg else 0
                horas_mes = cp_reg.horas_alocadas if cp_reg else 0

                dados_pessoa["meses"].append(valor_cp)

                if horas_mes:
                    horas_totais += horas_mes
                    meses_com_horas += 1

            dados_pessoa["horas_media"] = round(horas_totais / meses_com_horas, 1) if meses_com_horas else 0

            linha["pessoas"].append(dados_pessoa)

        tabela.append(linha)

    context = {
        "ano": ano,
        "semestre": semestre,
        "tabela": tabela,
        "meses": meses_semestre,
    }

    return render(request, "contrapartida/contrapartida_realizada_rh.html", context)

##############################
# DOWNLOAD DO BANCO DE DADOS #
##############################

def download_database(request):
    """View para download do arquivo do banco de dados"""
    file_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = 'attachment; filename="db.sqlite3"'
    return response

##########################
# UPLOAD DE CONTRACHEQUE #
##########################
def upload_contracheque(request):
    if request.method == 'POST' and 'pdf_files' in request.FILES:
        pdf_files = request.FILES.getlist('pdf_files')
        for pdf_file in pdf_files:
            reader = PdfReader(pdf_file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()

            try:
                nome_linha = text.splitlines()[9]
                nome = re.match(r"^[A-Za-zÀ-ú ]+", nome_linha).group(0).strip()

                cpf_linha = text.splitlines()[11]
                cpf = re.search(r"(\d{11})$", cpf_linha).group(1)

                salario_bruto_linha = text.splitlines()[-5]
                valores = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})", salario_bruto_linha)
                salario_bruto = float(valores[2].replace('.', '').replace(',', '.'))

                mes_referencia_linha = text.splitlines()[14]
                mes_abreviado, ano = mes_referencia_linha.split()
                ano = int(ano)
                meses_pt = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                mes = meses_pt.index(mes_abreviado.upper()) + 1

                try:
                    pessoa_obj, created = pessoa.objects.get_or_create(nome=nome, cpf=cpf, ativo=True)
                    salario_obj, salario_created = salario.objects.get_or_create(
                        id_pessoa=pessoa_obj,
                        mes=mes,
                        ano=ano,
                        defaults={
                            'valor': salario_bruto,
                            'horas': 160,
                            'anexo': pdf_file,
                        }
                    )
                    if not salario_created:
                        if not salario_obj.anexo:
                            salario_obj.anexo = pdf_file
                            salario_obj.save()
                            messages.success(request, f"Arquivo de contracheque atualizado para {nome} ({mes}/{ano}).")
                        else:
                            messages.warning(request, f"Contracheque já cadastrado para {nome} ({mes}/{ano}).")
                    else:
                        messages.success(request, f"Salário inserido com sucesso para {nome} ({mes}/{ano}).")

                except Exception as e:
                    messages.error(request, f"Erro ao processar o arquivo para {nome}: {str(e)}")

            except (IndexError, AttributeError, ValueError) as e:
                messages.error(request, f"Erro ao extrair informações do arquivo {pdf_file.name}: {str(e)}")

        return redirect('upload_contracheque')

    return render(request, 'upload.html')


def verifica_contracheque(request):
    pessoas = pessoa.objects.all()
    context = {}

    if request.method == 'POST':
        pessoa_id = request.POST.get('pessoa_id')
        pessoa_obj = pessoa.objects.get(id=pessoa_id)
        # Filtrar salários da pessoa que não possuem anexo ou cujo anexo é 0

        salarios_sem_anexo = salario.objects.filter(
            id_pessoa=pessoa_obj
        ).filter(
            Q(anexo__isnull=True) | Q(anexo='') | Q(anexo='0') | Q(anexo='False')
        )


        # Preparar informações para o e-mail
        meses_sem_anexo = [
            f"{calendar.month_name[s.mes]} de {s.ano}" for s in salarios_sem_anexo
        ]
        email_conteudo = (
            f"Olá {pessoa_obj.nome},\n\n"
            "Identificamos que você não possui contracheques anexados para os seguintes meses:\n\n"
            + "\n".join(meses_sem_anexo)
            + "\n\nPor favor, envie os contracheques pendentes o mais rápido possível.\n\n"
            "Atenciosamente,"
        )

        # Enviar e-mail se solicitado
        if 'enviar_email' in request.POST:
            send_mail(
                subject="Pendência de Contracheques",
                message=email_conteudo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[pessoa_obj.email],
            )
            messages.success(request, f"E-mail enviado para {pessoa_obj.nome} com sucesso!")

        context = {
            'pessoa_selecionada': pessoa_obj,
            'salarios_sem_anexo': salarios_sem_anexo,
            'email_conteudo': email_conteudo,
        }

    context['pessoas'] = pessoas
    return render(request, 'verifica_contracheque.html', context)

