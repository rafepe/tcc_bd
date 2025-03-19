from .models import *
from .tables import *
from datetime import datetime
from django_tables2 import SingleTableView
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect, render , get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
import csv
from django.http import JsonResponse
import io
import locale    
from collections import defaultdict
from .models import projeto, contrapartida_pesquisa, contrapartida_equipamento #, contrapartidaSO
import os
from django.conf import settings

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
        context["filtros"] = {
      
            "nome": self.request.GET.get("nome", ""),
            "mes": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", "")
        }
        
        return context




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

    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome', '').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes','').strip()
        if nome:
            queryset = queryset.filter(id_projeto__nome__icontains=nome)
        if ano:
            queryset = queryset.filter(id_salario__ano=ano)
        if mes:
            queryset = queryset.filter(id_salario__mes=mes)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "data_fim": self.request.GET.get("data_fim", ""),
        }
        return context



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
                horas_mensais = salario_obj.horas  # Total de horas disponíveis para aquele salário

                # Filtra todas as contrapartidas já cadastradas com o mesmo salário
                horas_usadas = contrapartida_pesquisa.objects.filter(
                    id_salario__id_pessoa=pessoa_id,
                    id_salario__mes=mes_ref,
                    id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)

                horas_utilizadas = sum(horas_usadas)  # Soma as horas já utilizadas

            except salario.DoesNotExist:
                messages.error(self.request, "Salário não encontrado")

        # Adicionando ao contexto
        context["horas_utilizadas"] = horas_utilizadas
        context["horas_mensais"] = horas_mensais
        context["horas_restantes"] = horas_mensais - horas_utilizadas

        return render(request, "\contrapartida\contrapartida_pesquisa_form.html", {
            "salarios": id_salario,
            "horas_restantes": horas_restantes,
        })  
    def get_success_url(self):
        return reverse_lazy("contrapartida_pesquisa_update", kwargs={"pk": self.object.pk})
    



class contrapartida_pesquisa_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida_pesquisas")
   
    model = contrapartida_pesquisa
    fields =  ['id_projeto', 'id_salario', 'horas_alocadas']


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
                horas_mensais = salario_obj.horas

                horas_usadas = contrapartida_pesquisa.objects.filter(
                   id_salario__id_pessoa=pessoa_id,
                   id_salario__mes=mes_ref,
                   id_salario__ano=ano_ref
                ).values_list('horas_alocadas', flat=True)

                horas_utilizadas = sum(horas_usadas)  # Somamos direto os valores

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
        if action == "update":
            return redirect("contrapartida_pesquisa_update", pk=self.object.pk)
        elif action == "save_exit":
            return redirect("contrapartida_pesquisa_menu")

        return super().form_valid(form)

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

        return render(request, "\contrapartida\contrapartida_equipamento_form.html", {
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
    fields =  ['id_projeto', 'ano', 'mes', 'id_equipamento', 'horas_alocadas']

    def get_success_url(self):
        return reverse_lazy('contrapartida_equipamento_menu') 
    
    def form_valid(self, form):
        self.object = form.save()

        action = self.request.POST.get("action")
        if action == "update":
            return redirect("contrapartida_equipamento_update", pk=self.object.pk)
        elif action == "save_exit":
            return redirect("contrapartida_equipamento_menu")

        return super().form_valid(form)

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
##############################
# CONTRAPARTIDA SO           #
##############################
class contrapartida_so_list(ListView):
    model = projeto  # Define o modelo explicitamente
    template_name = "contrapartida/contrapartida_so_list.html"
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
            num_meses = (projeto.data_fim.year - projeto.data_inicio.year) * 12 + (projeto.data_fim.month - projeto.data_inicio.month)
        
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


class contrapartida_so_menu(SingleTableView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.view_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(self.request, "Usuário sem permissão para ver Contrapartida SO.")
            return redirect('projeto_menu')

    model = contrapartida_so
    table_class = contrapartida_so_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'contrapartida_so_menu.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        projeto = self.request.GET.get('nome', '').strip()
        ano = self.request.GET.get('ano', '').strip()
        mes = self.request.GET.get('mes','').strip()
        if projeto:
            queryset = queryset.filter(id_pessoa__nome__icontains=projeto)
        if ano:
            queryset = queryset.filter(ano=ano)
        if mes:
            queryset = queryset.filter(mes=mes)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filtros"] = {
      
            "projeto": self.request.GET.get("nome", ""),
            "mes": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", "")
        }
        
        return context

class contrapartida_so_create(CreateView):
    model = contrapartida_so
    fields = ['id_pessoa','ano', 'mes', 'valor', 'horas']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar contrapartida SO", status=403)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            return HttpResponse("Erro: O contrapartida So para esta mes já existe.")


    def form_invalid(self, form):
        errors = form.errors.as_text()  # Converte os erros para texto
        messages.error(self.request, f"Erro ao salvar o projeto: {errors}")  
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('contrapartida_so_menu')

class contrapartida_so_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida SO")
   
    model = contrapartida_so
    fields = ['id_pessoa','ano', 'mes', 'valor', 'horas']

    def get_success_url(self):
        return reverse_lazy('contrapartida_so_menu')   

class contrapartida_so_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_contrapartida_so"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir contrapartida SO")

    model = contrapartida_so
    fields = []
    template_name_suffix = '_delete'
    def get_success_url(self):
        return reverse_lazy('contrapartida_so_menu')



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
        context["filtros"] = {
            "nome": self.request.GET.get("nome", ""),
            "data_fim": self.request.GET.get("mes", ""),
            "ano": self.request.GET.get("ano", "")           
        }
        return context




def contrapartida_realizada_detalhes(request, projeto_id):
    proj = get_object_or_404(projeto, id=projeto_id)

    # Calcula número de meses do projeto
    num_meses = (proj.data_fim.year - proj.data_inicio.year) * 12 + (proj.data_fim.month - proj.data_inicio.month)
    
    # Calcula Valor Mensal Devido
    vlr_mensal_devido = (proj.contrapartida_max ) /num_meses  if num_meses else 0.0
    # Dicionário para armazenar os totais por mês

    # Formata os valores antes de enviar ao template
    vlr_cp_max_formatado = locale.format_string('%.2f', proj.contrapartida_max, grouping=True)
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
           'vlr_mensal_devido': vlr_mensal_devido_formatado,  # Adicionado ao contexto
           'contrapartidas_por_mes': contrapartidas_ordenadas,
    }

    return render(request, 'contrapartida/contrapartida_realizada_detalhes.html', context)

def download_database(request):
    """View para download do arquivo do banco de dados"""
    file_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = 'attachment; filename="db.sqlite3"'
    return response
