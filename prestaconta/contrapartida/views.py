
from .models import projeto, equipamento, pessoa, salario
from .tables import projeto_table, equipamento_table, pessoa_table, salario_table
from django_tables2 import SingleTableView
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from datetime import datetime  # Importando o módulo para manipulação de datas
# Create your views here.

import io
import csv
from django.shortcuts import render
from django.http import HttpResponse
from .models import pessoa, projeto  # Importando ambos os modelos

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
    template_name = 'contrapartida/projeto_menu.html'

class projeto_create(CreateView):
    model = projeto
    fields = ['nome', 'data_inicio', 'data_fim', 'valor']

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
    fields = ['nome','data_inicio', 'data_fim', 'valor']
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




###########
# PROJETO #
###########

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
    template_name = 'contrapartida/equipamento_menu.html'

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
    template_name = 'contrapartida/pessoa_menu.html'

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
   
import django_tables2 as tables
from .models import salario
from django.shortcuts import render


from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import salario

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
    template_name = 'contrapartida/salario_menu.html'



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
    

