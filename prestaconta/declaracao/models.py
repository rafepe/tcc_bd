from django.db import models
from contrapartida.models import *
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

class declaracao_contrapartida_pesquisa(models.Model):
    id_projeto=models.IntegerField(verbose_name="Projeto Id")
    projeto = models.CharField(max_length=255, verbose_name='Projeto')
    mes = models.IntegerField(verbose_name="Mês de referência")
    ano = models.IntegerField(verbose_name="Ano de referência")
    total=models.FloatField(default=0, verbose_name="Total")
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name="Data de geração da declaração")

    class Meta:
        verbose_name = "Declaração Contrapartida Pesquisa"
        verbose_name_plural = "Declarações Contrapartida Pesquisa"
        db_table = 'declaracao_contrapartida_pesquisa'
        ordering = ['-ano', '-mes', 'projeto']
        constraints = [
            models.UniqueConstraint(
                fields=['id_projeto', 'mes', 'ano'],
                name='unique_declaracao_por_projeto_mes_ano'
            )
        ]

    def __str__(self):
        return f"{self.projeto} - {self.mes}/{self.ano}"    
    
class declaracao_contrapartida_pesquisa_item(models.Model):
    declaracao = models.ForeignKey(
        declaracao_contrapartida_pesquisa,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Declaração'
    )

    nome = models.CharField(max_length=255, verbose_name="Nome do Bolsista")
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    funcao = models.CharField(max_length=100, default="Pesquisador", verbose_name="Função")
    horas_alocadas = models.IntegerField(verbose_name="Carga Horária Mensal")
    salario =  models.FloatField( verbose_name="Salário")
    valor_cp = models.FloatField( verbose_name="Valor das Horas")

    class Meta:
        verbose_name = "Item da Declaração Contrapartida Pesquisa"
        verbose_name_plural = "Itens da Declaração Contrapartida Pesquisa"
        db_table = 'declaracao_contrapartida_pesquisa_item'
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['declaracao', 'cpf'],
                name='unique_item_por_declaracao_e_cpf'
            )
        ]

    def __str__(self):
        return f"{self.nome} - {self.declaracao}"
    
class declaracao_contrapartida_so(models.Model): 
    id_projeto=models.IntegerField(verbose_name="Projeto Id")
    projeto = models.CharField(max_length=255, verbose_name='Projeto')
    mes = models.IntegerField(verbose_name="Mês de referência")
    ano = models.IntegerField(verbose_name="Ano de referência")
    total=models.FloatField(default=0, verbose_name="Total")
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name="Data de geração da declaração")

    class Meta:
        verbose_name = "Declaração Contrapartida SO"
        verbose_name_plural = "Declarações Contrapartida SO"
        db_table = 'declaracao_contrapartida_so'
        ordering = ['-ano', '-mes', 'projeto']
        constraints = [
            models.UniqueConstraint(
                fields=['id_projeto', 'mes', 'ano'],
                name='unique_declaracao_so_por_projeto_mes_ano'
            )
        ]

    def __str__(self):
        return f"{self.projeto} - {self.mes}/{self.ano}"        
    
class declaracao_contrapartida_rh(models.Model):
    id_projeto=models.IntegerField(verbose_name="Projeto Id")
    projeto = models.CharField(max_length=255, verbose_name='Projeto')
    mes = models.IntegerField(verbose_name="Mês de referência")
    ano = models.IntegerField(verbose_name="Ano de referência")
    total=models.FloatField(default=0, verbose_name="Total")
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name="Data de geração da declaração")

    class Meta:
        verbose_name = "Declaração Contrapartida RH"
        verbose_name_plural = "Declarações Contrapartida RH"
        db_table = 'declaracao_contrapartida_rh'
        ordering = ['-ano', '-mes', 'projeto']
        constraints = [
            models.UniqueConstraint(
                fields=['id_projeto', 'mes', 'ano'],
                name='unique_declaracao_rh_por_projeto_mes_ano'
            )
        ]

    def __str__(self):
        return f"{self.projeto} - {self.mes}/{self.ano}"    
    
class declaracao_contrapartida_rh_item(models.Model):
    declaracao = models.ForeignKey(
        declaracao_contrapartida_rh,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Declaração'
    )

    nome = models.CharField(max_length=255, verbose_name="Nome do Bolsista")
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    funcao = models.CharField(max_length=100, default="Prospector", verbose_name="Função")
    horas_alocadas = models.IntegerField(verbose_name="Horas alocadas na unidade")
    salario =  models.FloatField( verbose_name="Salário")
    salario_mes = models.IntegerField(verbose_name="Mês de contracheque")
    salario_ano = models.IntegerField(verbose_name="Ano do contracheque")
    valor_cp = models.FloatField( verbose_name="Valor da Contrapartida")
    valor_hora= models.FloatField( verbose_name="Valor da Hora")

    class Meta:
        verbose_name = "Item da Declaração Contrapartida RH"
        verbose_name_plural = "Itens da Declaração Contrapartida RH"
        db_table = 'declaracao_contrapartida_rh_item'
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['declaracao', 'cpf'],
                name='unique_item_rh_por_declaracao_e_cpf'
            )
        ]

    def __str__(self):
        return f"{self.nome} - {self.declaracao}"

class declaracao_contrapartida_equipamento(models.Model):
    mes = models.IntegerField(verbose_name="Mês de referência")
    ano = models.IntegerField(verbose_name="Ano de referência")
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name="Data de geração da declaração")

    class Meta:
        verbose_name = "Declaração Contrapartida Equipamento"
        verbose_name_plural = "Declarações Contrapartida Equipamento"
        db_table = 'declaracao_contrapartida_equipamento'
        ordering = ['-ano', '-mes']
        constraints = [
            models.UniqueConstraint(
                fields=['mes', 'ano'],
                name='unique_declaracao_equipamento_mes_ano'
            )
        ]

    def __str__(self):
        return f"{self.mes}/{self.ano}"    
    
class declaracao_contrapartida_equipamento_item(models.Model):
    declaracao = models.ForeignKey(
        declaracao_contrapartida_equipamento,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Declaração'
    )
    
    codigo = models.CharField(max_length=255, verbose_name="Peia")
    projeto = models.CharField(max_length=14, verbose_name="Projeto")
    equipamento=models.CharField(max_length=255, verbose_name="Equipamento")
    horas_alocadas = models.IntegerField(verbose_name="Horas no mes")
    descricao = models.CharField(max_length=400, verbose_name="Descricao")
    valor_cp = models.FloatField( default=0,verbose_name="Valor da Contrapartida")

    class Meta:
        verbose_name = "Item da Declaração Contrapartida Equipamento"
        verbose_name_plural = "Itens da Declaração Contrapartida Equipamenot"
        db_table = 'declaracao_contrapartida_equipamento_item'
        ordering = ['equipamento']
        constraints = [
            models.UniqueConstraint(
                fields=['declaracao', 'equipamento','projeto'],
                name='unique_item_por_declaracao_equipamento_projeto'
            )
        ]
