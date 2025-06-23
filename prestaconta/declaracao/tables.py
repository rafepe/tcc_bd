import django_tables2 as tables
from .models import declaracao_contrapartida_pesquisa_item

class declaracao_contrapartida_pesquisa_item_table(tables.Table):
    valor_cp = tables.Column(verbose_name="Valor CP", accessor='valor_cp', 
                              attrs={"td": {"class": "text-end"}})

    class Meta:
        model = declaracao_contrapartida_pesquisa_item
        fields = ('nome', 'cpf', 'funcao', 'horas_alocadas', 'salario', 'valor_cp')
        attrs = {"class": "table table-striped table-bordered"}

    def render_valor_cp(self, value):
        return f'{value:.2f}'