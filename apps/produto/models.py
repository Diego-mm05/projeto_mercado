from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Produto(models.Model):
    TIPO_CHOICES = [
        ('mercado', 'Mercado (Unidade)'),
        ('estoque', 'Estoque (Caixa)'),
    ]

    nome = models.CharField(max_length=100)

    preco_custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço de custo',
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    preco_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço de venda',
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    estoque = models.PositiveIntegerField()

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='mercado'
    )

    codigo_barras = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    def lucro_unitario(self):
        return self.preco_venda - self.preco_custo

    def lucro_total(self):
        return self.lucro_unitario() * self.estoque

    def valor_estoque(self):
        return self.preco_custo * self.estoque

    def __str__(self):
        return f"{self.nome} - {self.get_tipo_display()}"


class Venda(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)
    lucro = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade} un"
