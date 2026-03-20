from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F, DecimalField, Q
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required

import cv2
import numpy as np
import zxingcpp
from xhtml2pdf import pisa

from .models import Produto, Venda


def inicio(request):
    return render(request, 'produto/inicio.html')


@login_required
def index_loja(request):
    q = request.GET.get('q', '').strip()
    produtos = Produto.objects.filter(tipo='mercado', estoque__gt=0)

    if q:
        produtos = produtos.filter(
            Q(nome__icontains=q) |
            Q(codigo_barras__icontains=q)
        )

    return render(request, 'produto/index_loja.html', {
        'produtos': produtos,
        'q': q
    })


@login_required
def index_estoque(request):
    produtos = Produto.objects.filter(tipo='estoque')
    return render(request, 'produto/index_estoque.html', {'produtos': produtos})


@login_required
def cadastrar(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', 'mercado')
        codigo_barras = request.POST.get('codigo_barras') or None

        if codigo_barras and Produto.objects.filter(codigo_barras=codigo_barras).exists():
            existente = Produto.objects.get(codigo_barras=codigo_barras)
            return render(request, 'produto/cadastrar.html', {
                'produto_existente': existente,
                'aviso_existente': True
            })

        try:
            preco_custo = Decimal(request.POST.get('preco_custo', '0'))
            preco_venda = Decimal(request.POST.get('preco_venda', '0'))
            if preco_custo <= 0 or preco_venda <= 0:
                raise InvalidOperation
        except:
            return render(request, 'produto/cadastrar.html', {
                'erro': 'Preços devem ser maiores que zero'
            })

        try:
            estoque = int(request.POST.get('estoque', 0))
            if estoque < 0:
                raise ValueError
        except:
            estoque = 0

        Produto.objects.create(
            nome=nome,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            estoque=estoque,
            tipo=tipo,
            codigo_barras=codigo_barras
        )

        return redirect(
            'produto:index_loja' if tipo == 'mercado'
            else 'produto:index_estoque'
        )

    return render(request, 'produto/cadastrar.html')


@login_required
def editar(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        produto.nome = request.POST.get('nome', '').strip()

        try:
            produto.preco_custo = Decimal(request.POST.get('preco_custo'))
            produto.preco_venda = Decimal(request.POST.get('preco_venda'))
            if produto.preco_custo <= 0 or produto.preco_venda <= 0:
                raise InvalidOperation
        except:
            messages.error(request, 'Preços devem ser maiores que zero')
            return redirect('produto:editar', produto_id=produto.id)

        try:
            produto.estoque = int(request.POST.get('estoque', 0))
            if produto.estoque < 0:
                raise ValueError
        except:
            produto.estoque = 0

        produto.tipo = request.POST.get('tipo', 'mercado')
        produto.save()

        return redirect(
            'produto:index_loja' if produto.tipo == 'mercado'
            else 'produto:index_estoque'
        )

    return render(request, 'produto/editar.html', {'produto': produto})


@login_required
def excluir(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    tipo = produto.tipo
    produto.delete()

    return redirect(
        'produto:index_loja' if tipo == 'mercado'
        else 'produto:index_estoque'
    )


@require_GET
@login_required
def buscar_por_codigo(request):
    codigo = request.GET.get('codigo')
    if not codigo:
        return JsonResponse({'error': 'codigo ausente'}, status=400)

    try:
        p = Produto.objects.get(codigo_barras=codigo)
        return JsonResponse({
            'id': p.id,
            'nome': p.nome,
            'preco_custo': str(p.preco_custo),
            'preco_venda': str(p.preco_venda),
            'estoque': p.estoque,
            'tipo': p.tipo,
            'codigo_barras': p.codigo_barras,
        })
    except Produto.DoesNotExist:
        return JsonResponse({'found': False}, status=404)


@csrf_exempt
@login_required
def ler_barcode(request):
    if request.method != 'POST' or 'image' not in request.FILES:
        return JsonResponse({'error': 'imagem_ausente'}, status=400)

    data = request.FILES['image'].read()
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        return JsonResponse({'error': 'imagem_invalida'}, status=400)

    img = cv2.bilateralFilter(img, 9, 75, 75)
    results = zxingcpp.read_barcodes(img)

    if not results:
        return JsonResponse({'error': 'codigo_nao_detectado'}, status=404)

    r = results[0]
    return JsonResponse({'code': r.text, 'format': str(r.format)})


@require_POST
@login_required
def vender_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    try:
        quantidade = int(request.POST.get('quantidade', 1))
        if quantidade <= 0:
            raise ValueError
    except:
        messages.error(request, 'Quantidade inválida')
        return redirect('produto:index_loja')

    if produto.estoque < quantidade:
        messages.error(request, 'Estoque insuficiente')
        return redirect('produto:index_loja')

    preco_venda = produto.preco_venda
    preco_custo = produto.preco_custo
    lucro = (preco_venda - preco_custo) * quantidade

    Venda.objects.create(
        produto=produto,
        quantidade=quantidade,
        preco_venda=preco_venda,
        preco_custo=preco_custo,
        lucro=lucro
    )

    produto.estoque -= quantidade
    produto.save()

    messages.success(
        request,
        f'Venda de {quantidade}x {produto.nome} realizada com sucesso!'
    )
    return redirect('produto:index_loja')


@login_required
def caixa(request):
    hoje = timezone.now().date()
    vendas = Venda.objects.filter(data__date=hoje)

    totais = vendas.aggregate(
        total_vendido=Sum(F('preco_venda') * F('quantidade'), output_field=DecimalField()),
        total_lucro=Sum('lucro')
    )

    return render(request, 'produto/caixa.html', {
        'vendas': vendas,
        'total_vendido': totais['total_vendido'] or 0,
        'total_lucro': totais['total_lucro'] or 0,
    })


@login_required
def relatorio(request):
    anos = Venda.objects.dates('data', 'year')
    anos_list = sorted({d.year for d in anos}, reverse=True)
    return render(request, 'produto/relatorio_filtro.html', {'anos': anos_list})


@login_required
def gerar_pdf(request):
    data_inicio = request.GET.get('data_inicio')
    data_final = request.GET.get('data_final')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    vendas = Venda.objects.all().order_by('-data')

    if data_inicio:
        vendas = vendas.filter(data__date__gte=data_inicio)
    if data_final:
        vendas = vendas.filter(data__date__lte=data_final)
    if mes:
        vendas = vendas.filter(data__month=mes)
    if ano:
        vendas = vendas.filter(data__year=ano)

    totais = vendas.aggregate(
        receita_total=Sum(F('preco_venda') * F('quantidade'), output_field=DecimalField()),
        custo_total=Sum(F('preco_custo') * F('quantidade'), output_field=DecimalField()),
        lucro_total=Sum('lucro')
    )

    context = {
        'vendas': vendas,
        'receita': totais['receita_total'] or 0,
        'custo': totais['custo_total'] or 0,
        'lucro': totais['lucro_total'] or 0,
        'agora': datetime.now()
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_vendas.pdf"'

    html = get_template('produto/relatorio_pdf.html').render(context)
    pisa.CreatePDF(html, dest=response)

    return response