from django import forms
from django.forms import formset_factory, BaseFormSet
from django.db import models
from .models import contrapartida_pesquisa, salario, contrapartida_rh

class ContrapartidaPesquisaForm(forms.ModelForm):
    class Meta:
        model = contrapartida_pesquisa
        fields = ['id_projeto', 'id_salario', 'funcao', 'horas_alocadas']
        widgets = {
            'id_projeto': forms.Select(attrs={'class': 'form-control projeto-select'}),
            'id_salario': forms.Select(attrs={'class': 'form-control salario-select'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Pesquisador'}),
            'horas_alocadas': forms.NumberInput(attrs={
                'class': 'form-control horas-input', 
                'step': '0.1', 
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campo readonly para mostrar horas restantes (preenchido via JS)
        self.fields['horas_restantes'] = forms.DecimalField(
            required=False,
            disabled=True,
            widget=forms.NumberInput(attrs={
                'class': 'form-control horas-restantes', 
                'readonly': 'readonly'
            })
        )


class BaseContrapartidaPesquisaFormSet(BaseFormSet):  # ← MUDOU: BaseFormSet ao invés de BaseInlineFormSet
    """
    Validação customizada para verificar horas disponíveis por salário
    """
    def clean(self):
        if any(self.errors):
            return
        
        salarios_usados = {}
        projetos_salarios = set()  # Para verificar unique_together
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                id_projeto = form.cleaned_data.get('id_projeto')
                id_salario = form.cleaned_data.get('id_salario')
                horas_alocadas = form.cleaned_data.get('horas_alocadas', 0)
                
                # Verifica unique_together (projeto, salário)
                if id_projeto and id_salario:
                    chave = (id_projeto.id, id_salario.id)
                    if chave in projetos_salarios:
                        raise forms.ValidationError(
                            f'Você está tentando cadastrar o mesmo salário '
                            f'({id_salario.id_pessoa}) mais de uma vez para o projeto '
                            f'{id_projeto.nome}. Cada salário só pode ser cadastrado uma vez por projeto.'
                        )
                    projetos_salarios.add(chave)
                    
                    # Verifica se já existe no banco (para evitar duplicatas)
                    if contrapartida_pesquisa.objects.filter(
                        id_projeto=id_projeto, 
                        id_salario=id_salario
                    ).exists():
                        raise forms.ValidationError(
                            f'Já existe uma contrapartida cadastrada para o salário '
                            f'{id_salario.id_pessoa} no projeto {id_projeto.nome}.'
                        )
                
                # Acumula horas por salário
                if id_salario:
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


# Criando o formset
ContrapartidaPesquisaFormSet = formset_factory(
    form=ContrapartidaPesquisaForm,
    formset=BaseContrapartidaPesquisaFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)