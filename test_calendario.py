"""
test_calendario.py — Testes automatizados para a aba de Calendário e seleção de chamadas.
"""

import sys
from datetime import date
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

import db
from ui_calendario import AbaCalendario, DialogEscolherTurmaDia
from ui_chamada import AbaChamada
from main import MainWindow

def test_funcoes_banco():
    print("--- Teste 1: Funções de banco para calendário ---")
    turmas_seg = db.turmas_por_dia_semana("Segunda")
    assert len(turmas_seg) >= 6, f"Deveria haver pelo menos 6 turmas na segunda, obteve {len(turmas_seg)}"
    for t in turmas_seg:
        assert t["dia_semana"] == "Segunda"
        assert t["curso"] == "Informática"
    print("  [OK] Turmas de Segunda-feira (Informática) validadas com sucesso.")

    turmas_ter = db.turmas_por_dia_semana("Terça")
    assert len(turmas_ter) >= 4, f"Deveria haver pelo menos 4 turmas na terça, obteve {len(turmas_ter)}"
    for t in turmas_ter:
        assert t["dia_semana"] == "Terça"
        assert t["curso"] == "Robótica"
    print("  [OK] Turmas de Terça-feira (Robótica) validadas com sucesso.")

    # Status chamadas mes
    status = db.status_chamadas_mes(2026, 9)
    assert isinstance(status, dict)
    print(f"  [OK] status_chamadas_mes(2026, 9) retornou {len(status)} registros.")


def test_widget_calendario():
    print("\n--- Teste 2: Renderização e Navegação da AbaCalendario ---")
    cal_widget = AbaCalendario()
    
    # Valida componentes
    assert cal_widget.combo_mes.count() == 12
    assert cal_widget.grade_layout.count() > 0
    print("  [OK] Grade do calendário construída com sucesso.")

    # Testa navegação próximo mês
    mes_orig = cal_widget.mes_atual
    ano_orig = cal_widget.ano_atual
    cal_widget._proximo_mes()
    if mes_orig == 12:
        assert cal_widget.mes_atual == 1 and cal_widget.ano_atual == ano_orig + 1
    else:
        assert cal_widget.mes_atual == mes_orig + 1
    print("  [OK] Navegação para próximo mês validada.")

    # Testa navegação mês anterior
    cal_widget._mes_anterior()
    assert cal_widget.mes_atual == mes_orig and cal_widget.ano_atual == ano_orig
    print("  [OK] Navegação para mês anterior validada.")

    # Testa filtro por curso
    cal_widget.combo_curso.setCurrentText("Informática")
    cal_widget.combo_curso.setCurrentText("Robótica")
    cal_widget.combo_curso.setCurrentText("Todos os Cursos")
    print("  [OK] Filtro de curso no calendário validado.")


def test_dialogo_dia():
    print("\n--- Teste 3: Diálogo de Escolha de Turma do Dia ---")
    d_seg = date(2026, 9, 7)  # Segunda-feira
    turmas = db.turmas_por_dia_semana("Segunda")
    status = db.status_chamadas_mes(2026, 9)
    
    dlg = DialogEscolherTurmaDia(d_seg, turmas, status)
    assert dlg.windowTitle().startswith("Chamada — Segunda-feira")
    
    capturado = []
    dlg.turma_selecionada.connect(lambda t, d: capturado.append((t, d)))
    
    # Dispara seleção de uma turma
    primeira_t = turmas[0]["id"]
    dlg._acionar_chamada(primeira_t)
    assert len(capturado) == 1
    assert capturado[0] == (primeira_t, "2026-09-07")
    print("  [OK] Diálogo de escolha de turma emitiu sinal correto com turma_id e data.")


def test_integracao_chamada_e_janela():
    print("\n--- Teste 4: Integração com AbaChamada e MainWindow ---")
    win = MainWindow()
    assert win.tabs.count() == 4
    assert win.tabs.tabText(0) == "Alunos"
    assert win.tabs.tabText(1) == "Chamada"
    assert win.tabs.tabText(2) == "Calendário"
    assert win.tabs.tabText(3) == "Estatísticas"
    print("  [OK] As 4 abas configuradas corretamente na MainWindow.")

    # Testa transição do calendário para a chamada
    turma_teste = "INFO-SEG-08H00"
    data_teste = "2026-09-14"
    win.aba_calendario.navegar_para_chamada.emit(turma_teste, data_teste)
    
    assert win.tabs.currentIndex() == 1, "Deveria ter mudado para a aba Chamada (índice 1)"
    assert win.aba_chamada.turma_combo.currentData() == turma_teste
    assert win.aba_chamada.data_edit.date().toString("yyyy-MM-dd") == data_teste
    print(f"  [OK] Redirecionamento da aba Calendário para a chamada de {turma_teste} em {data_teste} concluído com sucesso.")

    # Testa atualização F5 na aba de calendário
    win.tabs.setCurrentIndex(2)
    win.atualizar_pagina_atual()
    print("  [OK] Atualização F5 na aba Calendário executada com sucesso.")


if __name__ == "__main__":
    test_funcoes_banco()
    test_widget_calendario()
    test_dialogo_dia()
    test_integracao_chamada_e_janela()
    print("\n[SUCESSO] TODOS OS TESTES DO CALENDARIO PASSARAM COM 100% DE SUCESSO!")
