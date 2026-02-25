import json
from django import forms
from django.forms import formset_factory, BaseFormSet,inlineformset_factory
from django.db import models
from .models import contrapartida_pesquisa, salario, contrapartida_rh, projeto,contrapartida_so_projeto,equipamento,contrapartida_equipamento
from decimal import Decimal
from datetime import datetime,date

class ContrapartidasPesquisaRhForm(forms.ModelForm):
    """
    Formulário sem id_projeto (será passado externamente pela view)
    """
    class Meta:
        #model = self.model
        fields = ['id_salario', 'funcao', 'horas_alocadas']  # ← Removido id_projeto
        widgets = {
            'id_salario': forms.Select(attrs={
                'class': 'form-control salario-select',
                'data-horas': ''  # Será preenchido dinamicamente
            }),
            'funcao': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Pesquisador'
            }),
            'horas_alocadas': forms.NumberInput(attrs={
                'class': 'form-control horas-input', 
                'step': '0.1', 
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Recebe projeto para filtrar salários
        self.projeto = kwargs.pop('projeto', None)
        super().__init__(*args, **kwargs)
        
        # Filtra salários se projeto foi fornecido
        if self.projeto:
            # Filtra salários dentro do período do projeto
            salarios_filtrados = salario.objects.filter(
                ano__gte=self.projeto.data_inicio.year,
                ano__lte=self.projeto.data_fim.year
            )
            
            # Refina por mês se necessário
            if self.projeto.data_inicio.year == self.projeto.data_fim.year:
                # Mesmo ano: filtra por mês
                salarios_filtrados = salarios_filtrados.filter(
                    mes__gte=self.projeto.data_inicio.month,
                    mes__lte=self.projeto.data_fim.month
                )
            else:
                # Anos diferentes: lógica mais complexa
                from django.db.models import Q
                salarios_filtrados = salarios_filtrados.filter(
                    Q(ano=self.projeto.data_inicio.year, mes__gte=self.projeto.data_inicio.month) |
                    Q(ano__gt=self.projeto.data_inicio.year, ano__lt=self.projeto.data_fim.year) |
                    Q(ano=self.projeto.data_fim.year, mes__lte=self.projeto.data_fim.month)
                )
            
            self.fields['id_salario'].queryset = salarios_filtrados.order_by(
                'id_pessoa__nome', '-ano', '-mes'
            )
        
        # Campo readonly para mostrar horas restantes
        self.fields['horas_restantes'] = forms.DecimalField(
            required=False,
            disabled=True,
            label='Horas Disponíveis',
            widget=forms.NumberInput(attrs={
                'class': 'form-control horas-restantes', 
                'readonly': 'readonly',
                'placeholder': 'Selecione salário'
            })
        )


class BaseContrapartidasPesquisaRhFormSet(BaseFormSet):
    """
    Validação customizada para verificar horas disponíveis por salário
    """
    def __init__(self, *args, **kwargs):
        self.projeto = kwargs.pop('projeto', None)
        super().__init__(*args, **kwargs)
    
    def _construct_form(self, i, **kwargs):
        """
        Passa o projeto para cada formulário individual
        """
        kwargs['projeto'] = self.projeto
        return super()._construct_form(i, **kwargs)
    
    def clean(self):
        if any(self.errors):
            return
        
        if not self.projeto:
            raise forms.ValidationError('Projeto não especificado.')
        
        salarios_usados = {}
        salarios_duplicados = set()
        
        for form in self.forms:

            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                id_salario = form.cleaned_data.get('id_salario')
                horas_alocadas = form.cleaned_data.get('horas_alocadas', 0)
                
                if id_salario:
                    # Verifica duplicatas no formset
                    if id_salario.id in salarios_duplicados:
                        raise forms.ValidationError(
                            f'O salário de {id_salario.id_pessoa} ({id_salario.mes}/{id_salario.ano}) '
                            f'foi selecionado mais de uma vez. Cada salário só pode ser '
                            f'cadastrado uma vez por projeto.'
                        )
                    salarios_duplicados.add(id_salario.id)
                    
                    # Verifica se já existe no banco para este projeto
                    if self.model.objects.filter(
                        id_projeto=self.projeto,
                        id_salario=id_salario
                    ).exists():
                        raise forms.ValidationError(
                            f'Já existe uma contrapartida cadastrada para o salário '
                            f'de {id_salario.id_pessoa} ({id_salario.mes}/{id_salario.ano}) '
                            f'neste projeto.'
                        )
                    
                    # Acumula horas por salário
                    if id_salario.id not in salarios_usados:
                        salarios_usados[id_salario.id] = {
                            'salario': id_salario,
                            'horas_novas': 0
                        }
                    salarios_usados[id_salario.id]['horas_novas'] += horas_alocadas
        
        # Valida disponibilidade de horas para cada salário
        for salario_id, dados in salarios_usados.items():
            salario_obj = dados['salario']
            horas_novas = dados['horas_novas']
            
            # Calcula horas já utilizadas
            horas_usadas_pesquisa = contrapartida_pesquisa.objects.filter(
                id_salario__id_pessoa=salario_obj.id_pessoa,
                id_salario__mes=salario_obj.mes,
                id_salario__ano=salario_obj.ano
            ).aggregate(total=models.Sum('horas_alocadas'))['total'] or 0
            
            horas_usadas_rh = contrapartida_rh.objects.filter(
                id_salario__id_pessoa=salario_obj.id_pessoa,
                id_salario__mes=salario_obj.mes,
                id_salario__ano=salario_obj.ano
            ).aggregate(total=models.Sum('horas_alocadas'))['total'] or 0
            
            horas_utilizadas = horas_usadas_pesquisa + horas_usadas_rh
            horas_disponiveis = (salario_obj.horas_limite or 0) - horas_utilizadas
            
            if horas_novas > horas_disponiveis:
                raise forms.ValidationError(
                    f'O salário de {salario_obj.id_pessoa} ({salario_obj.mes}/{salario_obj.ano}) '
                    f'possui apenas {horas_disponiveis}h disponíveis, mas você está tentando '
                    f'alocar {horas_novas}h no total.'
                )

class ContrapartidaSOForm(forms.ModelForm):


    hoje=datetime.today()
   
    ano_mes = forms.CharField(
        label="Ano/Mês",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": f"{hoje.year}/{hoje.month}"})
    )

    class Meta:
        model = contrapartida_so_projeto
        fields = ["ano_mes", "valor"]
        widgets = {
            "valor": forms.NumberInput(attrs={"step": "0.01"}),
        }
    
    def __init__(self, *args, **kwargs):
        # Recebe projeto para filtrar salários
        self.projeto = kwargs.pop('projeto', None)
        super().__init__(*args, **kwargs)

        
    
    def clean(self):
        cleaned = super().clean()

        ano_mes = cleaned.get("ano_mes")

        if ano_mes:
            try:
                ano_str, mes_str = ano_mes.split("/")
                ano = int(ano_str)
                mes = int(mes_str)

                if mes < 1 or mes > 12:
                    raise ValueError
            except Exception:
                raise forms.ValidationError("Formato da data deve ser AAAA/MM")

            cleaned['ano'] = ano
            cleaned['mes'] = mes

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.ano = self.cleaned_data['ano']
        obj.mes = self.cleaned_data['mes']

        if commit:
            obj.save()
        return obj

class BaseContrapartidaSOFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.projeto = kwargs.pop('projeto', None)
        super().__init__(*args, **kwargs)
    
    def _construct_form(self, i, **kwargs):
        """
        Passa o projeto para cada formulário individual
        """
        kwargs['projeto'] = self.projeto
        return super()._construct_form(i, **kwargs) 
  
    
    def clean(self):
        if any(self.errors):
            return
        
        # if not self.projeto:
        #     raise forms.ValidationError('Projeto não especificado.')
        
        meses_usados = set()

        for i, form in enumerate(self.forms):

            if not hasattr(form, "cleaned_data"):
                continue
            
            if form.cleaned_data.get("DELETE"):
                continue
            
            ano_mes = form.cleaned_data.get("ano_mes")
            valor = form.cleaned_data.get("valor")
            data_inicio = self.projeto.data_inicio
            data_fim = self.projeto.data_fim

            if not ano_mes:
                raise forms.ValidationError(f"Linha {i+1}: Informe o campo Ano/Mês.")

            # parsing AAAA/MM
            try:
                ano_str, mes_str = ano_mes.split("/")
                ano = int(ano_str)
                mes = int(mes_str)
            except ValueError:
                raise forms.ValidationError(f"Linha {i+1}: Formato inválido. Use AAAA/MM.")

            ref = date(ano, mes, 1)

            if ref < data_inicio or ref > data_fim:
                raise forms.ValidationError(
                    f"Mês/ano {mes}/{ano} está fora do intervalo do projeto."
                )

            # valida duplicidade
            if (ano, mes) in meses_usados:
                raise forms.ValidationError(f"Mês duplicado na linha {i+1}.")
            meses_usados.add((ano, mes))

            # escrever nos cleaned_data para uso no save_formset()
            form.cleaned_data["ano"] = ano
            form.cleaned_data["mes"] = mes

            # valor decimal com arredondamento
            try:
                form.cleaned_data["valor"] = round(Decimal(valor), 2)
            except Exception:
                raise forms.ValidationError(f"Linha {i+1}: Valor inválido.")

class ContrapartidaEquipamentoForm(forms.ModelForm):

    class Meta:
        model = contrapartida_equipamento
        fields = ['ano', 'mes', 'id_equipamento', 'descricao', 'horas_alocadas', 'valor_manual']


    def __init__(self, *args, **kwargs):
        self.projeto = kwargs.pop('projeto', None)
        super().__init__(*args, **kwargs)

        # Bootstrap / seletor JS
        self.fields['id_equipamento'].widget.attrs.update({
            'class': 'form-select equipamento-select'
        })
        
        equipamentos = self.fields['id_equipamento'].queryset

        mapa_valor_hora = {
            str(e.pk): float(e.valor_hora)
            for e in equipamentos
        }

        # Joga o JSON no HTML (data attribute)
        self.fields['id_equipamento'].widget.attrs[
            'data-valores-hora'
        ] = json.dumps(mapa_valor_hora)
            

class BaseContrapartidaEquipamentoFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.projeto = kwargs.pop('projeto', None)
        super().__init__(*args, **kwargs)
    
    def _construct_form(self, i, **kwargs):
        """
        Passa o projeto para cada formulário individual
        """
        kwargs['projeto'] = self.projeto
        return super()._construct_form(i, **kwargs) 

    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data:
                continue

            ano = form.cleaned_data.get("ano")
            mes = form.cleaned_data.get("mes")
            equipamento_obj = form.cleaned_data.get("id_equipamento")

            if not ano or not mes or not equipamento_obj:
                form.add_error(None, "Ano, mês e equipamento são obrigatórios.")




ContrapartidaPesquisaFormSet= inlineformset_factory(
    projeto,
    model=contrapartida_pesquisa,
    form=ContrapartidasPesquisaRhForm,
    formset=BaseContrapartidasPesquisaRhFormSet,
    extra=1,
    can_delete=True
)

ContrapartidaRhFormSet= inlineformset_factory(
    projeto,
    model=contrapartida_rh,
    form=ContrapartidasPesquisaRhForm,
    formset=BaseContrapartidasPesquisaRhFormSet,
    extra=1,
    can_delete=True
)


ContrapartidaSOFormSet= inlineformset_factory(
    projeto,
    model=contrapartida_so_projeto,
    form=ContrapartidaSOForm,
    formset=BaseContrapartidaSOFormSet,
    extra=1,
    can_delete=True
)

ContrapartidaEquipamentoFormSet = inlineformset_factory(
    projeto,
    model=contrapartida_equipamento,
    form=ContrapartidaEquipamentoForm,
    formset=BaseContrapartidaEquipamentoFormSet,
    extra=1,
    can_delete=True 
)