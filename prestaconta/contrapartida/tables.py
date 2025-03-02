from .models import projeto, equipamento, pessoa, salario, contrapartida_pesquisa
from django_tables2.utils import A
from django.db.models import Func, IntegerField, F
from django.urls import reverse
from django.utils.dateformat import DateFormat
from django.utils.html import format_html
import django_tables2 as tables
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class projeto_table(tables.Table):
    nome = tables.LinkColumn("projeto_update", args=[A("pk")])
    peia = tables.LinkColumn("projeto_update", args=[A("pk")])
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
    quantidade_nos = tables.LinkColumn("equipamento_update", args=[A("pk")])
    cvc = tables.LinkColumn("equipamento_update", args=[A("pk")])
    cma = tables.LinkColumn("equipamento_update", args=[A("pk")])
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")
    class Meta:
        model = equipamento
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome','valor_aquisicao', 'quantidade_nos', 'cvc')

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


    
    def render_excluir(self, record):
        url = reverse("equipamento_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)

class pessoa_table(tables.Table):
    nome = tables.LinkColumn("pessoa_update", args=[A("pk")])
    ativo = tables.LinkColumn("pessoa_update", args=[A("pk")]) 
    excluir = tables.Column(empty_values=(), orderable=False, verbose_name="Excluir")

    class Meta:
        model = pessoa
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome','ativo')

    def render_ativo(self, value):
        return 'Ativo' if value else 'Desativado'

    def render_excluir(self, record):
        url = reverse("pessoa_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)

class salario_table(tables.Table):
    pessoa = tables.LinkColumn("salario_update", args=[A("pk")], accessor='id_pessoa.nome', verbose_name="Pessoa")
    referencia = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Mês de Referência")
    valor = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Valor")
    horas = tables.LinkColumn("salario_update", args=[A("pk")], verbose_name="Horas mensais")
    excluir = tables.TemplateColumn("<a href='{% url 'salario_delete' record.id %}'>Excluir</a>", verbose_name="Excluir")

    class Meta:
        model = salario
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('pessoa', 'referencia', 'valor', 'horas', 'excluir')

    def render_valor(self, value):
        if value is not None:
            formatted_value = locale.currency(value, grouping=True)
            return format_html('<span>{}</span>', formatted_value)
        return '-'

    def render_excluir(self, record):
        url = reverse("salario_delete", args=[record.pk])
        return format_html('<a href="{}" class="btn btn-danger btn-sm">Excluir</a>', url)

class contrapartida_pesquisa_table(tables.Table):
    projeto = tables.Column()
    nome = tables.Column(verbose_name='Pesquisador')
    referencia = tables.Column()
    valor_hora = tables.Column()
    horas_alocadas = tables.Column()

    class Meta:
        model = contrapartida_pesquisa
        attrs = {"class": "table thead-light table-striped table-hover"}
        template_name = "django_tables2/bootstrap4.html"
        fields = ('projeto','nome','referencia','valor_hora','horas_alocadas')
