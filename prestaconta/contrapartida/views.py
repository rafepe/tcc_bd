from .models import *
from .tables import *
from datetime import datetime
from django_tables2 import SingleTableView
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
import csv
import io


from django.contrib.auth import authenticate, login, logout
def index(request):
    usuario = request.POST.get('username')
    senha = request.POST.get('password')
    user = authenticate(username=usuario, password=senha)
    if (user is not None):
        login(request, user)
        request.session['username'] = usuario
        request.session['password'] = senha
        request.session['usernamefull'] = user.get_full_name()

        from django.shortcuts import redirect
        return redirect('procedimento_menu')
    else:       
        return render(request, 'index.html')


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
                id, nome, data_inicio_str, data_fim_str, valor_str = row 

                try:
                    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
                except ValueError:
                    return HttpResponse(f"Formato de data inválido: {data_inicio_str}", status=400)
                
                try:
                    data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y").date()
                except ValueError:
                    return HttpResponse(f"Formato de data inválido: {data_fim_str}", status=400)
                valor = float(valor_str.replace(",", "."))
                projeto.objects.create(id=id, nome=nome, data_inicio=data_inicio, data_fim=data_fim, valor=valor)
            return HttpResponse("Arquivo CSV importado para o modelo Projeto com sucesso!")
        
        elif model_choice == 'equipamento':
            for row in csv_reader:
                id, nome, valor_aquisicao, quantidade_nos, cvc, cma = row
                equipamento.objects.create(id=id, nome=nome, valor_aquisicao=valor_aquisicao, quantidade_nos=quantidade_nos, cvc=cvc, cma=cma)
            return HttpResponse("Arquivo CSV importado para o modelo Equipamento com sucesso!")
        
        elif model_choice == 'salario':
            for row in csv_reader:
                id_pessoa, referencia, valor = row

                salario.objects.create(id_pessoa_id=id_pessoa, referencia=referencia, valor=valor)

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
            return HttpResponse("Sem permissão para ver projetos")

    model = projeto
    table_class = projeto_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'projeto_menu.html'

class projeto_create(CreateView):
    model = projeto
    fields = ['nome', 'peia', 'data_inicio', 'data_fim', 'valor_total', 'valor_financiado', 'tx_administrativa', 'contrapartida_prometida', 'ativo']


    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar projetos")

    def get_success_url(self):
        return reverse_lazy('projeto_menu')

class projeto_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar projetos")
   
    model = projeto
    fields = ['nome','data_inicio', 'data_fim', 'valor','contrapartida_prometida']
    def get_success_url(self):
        return reverse_lazy('projeto_menu')   

class projeto_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_projeto"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir projetos")

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
            return HttpResponse("Sem permissão para ver equipamentos")

    model = equipamento
    table_class = equipamento_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'equipamento_menu.html'

class equipamento_create(CreateView):
    model = equipamento
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar equipamentos")

    def get_success_url(self):
        return reverse_lazy('equipamento_menu')

class equipamento_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar equipamentos")
   
    model = equipamento
    fields = ['nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma']
    def get_success_url(self):
        return reverse_lazy('equipamento_menu')   

class equipamento_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_equipamento"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir equipamentos")

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
            return HttpResponse("Sem permissão para criar pessoas")

    def get_success_url(self):
        return reverse_lazy('pessoa_menu')

class pessoa_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_pessoa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar pessoas")
   
    model = pessoa
    fields = ['nome', 'ativo']
    def get_success_url(self):
        return reverse_lazy('pessoa_menu')   

class pessoa_delete(DeleteView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.delete_pessoa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para excluir pessoas")

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
            return HttpResponse("Sem permissão para ver salários")

    model = salario
    table_class = salario_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 10}
    template_name = 'salario_menu.html'

class salario_create(CreateView):
    model = salario
    fields = ['id_pessoa', 'referencia', 'valor']

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.create_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para criar salários", status=403)

    def form_valid(self, form):
        try:
            return super().form_valid(form)  # Tenta salvar o salário
        except IntegrityError:
            return HttpResponse("Erro: O salário para esta pessoa e referência já existe.")

    def get_success_url(self):
        return reverse_lazy('salario_menu')

class salario_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_salario"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar salarios")
   
    model = salario
    fields = ['id_pessoa','referencia','valor']

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

from django.views.generic import ListView
from django.utils.timezone import now
from django.shortcuts import render
from datetime import datetime
from .models import projeto

def get_semestre_atual():
    """Retorna o ano e o semestre atual"""
    hoje = now().date()
    ano = hoje.year
    semestre = 1 if hoje.month <= 6 else 2
    return ano, semestre

class projetos_semestre(ListView):
    model = projeto
    template_name = "projetos_semestre.html"
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
        print(qs.query)

        return projeto.objects.filter(data_fim__range=(data_inicio, data_fim))

    def get_context_data(self, **kwargs):
        """Adiciona os filtros ao contexto"""
        context = super().get_context_data(**kwargs)
        context["ano_atual"], context["semestre_atual"] = get_semestre_atual()
        context["ano_selecionado"] = self.request.GET.get("ano", context["ano_atual"])
        context["semestre_selecionado"] = self.request.GET.get("semestre", context["semestre_atual"])
        print(context)
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
    fields = ['projeto', 'nome', 'referencia', 'horas_alocadas']
    template_name = 'contrapartida_pesquisa_form.html'
    success_url = reverse_lazy('contrapartida:contrapartida_pesquisa_menu')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pegando todos os projetos disponíveis
        context['projetos'] = projeto.objects.all()

        # Pegando apenas os nomes das pessoas que possuem salários registrados
        pessoas_com_salario = (
            salario.objects.filter(id_pessoa__isnull=False)
            .values_list('id_pessoa__nome', flat=True)
            .distinct()
        )
        context['pessoas'] = list(pessoas_com_salario)  # Convertendo para lista para facilitar no template

        # Obtendo a pessoa selecionada
        pessoa_id = self.request.GET.get('pessoa')
        referencia_id = self.request.GET.get('referencia')

        if pessoa_id:
            # Filtrando os salários pela pessoa e pela referência
            salarios = salario.objects.filter(id_pessoa_id=pessoa_id).exclude(valor__isnull=True, horas__isnull=True)
            
            if referencia_id:
                salarios = salarios.filter(id=referencia_id)  # Filtra pela referência também

            context['salarios'] = salarios

            if salarios.exists():
                pessoa_nome = salarios.first().id_pessoa.nome
                context['pessoa_nome'] = pessoa_nome
            else:
                context['pessoa_nome'] = "Pessoa não encontrada"

        else:
            context['salarios'] = []
            context['pessoa_nome'] = None

        return context


class contrapartida_pesquisa_update(UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("contrapartida.update_contrapartida_pesquisa"):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Sem permissão para atualizar contrapartida_pesquisas")
   
    model = contrapartida_pesquisa
    fields = ['valor','horas']

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
       
    
