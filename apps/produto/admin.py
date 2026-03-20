from django.contrib import admin
from apps.produto.models import Produto,Venda
@admin.register(Produto)
class adminProduto(admin.ModelAdmin):
    list_display = ('id', 'nome', 'preco_venda', 'preco_custo', 'estoque', 'tipo', 'codigo_barras')
    list_display_links = ('id',)
    search_fields = ('nome',)
    list_editable = ('nome', 'preco_venda', 'preco_custo', 'estoque', 'tipo', 'codigo_barras')

@admin.register(Venda)
class adminVenda(admin.ModelAdmin):
    list_display = ('id', 'produto', 'quantidade', 'preco_venda', 'preco_custo', 'lucro', 'data')
    list_display_links = ('id',)
    search_fields = ('produto',)
    list_editable = ('produto', 'quantidade', 'preco_venda', 'preco_custo', 'lucro',)
