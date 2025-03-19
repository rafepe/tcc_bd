from .models import *
from django_tables2.utils import A
from django.db.models import Func, IntegerField, F
from django.urls import reverse
from django.utils.dateformat import DateFormat
from django.utils.html import format_html
import django_tables2 as tables
import locale
from django.utils.html import format_html

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class projeto_table(tables.Table):
    nome = tables.LinkColumn("projeto_update",orderable=True, args=[A("pk")])
    peia = tables.LinkColumn("projeto_update",orderable=True ,args=[A("pk")])
    data_inicio = tables.LinkColumn("projeto_update", args=[A("pk")])
    data_fim = tables.LinkColumn("projeto_update", args=[A("pk")])
    valor_total = tables.LinkColumn("projeto_update", args=[A("pk")])
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")

    class Meta:
        model = projeto
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields =    ("nome", "peia", "data_inicio", "data_fim", "valor_total", "excluir")
        sequence =  ("nome", "peia", "data_inicio", "data_fim", "valor_total", "excluir")
    
    def render_data_inicio(self, value):
        # Formatar a data no formato DD/MM/YYYY
        if value is not None:
            formatted_date = DateFormat(value).format('d/m/Y')
            return format_html('<span>{}</span>', formatted_date)
        return '-'

    def render_data_fim(self, value):
        # Formatar a data no formato DD/MM/YYYY
        if value is not None:
            formatted_date = DateFormat(value).format('d/m/Y')
            return format_html('<span>{}</span>', formatted_date)
        return '-'

    def render_valor_total(self, value):
        # Formatar o valor como moeda
        if value is not None:
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)
        return '-'

    def render_excluir(self, record):
        url = reverse("projeto_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)

class equipamento_table(tables.Table):
    nome = tables.LinkColumn("equipamento_update", args=[A("pk")])
    valor_aquisicao = tables.LinkColumn("equipamento_update", args=[A("pk")])
    quantidade_nos = tables.LinkColumn("equipamento_update", args=[A("pk")], verbose_name="Qtde Nós")
    cvc = tables.LinkColumn("equipamento_update", args=[A("pk")], verbose_name="CVC")
    cma = tables.LinkColumn("equipamento_update", args=[A("pk")], verbose_name="CMA")    
    valor_hora = tables.Column(empty_values=())
    horas_mensais = tables.LinkColumn("equipamento_update", args=[A("pk")], verbose_name="Horas Mensais")
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")
    class Meta:
        model = equipamento
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields =    ('nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma', 'valor_hora', 'ativo')
        sequence =  ('nome', 'valor_aquisicao', 'quantidade_nos', 'cvc', 'cma', 'valor_hora', 'ativo') 

    def render_valor_aquisicao(self, value):
        if value is not None:
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)  # Exibe o valor com o símbolo R$
        return '-'
    
    def render_cvc(self, value):
        if value is not None:
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)  # Exibe o valor com o símbolo R$
        return '-'

    def render_cma(self, value):
        if value is not None:
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)  # Exibe o valor com o símbolo R$
        return '-'

    def render_valor_hora(self, record):
        if record.nome in ['DGX-1','DGX-A100','DGX-H100']:
          value = (( (0.1*record.valor_aquisicao) + record.cvc + record.cma ) / 1200) / record.quantidade_nos
        else:
          value = ( ( (0.1*record.valor_aquisicao) + record.cvc + record.cma ) / 1440 ) / record.quantidade_nos
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value)  # Exibe o valor com o símbolo R$   
    
    def render_excluir(self, record):
        url = reverse("equipamento_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)

class pessoa_table(tables.Table):
    nome = tables.LinkColumn("pessoa_update", args=[A("pk")])
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")

    class Meta:
        model = pessoa
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome','ativo')

    def render_excluir(self, record):
        url = reverse("pessoa_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)


class salario_table(tables.Table):
    pessoa = tables.LinkColumn("salario_update", args=[A("pk")], accessor='id_pessoa.nome', verbose_name="Pessoa")
    ano = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Ano de Referência")
    mes = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Mês de Referência")
    valor = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Valor")
    horas = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Horas mensais")
    valor_hora = tables.Column(empty_values=(), verbose_name="Valor-Hora", orderable=False)
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")

    class Meta:
        model = salario
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('pessoa', 'ano', 'mes', 'valor', 'horas', 'valor_hora','excluir')

    def render_valor_hora(self, record):
        if record.valor and record.horas and record.horas != 0:
            value = round(record.valor / record.horas, 2)
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)
        return 0
    
    def render_valor(self, value):
        if value is not None:
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)
        return '-'

    def render_excluir(self, record):
        url = reverse("salario_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)



class contrapartida_pesquisa_table(tables.Table):
    id_projeto = tables.LinkColumn("contrapartida_pesquisa_update", args=[A("pk")], verbose_name="Projeto")
    id_salario = tables.LinkColumn("contrapartida_pesquisa_update", args=[A("pk")], verbose_name="Salário")
    horas_alocadas = tables.LinkColumn("contrapartida_pesquisa_update", args=[A("pk")], verbose_name="Horas Alocadas")
    valor_hora = tables.Column(empty_values=(), verbose_name="Valor-Hora", orderable=False)
    valor_cp = tables.Column(empty_values=(), verbose_name="Valor Contrapartida", orderable=False)
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")


    def render_valor_hora(self, record):
        if record.id_salario.valor and record.id_salario.horas and record.id_salario.horas != 0:
            value = round(record.id_salario.valor/ record.id_salario.horas, 2)
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)  # Exibe o valor com o símbolo R$
        return 0
    
    def render_valor_cp(self, record):
        if record.id_salario.valor and record.id_salario.horas and record.id_salario.horas != 0:
            value = round(record.horas_alocadas * record.id_salario.valor/ record.id_salario.horas, 2)
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value) 
        return 0

    def render_excluir(self, record):
        url = reverse("contrapartida_pesquisa_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)
    
    
    class Meta:
        model = contrapartida_pesquisa
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('id_projeto', 'id_salario', 'horas_alocadas')

class contrapartida_equipamento_table(tables.Table):
    id_projeto = tables.LinkColumn("contrapartida_equipamento_update", args=[A("pk")], verbose_name="Projeto")
    mes = tables.LinkColumn("contrapartida_equipamento_update", args=[A("pk")], verbose_name="Mês")
    ano = tables.LinkColumn("contrapartida_equipamento_update", args=[A("pk")], verbose_name="Ano")
    id_equipamento = tables.LinkColumn("contrapartida_equipamento_update", args=[A("pk")], verbose_name="Equipamento")
    horas_alocadas = tables.LinkColumn("contrapartida_equipamento_update", args=[A("pk")], verbose_name="Horas Alocadas")
    valor_hora = tables.Column(empty_values=(), verbose_name="Valor-Hora", orderable=False)
    valor_cp = tables.Column(empty_values=(), verbose_name="Valor Contrapartida", orderable=False)
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")


    def render_valor_hora(self, record):
        valor_aquisicao = record.id_equipamento.valor_aquisicao or 0
        cvc = record.id_equipamento.cvc or 0
        cma = record.id_equipamento.cma or 0
        quantidade_nos = record.id_equipamento.quantidade_nos or 1 
        if record.id_equipamento.nome in ['DGX-1','DGX-A100','DGX-H100']:
          value = (( (0.1*valor_aquisicao) +  cvc + cma )  /  1200) / quantidade_nos
        else:
          value = ( (0.1*valor_aquisicao) +  cvc + cma )  /  1440 / quantidade_nos
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value)  # Exibe o valor com o símbolo R$

    
    def render_valor_cp(self, record):
        valor_aquisicao = record.id_equipamento.valor_aquisicao or 0
        cvc = record.id_equipamento.cvc or 0
        cma = record.id_equipamento.cma or 0
        quantidade_nos = record.id_equipamento.quantidade_nos or 1  # Evita divisão por zero
        horas_alocadas = record.horas_alocadas or 0 
        if record.id_equipamento.nome in ['DGX-1','DGX-A100','DGX-H100']:
          value_valor_hora = (( (0.1*valor_aquisicao) + cvc + cma )  /  1200) / quantidade_nos
        else:
          value_valor_hora = ( ( (0.1*valor_aquisicao) + cvc + cma )  /  1440  ) /  quantidade_nos
        value = round(horas_alocadas * value_valor_hora , 2)
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value) 


    def render_excluir(self, record):
        url = reverse("contrapartida_equipamento_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)
    
    
    class Meta:
        model = contrapartida_equipamento
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('id_projeto', 'ano', 'mes', 'id_equipamento', 'horas_alocadas', 'valor_hora', 'valor_cp', 'excluir')
        sequence = ('id_projeto', 'ano', 'mes', 'id_equipamento', 'horas_alocadas', 'valor_hora', 'valor_cp', 'excluir')


class contrapartida_so_table(tables.Table):
    id_projeto = tables.LinkColumn("contrapartida_so_update", args=[A("pk")], verbose_name="Projeto")
    so_da_ue  = tables.Column(empty_values=(), verbose_name="SO da Ue Permitido", orderable=False)
    so_no_ptr=  tables.Column(empty_values=(), verbose_name="SO no PTR", orderable=False)
    cp_ue_so = tables.Column(empty_values=(), verbose_name="Contrapartida UE de S.O", orderable=False)
    cp_mensal_so = tables.Column(empty_values=(), verbose_name="Contrapartida Mensal de SO", orderable=False)
    num_meses=tables.Column(empty_values=(), verbose_name="Numero de Meses", orderable=False)
    dt_inicio=tables.Column(empty_values=(), verbose_name="Data Inicio", orderable=False)
    ano_alocacao = tables.LinkColumn("contrapartida_so_update", args=[A("pk")], verbose_name="Ano")
    mes_alocacao = tables.LinkColumn("contrapartida_so_update", args=[A("pk")], verbose_name="Mês")
    valor =tables.LinkColumn("contrapartida_so_update", args=[A("pk")], verbose_name="Valor Alocado")
 
    
    

    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")
    

    def render_so_da_ue(self, record):
        value=round(record.id_projeto.valor_total * record.id_projeto.tx_adm_ue,2)-record.valor_funape
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value) 
    
    def render_so_no_ptr(self, record):
        value=record.id_projeto_valor_so_ptr
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value) 
    
    def render_num_meses(self, record):
        data_inicio = record.id_projeto.data_inicio
        data_fim = record.id_projeto.data_fim
        num_meses = data_fim.month - data_inicio.month + ((data_fim.year - data_inicio.year) * 12)
        return num_meses
    
    def render_cp_ue_so(self, record):
        value = record.so_da_ue - record.so_no_ptr
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value) 
     
    def render_cp_mensal_so(self, record):
        value = round(record.cp_ue_so/record.num_meses,2)
        formatted_value = locale.currency(value, grouping=True)
        return format_html('<span>{}</span>', formatted_value) 

    def render_excluir(self, record):
        url = reverse("contrapartida_so_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)    
    
    class Meta:
        model = contrapartida_so
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('id_projeto', 'cp_ue_so', 'cp_mensal_so','valor','mes_alocacao','ano_alocacao')