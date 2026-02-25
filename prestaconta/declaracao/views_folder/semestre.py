from ..models import *
from contrapartida.models import *

import os
import zipfile
from threading import Lock
from datetime import datetime, date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.cache import never_cache

from .contrapartida_rh import gerar_declaracao_contrapartida_rh
from .contrapartida_pesquisa import gerar_declaracao_contrapartida_pesquisa
from .contrapartida_so import gerar_declaracao_contrapartida_so
from .contrapartida_equipamento import gerar_declaracao_contrapartida_equipamento
from ..gerar_docx import (
    gerar_docx_rh as _gerar_docx_rh,
    gerar_docx_pesquisa as _gerar_docx_pesquisa,
    gerar_docx_so as _gerar_docx_so,
    gerar_docx_equipamento as _gerar_docx_equipamento,
    _pasta_declaracoes_semestre,
    _caminho_docx_declaracao,
    _caminho_docx_equipamento,
)


# =========================================================
# PROGRESSO GLOBAL
# =========================================================
progresso_lock = Lock()
progresso = {
    "status": "aguardando",   # aguardando | gerando | finalizado | erro
    "percentual": 0,
    "mensagem": "",
    "ano": None,
    "semestre": None,
    "finalizado": False,
}


def _set_progresso(**kwargs):
    with progresso_lock:
        progresso.update(kwargs)


def _no_cache_json(data, status=200):
    resp = JsonResponse(data, status=status)
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    return resp


# =========================================================
# HTTP WRAPPERS PARA GERAR DOCX
# =========================================================

