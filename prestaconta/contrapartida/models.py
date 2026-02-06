from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .utils import gerar_meses_entre
import os
import re


class projeto(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    peia = models.CharField(max_length=255, verbose_name="PEIA")
    data_inicio = models.DateField(verbose_name="Data início")
    data_fim = models.DateField(verbose_name="Data fim")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor total")
    valor_financiado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor financiado")
    valor_so_ptr = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor SO Plano de Trabalho")
    valor_funape = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor Funape")
    tx_adm_ue = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, verbose_name="Tx Admin. Unidade Embrapii")
    contrapartida = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Contrapartida prometida')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    def __str__(self):
        return self.nome

    @property
    def num_mes(self):
        if self.data_inicio and self.data_fim:
            return len(gerar_meses_entre(self.data_inicio,self.data_fim))
        return 0

    class Meta:
        ordering = ['nome']

    @property
    def contrapartida_max(self):
        return self.valor_total - self.valor_financiado

class equipamento(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, verbose_name="Nome do Equipamento")
    valor_aquisicao = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,verbose_name="Valor de Aquisição")
    quantidade_nos = models.IntegerField(default=1, verbose_name="Quantidade de Nós")
    cvc = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="CVC - Custo de Verificação e Calibração")
    cma = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="CMA - Custo de Manutenção Anual")
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    horas_mensais = models.IntegerField(default=0, verbose_name="Horas Mensais")
    
    @property
    def valor_hora(self):
        valor_aquisicao = self.valor_aquisicao or 0
        cvc = self.cvc or 0
        cma = self.cma or 0
        quantidade_nos = self.quantidade_nos or 1 
        if self.nome.upper().startswith("DGX"):
            value = (( (Decimal(0.1)*valor_aquisicao) +  cvc + cma )  /  1200) / quantidade_nos
        else:
            value = ((Decimal(0.1)*valor_aquisicao) +  cvc + cma )  /  1440 / quantidade_nos
           
        return round(value,7) 
    
    def __str__(self):
        return self.nome
 
    class Meta:
        ordering = ['-ativo','nome']

class pessoa(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True, default=None, verbose_name='CPF')
    email = models.EmailField(unique=False, null=True, blank=True, default=None, verbose_name='E-mail')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
   
    def __str__(self):
        return self.nome
 
    class Meta:
        ordering = ['-ativo', 'nome']


def caminho_comprovante(instance, filename):
    nome = re.sub(r'\s+', '_', instance.id_pessoa.nome.strip())

    ano = instance.ano
    mes = instance.mes
    semestre = 1 if mes <= 6 else 2

    new_filename = f"{nome}-{ano:04d}-{mes:02d}.pdf"
    new_filename = new_filename.replace(" ", "_")

    return f"comprovantes/{ano:04d}-{semestre}/{nome}/{new_filename}"



class salario(models.Model):
    id = models.AutoField(primary_key=True)
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
    valor = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,blank=True, null=True)
    horas = models.IntegerField(default=160, null=False)
    horas_limite= models.IntegerField(default=0 , null=True)
    anexo = models.FileField(upload_to=caminho_comprovante, null=True, blank=True)
    
    @property
    def valor_hora(self):
        if self.valor and self.horas and self.horas != 0:
            return round(self.valor / self.horas, 2)
        return 0

    
    def delete(self, *args, **kwargs):
        # Remove o arquivo do sistema de arquivos antes de deletar o objeto
        if self.anexo and os.path.isfile(self.anexo.path):
            os.remove(self.anexo.path)
        super().delete(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['id_pessoa', 'ano', 'mes'], name='unique_pessoa_referencia')
        ]
        ordering = ['id_pessoa']

    def __str__(self):
        return f"{self.id_pessoa} - {self.ano}/{self.mes}"

@receiver(post_delete, sender=salario)
def delete_anexo_file(sender, instance, **kwargs):
    if instance.anexo and os.path.isfile(instance.anexo.path):
        os.remove(instance.anexo.path)

class contrapartida_pesquisa(models.Model):
    id_projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE, verbose_name='Projeto')
    id_salario = models.ForeignKey('salario', on_delete=models.CASCADE, verbose_name='Salário')
    horas_alocadas = models.DecimalField(max_digits=9, decimal_places=3, default=0.0, verbose_name='Horas Alocadas',blank=True)
    funcao = models.CharField(max_length=100, default="Pesquisador",null=True, verbose_name="Função")
    
    @property
    def valor_cp(self):
        if self.id_salario.valor and self.id_salario.horas:
            return round(self.horas_alocadas * (self.id_salario.valor / self.id_salario.horas), 2)
        return 0
    
    class Meta:
        unique_together = ('id_projeto', 'id_salario')

    def __str__(self):
        return f"{self.id_projeto} - {self.id_salario}"

class contrapartida_equipamento(models.Model):
    id_projeto = models.ForeignKey(projeto, on_delete=models.CASCADE)
    mes = models.IntegerField(
        verbose_name="Mês de referência",
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    ano = models.IntegerField(
        verbose_name="Ano de referência",
        validators=[MinValueValidator(2000), MaxValueValidator(2200)]
    )    
    id_equipamento = models.ForeignKey(equipamento, on_delete=models.CASCADE)
    descricao=models.CharField(max_length=400,null=True,verbose_name='Descricao')
    horas_alocadas = models.IntegerField(blank=True, null=True, default=0)
    valor_manual= models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True,default=0)

    @property
    def valor_cp(self):
        horas_alocadas = self.horas_alocadas or 0
        valor_hora_equipamento= self.id_equipamento.valor_hora
        if self.valor_manual is not None and self.valor_manual > 0:
            return round(self.valor_manual, 2)

        return round(horas_alocadas *valor_hora_equipamento, 2)
    
    class Meta:
        ordering = ['-ano','-mes']

class contrapartida_so_projeto(models.Model):
    id_projeto = models.ForeignKey(projeto, on_delete=models.CASCADE, related_name='Projeto')
    ano = models.IntegerField(verbose_name="Ano Referencia")
    mes = models.IntegerField(verbose_name="Mês Referencia")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrapartida {self.id_projeto.nome} - {self.ano}/{self.mes}"

    class Meta:
        verbose_name = "Contrapartida SO"
        verbose_name_plural = "Contrapartidas SO"
        ordering = ['ano','mes']
        #db_table = 'contrapartida_so_proj'

class contrapartida_rh(models.Model):
    id_projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE, verbose_name='Projeto')
    id_salario = models.ForeignKey('salario', on_delete=models.CASCADE, verbose_name='Salário')
    horas_alocadas = models.DecimalField(max_digits=6, decimal_places=1, default=0.0,verbose_name='Horas Alocadas',null=True,blank=True)
    funcao = models.CharField(max_length=100,null=True, verbose_name="Função")

    @property
    def valor_cp(self):
        if self.id_salario.valor and self.id_salario.horas:
            return round((self.horas_alocadas * (self.id_salario.valor / self.id_salario.horas) or 0), 2)
        return 0
    
    class Meta:
        unique_together = ('id_projeto', 'id_salario')

    def __str__(self):
        return f"{self.id_projeto} - {self.id_salario}"