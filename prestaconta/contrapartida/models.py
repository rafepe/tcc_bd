from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone



from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


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
            return (self.data_fim.year - self.data_inicio.year) * 12 + (self.data_fim.month - self.data_inicio.month)
        return 0

    class Meta:
        ordering = ['data_fim']

    @property
    def contrapartida_max(self):
        return self.valor_total - self.valor_financiado

class equipamento(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, verbose_name="Nome do Equipamento")
    valor_aquisicao = models.FloatField(verbose_name="Valor de Aquisição")
    quantidade_nos = models.IntegerField(default=1, verbose_name="Quantidade de Nós")
    cvc = models.FloatField(default=0, verbose_name="CVC - Custo de Verificação e Calibração")
    cma = models.FloatField(default=0, verbose_name="CMA - Custo de Manutenção Anual")
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    horas_mensais = models.IntegerField(default=0, verbose_name="Horas Mensais")
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
    valor = models.FloatField(blank=True, null=True, default=0)
    horas = models.IntegerField(default=160, null=False)
    anexo = models.FileField(upload_to='comprovantes/', null=True, blank=True)
    
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
    horas_alocadas = models.FloatField(verbose_name='Horas Alocadas',default=0.0,null=True,blank=True)

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
    horas_alocadas = models.IntegerField(blank=True, null=True, default=0)
    
    class Meta:
        ordering = ['-ano','-mes']

class contrapartida_rh(models.Model):
    id = models.AutoField(primary_key=True)
    id_projeto = models.ForeignKey(projeto, on_delete=models.CASCADE)
    id_salario = models.ForeignKey(salario, on_delete=models.CASCADE)
    valor_cp = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('id_projeto', 'id_salario')

    def __str__(self):
        return f"Contrapartida RH - {self.id_projeto.nome} - {self.id_salario.id_pessoa.nome}"

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