@login_required
def gerar_docx_rh(request, declaracao_id):
    decl = get_object_or_404(declaracao_contrapartida_rh, id=declaracao_id)
    _gerar_docx_rh(decl)
    messages.success(request, "DOCX RH gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={decl.projeto}&mes={decl.mes}&ano={decl.ano}')


@login_required
def gerar_docx_pesquisa(request, declaracao_id):
    decl = get_object_or_404(declaracao_contrapartida_pesquisa, id=declaracao_id)
    _gerar_docx_pesquisa(decl)
    messages.success(request, "DOCX Pesquisa gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={decl.projeto}&mes={decl.mes}&ano={decl.ano}')


@login_required
def gerar_docx_so(request, declaracao_id):
    decl = get_object_or_404(declaracao_contrapartida_so, id=declaracao_id)
    _gerar_docx_so(decl)
    messages.success(request, "DOCX SO gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?projeto={decl.projeto}&mes={decl.mes}&ano={decl.ano}')


@login_required
def gerar_docx_equipamento(request, id):
    decl = get_object_or_404(declaracao_contrapartida_equipamento, id=id)
    _gerar_docx_equipamento(decl)
    messages.success(request, "DOCX Equipamento gerado.")
    url = reverse('declaracoes_menu')
    return redirect(f'{url}?mes={decl.mes}&ano={decl.ano}')


def gerar_declaracoes_semestre(request):
    """
    Página para:
      - mostrar qtd de projetos no semestre
      - indicar se o semestre está completo (todas as declarações existem)
      - gerar declarações pendentes
      - gerar ZIP com as declarações DOCX existentes
    """
    hoje = date.today()
    ano_atual = hoje.year
    semestre_atual = 1 if hoje.month <= 6 else 2

    # semestre padrão: anterior
    if semestre_atual == 1:
        semestre_default = 2
        ano_default = ano_atual - 1
    else:
        semestre_default = 1
        ano_default = ano_atual

    ano = int(request.GET.get("ano", ano_default))
    semestre = int(request.GET.get("semestre", semestre_default))
    meses_semestre = [1, 2, 3, 4, 5, 6] if semestre == 1 else [7, 8, 9, 10, 11, 12]

    # projetos ativos no semestre
    data_ini = date(ano, 1 if semestre == 1 else 7, 1)
    mes_fim = 6 if semestre == 1 else 12
    dia_fim = 30 if semestre == 1 else 31
    data_fim = date(ano, mes_fim, dia_fim)

    projetos = projeto.objects.filter(
        ativo=True,
        data_inicio__lte=data_fim,
        data_fim__gte=data_ini
    ).order_by("nome")

    projetos_qtd = projetos.count()

    # ---- contagem de declarações existentes ----
    total_existente = 0
    total_esperado = (projetos_qtd * 3 * len(meses_semestre)) + len(meses_semestre)

    for p in projetos:
        for mes in meses_semestre:
            if declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                total_existente += 1
            if declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                total_existente += 1
            if declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                total_existente += 1

    for mes in meses_semestre:
        if declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).exists():
            total_existente += 1

    semestre_completo = (total_existente == total_esperado)

    # ---- gerar declarações pendentes ----
    if request.GET.get("gerar") == "1":
        total_pesq = total_rh = total_so = total_equip = 0

        for p in projetos:
            for mes in meses_semestre:

                # PESQUISA
                if not declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_pesquisa(request, p.id, mes, ano)
                decl_p = declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_p:
                    _gerar_docx_pesquisa(decl_p)
                    total_pesq += 1

                # RH
                if not declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_rh(request, p.id, mes, ano)
                decl_rh = declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_rh:
                    _gerar_docx_rh(decl_rh)
                    total_rh += 1

                # SO
                if not declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_so(request, p.id, mes, ano)
                decl_so = declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_so:
                    _gerar_docx_so(decl_so)
                    total_so += 1

        # EQUIPAMENTO (1 por mês, global)
        for mes in meses_semestre:
            if not declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).exists():
                gerar_declaracao_contrapartida_equipamento(request, p.id, mes, ano)
            decl_eq = declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first()
            if decl_eq:
                _gerar_docx_equipamento(decl_eq)
                total_equip += 1

        messages.success(
            request,
            f"Declarações (e DOCX) gerados. Pesquisa={total_pesq}, RH={total_rh}, SO={total_so}, Equip={total_equip}"
        )

        request.session["ultima_geracao_zip"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        return redirect(reverse("gerar_declaracoes_semestre") + f"?ano={ano}&semestre={semestre}")

    # ---- ZIP do semestre ----
    pasta_semestre = _pasta_declaracoes_semestre(ano, semestre)
    zip_filename = f"declaracoes_{ano}-{semestre}.zip"
    zip_path = os.path.join(pasta_semestre, zip_filename)
    zip_exists = os.path.exists(zip_path)

    if request.GET.get("zip") == "1":
        # recria o ZIP sempre, com o que existir
        if os.path.exists(zip_path):
            os.remove(zip_path)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 1) arquivos por projeto
            for p in projetos:
                peia = p.peia
                nome_proj = p.nome

                for mes in meses_semestre:
                    caminho_rh = _caminho_docx_declaracao(ano, semestre, peia, nome_proj, "rh", mes)
                    if os.path.exists(caminho_rh):
                        zipf.write(caminho_rh, os.path.relpath(caminho_rh, pasta_semestre))

                    caminho_pesq = _caminho_docx_declaracao(ano, semestre, peia, nome_proj, "pesquisa", mes)
                    if os.path.exists(caminho_pesq):
                        zipf.write(caminho_pesq, os.path.relpath(caminho_pesq, pasta_semestre))

                    caminho_so = _caminho_docx_declaracao(ano, semestre, peia, nome_proj, "so", mes)
                    if os.path.exists(caminho_so):
                        zipf.write(caminho_so, os.path.relpath(caminho_so, pasta_semestre))

            # 2) equipamentos (1 por mês, global) — fora do loop de projetos
            for mes in meses_semestre:
                caminho_eq = _caminho_docx_equipamento(ano, semestre, mes)
                if os.path.exists(caminho_eq):
                    zipf.write(caminho_eq, os.path.relpath(caminho_eq, pasta_semestre))

        messages.success(request, "ZIP criado com sucesso!")
        return redirect(reverse("gerar_declaracoes_semestre") + f"?ano={ano}&semestre={semestre}")

    ultima_data = request.session.get("ultima_geracao_zip")

    return render(request, "declaracao/gerar_declaracoes_semestre.html", {
        "ano": ano,
        "semestre": semestre,
        "projetos_qtd": projetos_qtd,
        "semestre_completo": semestre_completo,
        "zip_exists": os.path.exists(zip_path),
        "zip_filename": zip_filename,
        "ultima_data": ultima_data,
    })


@never_cache
@login_required
def progresso_semestre(request):
    with progresso_lock:
        return _no_cache_json(progresso)


@never_cache
@login_required
def gerar_semestre_ajax(request):
    #print("Entrou no gerar_semestre_ajax")
    """
    Gera declarações + DOCX no disco, atualizando o dict global 'progresso'.
    O front faz polling em /progresso_semestre/ pra atualizar a barra.
    """
    try:
        ano = int(request.GET.get("ano"))
        semestre = int(request.GET.get("semestre"))
    except (TypeError, ValueError):
        _set_progresso(status="erro", mensagem="Parâmetros inválidos (ano/semestre).", finalizado=True)
        return _no_cache_json({"ok": False, "erro": "Parâmetros inválidos."}, status=400)

    meses = [1, 2, 3, 4, 5, 6] if semestre == 1 else [7, 8, 9, 10, 11, 12]

    data_ini = date(ano, 1 if semestre == 1 else 7, 1)
    data_fim = date(ano, 6 if semestre == 1 else 12, 30 if semestre == 1 else 31)

    projetos = projeto.objects.filter(
        ativo=True,
        data_inicio__lte=data_fim,
        data_fim__gte=data_ini
    ).order_by("nome")

    projetos_qtd = projetos.count()

    # total de "passos" pra barra:
    # 3 docx por projeto/mês (pesq, rh, so) + 1 docx de equipamento por mês
    total_ops = (projetos_qtd * 3 * len(meses)) + len(meses)
    if total_ops <= 0:
        _set_progresso(
            status="finalizado",
            percentual=100,
            mensagem="Nada a gerar (sem projetos no semestre).",
            ano=ano,
            semestre=semestre,
            finalizado=True,
        )
        return _no_cache_json({"ok": True, "vazio": True})

    atual = 0

    _set_progresso(
        status="gerando",
        percentual=0,
        mensagem="Iniciando geração...",
        ano=ano,
        semestre=semestre,
        finalizado=False,
    )

    def _msg_projeto(tipo: str, ano: int, mes: int, p) -> str:
        return f"Gerando {tipo} - {ano} - {mes:02d} - {p.peia} - {p.nome}"

    def _msg_equip(tipo: str, ano: int, mes: int) -> str:
        return f"Gerando {tipo} - {ano} - {mes:02d}"

    # log opcional (ajuda a debugar travas)
    logdir = os.path.join(settings.MEDIA_ROOT, "logs")
    os.makedirs(logdir, exist_ok=True)
    logpath = os.path.join(logdir, f"geracao_{ano}_{semestre}.log")

    def log(msg):
        with open(logpath, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - {msg}\n")

    log(f"Início geração semestre {semestre}/{ano}, projetos={projetos_qtd}")

    # pega um projeto "fallback" para a declaração de equipamento (sua função exige projeto_id)
    p_fallback = projetos.first()

    try:
        #print("Entrou no try")
        # -------------------------
        # LOOP PROJETOS / MESES
        # -------------------------
        for p in projetos:
            #print("entrou")
            #print(p)
            for mes in meses:
                #print(mes)

                # ===== PESQUISA =====
                if not declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_pesquisa(request, p.id, mes, ano)

                decl_p = declaracao_contrapartida_pesquisa.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_p:
                    #print(decl_p)
                    path = _gerar_docx_pesquisa(decl_p)
                    log(f"SALVO PESQUISA: {path}")
                    

                atual += 1
                _set_progresso(
                    percentual=int(100 * atual / total_ops),
                    mensagem=_msg_projeto("Pesquisa", ano, mes, p)
                )

                # ===== RH =====
                if not declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_rh(request, p.id, mes, ano)

                decl_rh = declaracao_contrapartida_rh.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                #print(decl_rh)
                if decl_rh:
                    path = _gerar_docx_rh(decl_rh)
                    log(f"SALVO RH: {path}")


                atual += 1
                _set_progresso(
                    percentual=int(100 * atual / total_ops),
                    mensagem=_msg_projeto("RH", ano, mes, p)
                )


                # ===== SO =====
                if not declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).exists():
                    gerar_declaracao_contrapartida_so(request, p.id, mes, ano)

                decl_so = declaracao_contrapartida_so.objects.filter(id_projeto=p.id, mes=mes, ano=ano).first()
                if decl_so:
                    path = _gerar_docx_so(decl_so)
                    log(f"SALVO SO: {path}")

                atual += 1
                _set_progresso(
                    percentual=int(100 * atual / total_ops),
                    mensagem=_msg_projeto("SO", ano, mes, p)
                )

        # -------------------------
        # EQUIPAMENTOS (1 por mês)
        # -------------------------
        for mes in meses:
            if not declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).exists():
                if p_fallback:
                    gerar_declaracao_contrapartida_equipamento(request, p_fallback.id, mes, ano)

            decl_eq = declaracao_contrapartida_equipamento.objects.filter(mes=mes, ano=ano).first()
            if decl_eq:
                path = _gerar_docx_equipamento(decl_eq)
                log(f"SALVO EQUIPAMENTO: {path}")

            atual += 1
            _set_progresso(
                percentual=int(100 * atual / total_ops),
                mensagem=_msg_equip("Equipamento", ano, mes)
            )

        _set_progresso(status="finalizado", percentual=100, mensagem="Geração concluída!", finalizado=True)
        log("Finalizado com sucesso.")
        return _no_cache_json({"ok": True})

    except Exception as e:
        log(f"ERRO: {repr(e)}")
        _set_progresso(status="erro", mensagem=f"Erro: {e}", finalizado=True)
        return _no_cache_json({"ok": False, "erro": str(e)}, status=500)
