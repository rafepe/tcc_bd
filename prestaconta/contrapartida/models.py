from django.core.exceptions import ValidationError
from django.db import models
from django.db import models
import re


class projeto(models.Model):
    nome = models.CharField(max_length=255)
    data_inicio = models.DateField(verbose_name="Data início")
    data_fim = models.DateField(verbose_name="Data fim")
    valor = models.FloatField()

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
    id_pessoa = models.ForeignKey(pessoa, on_delete=models.CASCADE, db_column='id_pessoa', verbose_name='Pessoa')
    referencia = models.CharField(
        max_length=7,  # Formato MM/YYYY
        verbose_name="Mês de referência"
    )
    valor = models.FloatField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['id', 'referencia'], name='unique_pessoa_referencia')
        ]
        ordering = ['id_pessoa']


class contrapartidaPessoa(models.Model):
    salario_bruto = models.ForeignKey(salario, on_delete=models.CASCADE)
    horas_alocadas = models.FloatField(blank=True, null=True)

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
