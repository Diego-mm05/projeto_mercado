from django.urls import path
from . import views

app_name = 'produto'

urlpatterns = [
    path('', views.inicio, name='inicio'),

    path('loja/', views.index_loja, name='index_loja'),
    path('estoque/', views.index_estoque, name='index_estoque'),

    path('cadastrar/', views.cadastrar, name='cadastrar'),
    path('editar/<int:produto_id>/', views.editar, name='editar'),
    path('excluir/<int:produto_id>/', views.excluir, name='excluir'),

    # VENDA (APENAS UMA ROTA)
    path('vender/<int:produto_id>/', views.vender_produto, name='vender'),

    path('caixa/', views.caixa, name='caixa'),
    
    # RELATÓRIO
    path('relatorio/', views.relatorio, name='relatorio'),
    path('relatorio/pdf/', views.gerar_pdf, name='gerar_pdf'),

    # CÓDIGO DE BARRAS
    path('api/buscar_por_codigo/', views.buscar_por_codigo, name='buscar_por_codigo'),
    path('api/ler_barcode/', views.ler_barcode, name='ler_barcode'),
]
