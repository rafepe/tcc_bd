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
    total=models.FloatField( verbose_name="Total")
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