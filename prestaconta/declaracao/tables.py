import django_tables2 as tables
from .models import declaracao_contrapartida_pesquisa_item,declaracao_contrapartida_rh_item,declaracao_contrapartida_equipamento_item

class declaracao_contrapartida_pesquisa_item_table(tables.Table):
    valor_cp = tables.Column(verbose_name="Valor CP", accessor='valor_cp', 
                              attrs={"td": {"class": "text-end"}})

    class Meta:
        model = declaracao_contrapartida_pesquisa_item
        fields = ('nome', 'cpf', 'funcao', 'horas_alocadas', 'salario', 'valor_cp')
        attrs = {"class": "table table-striped table-bordered"}

    def render_valor_cp(self, value):
        return f'{value:.2f}'

class declaracao_contrapartida_rh_item_table(tables.Table):
    valor_cp = tables.Column(verbose_name="Valor CP", accessor='valor_cp', 
                              attrs={"td": {"class": "text-end"}})
    valor_hora = tables.Column(verbose_name="Valor hora", accessor='valor_hora', 
                              attrs={"td": {"class": "text-end"}})
    
    data_cheque= tables.Column(empty_values=(),verbose_name="Mês/Ano do Contracheque")

    class Meta:
        model = declaracao_contrapartida_rh_item
        fields = ('nome', 'cpf', 'funcao' ,'salario', 'valor_hora','horas_alocadas', 'valor_cp','data_cheque')
        attrs = {"class": "table table-striped table-bordered"}

    def render_valor_cp(self, value):
        return f'{value:.2f}'
    
    def render_valor_hora(self, value):
        return f'{value:.2f}'   
    
    def render_data_cheque(self, record):
        meses_ptbr = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
            5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
            9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
        }

        mes = record.salario_mes
        ano = record.salario_ano
        mes_nome = meses_ptbr.get(mes, "-")
        return f"{mes_nome}/{ano}" if mes_nome != "-" else "-"

class declaracao_contrapartida_equipamento_item_table(tables.Table):
    valor_cp = tables.Column(verbose_name="Valor CP", accessor='valor_cp',attrs={"td": {"class": "text-end"}})
    descricao = tables.Column(verbose_name="Descricao", accessor='descricao',attrs={"td": {"class": "text-end"}})
    def render_valor_cp(self, value):
        return f'{value:.2f}' 
    
    def render_descricao(self, value):
        if not value:
             return "-"
        if len(value) > 40:
            return f"{value[:40]}..."
        return value    

    class Meta:
        model = declaracao_contrapartida_equipamento_item
        fields = ("equipamento","codigo", "projeto","descricao","horas_alocadas","valor_cp")
        attrs = {"class": "table table-striped table-bordered"}

