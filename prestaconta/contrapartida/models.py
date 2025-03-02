from django.core.exceptions import ValidationError
from django.db import models
import re
from django.db.models import F, ExpressionWrapper, FloatField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from django.db import models

class projeto(models.Model):
    nome = models.CharField(max_length=255)
    peia = models.CharField(max_length=255, verbose_name="PEIA")
    data_inicio = models.DateField(verbose_name="Data início")
    data_fim = models.DateField(verbose_name="Data fim")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor total")
    valor_financiado = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor financiado")
    valor_so_ptr = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor SO Plano de Trabalho")
    valor_funape = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Funape")
    tx_adm_ue = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, verbose_name="Tx Admin. Unidade Embrapii")
    contrapartida = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Contrapartida prometida')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['data_fim']


class equipamento(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Equipamento")
    valor_aquisicao = models.FloatField(verbose_name="Valor de Aquisição")
    quantidade_nos = models.IntegerField(default=1, verbose_name="Quantidade de Nós")
    cvc = models.FloatField(default=0, verbose_name="CVC - Custo de Verificação e Calibração")
    cma = models.FloatField(default=0, verbose_name="CMA - Custo de Manutenção Anual")
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    def __str__(self):
        return self.nome
 
    class Meta:
        ordering = ['nome']

class pessoa(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
   
    def __str__(self):
        return self.nome
 
    class Meta:
        ordering = ['-ativo','nome']

def validar_mes_ano(value):
    if not re.match(r'^(0[1-9]|1[0-2])/\d{4}$', value):
        raise ValidationError('Formato inválido. Use MM/YYYY.')

class salario(models.Model):
    id_pessoa = models.ForeignKey(
        pessoa, on_delete=models.CASCADE, db_column='id_pessoa', verbose_name='Pessoa'
    )
    mes = models.IntegerField(
        verbose_name="Mês de referência",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    ano = models.IntegerField(
        verbose_name="Ano de referência",
        validators=[MinValueValidator(2000), MaxValueValidator(2200)]
    )
    valor = models.FloatField(blank=True, null=True)
    horas = models.IntegerField(default=160, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['id_pessoa', 'mes', 'ano'], name='unique_pessoa_referencia')
        ]
        ordering = ['id_pessoa']

class contrapartida_pesquisa(models.Model):
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE, verbose_name='Projeto')
    nome = models.ForeignKey('Pessoa', on_delete=models.CASCADE, verbose_name='Nome')
    referencia = models.ForeignKey('Salario', on_delete=models.CASCADE, verbose_name='Referência')
    valor_hora = models.FloatField(verbose_name='Valor Hora')
    horas_alocadas = models.FloatField(verbose_name='Horas Alocadas')

    class Meta:
        unique_together = ('projeto', 'nome', 'referencia')
        verbose_name = 'Contrapartida Pesquisa'
        verbose_name_plural = 'Contrapartidas Pesquisas'

"""
class contrapartidaSO(models.Model):
    projeto = models.ForeignKey(projeto, on_delete=models.CASCADE)
    valor_financiado = models.FloatField(blank=True, null=True)
    meses = models.IntegerField(blank=True, null=True)
    dao_funape = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['projeto']

class contrapartidaEquipamento(models.Model):
    projeto = models.ForeignKey(projeto, on_delete=models.CASCADE)
    equipamento = models.ForeignKey(equipamento, on_delete=models.CASCADE)
    referencia = models.DateField(blank=True, null=True)
    quantidade_hora = models.FloatField(blank=True, null=True)
    
    class Meta:
        ordering = ['projeto']

class projetoContrapartidaPesquisa(models.Model):
    contrapartida_pesquisa = models.ForeignKey(contrapartidaPessoa, on_delete=models.CASCADE)
    projeto = models.ForeignKey(projeto, on_delete=models.CASCADE)
    referencia_alocacao = models.DateField(blank=True, null=True)
    referencia_arrecadacao = models.DateField(blank=True, null=True)
 
    class Meta:
        ordering = ['projeto']
"""