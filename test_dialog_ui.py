"""
test_dialog_ui.py — Teste de interface do DialogImportarEstruturado
"""

import sys
import os
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import db
from PySide6.QtWidgets import QApplication
from ui_importar import DialogImportarEstruturado

def test_dialog():
    app = QApplication.instance() or QApplication(sys.argv)
    db.init_db()

    # Cria arquivo temporário com o exemplo
    exemplo = """SEGUNDA_8H_9H {
ANNA ALICE SANTOS FERREIRA DA SILVA;01/08/2017;Feminino;
ANNA CLARA SANTOS FERREIRA DA SILVA;11/08/2016;Feminino;
BENJAMIM GABRIEL DE OLIVEIRA BALDERRAMA;22/06/2016;Masculino;
}

SEGUNDA_9H_10H {
GABRIEL SILVA AFONSO;21/01/2011;Masculino;
HELENA HADLICH ESQUEDA;13/04/2017;Feminino;
}

TERCA_8H_9H {
ALICE BENDER RIBEIRO;09/01/2011;Feminino;
BRYAN FRANCO DE MELO;24/04/2012;Masculino;
}
"""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(exemplo)
        tmp_path = f.name

    try:
        dlg = DialogImportarEstruturado(tmp_path)
        assert dlg.tabela_turmas.rowCount() == 3
        print(f"  [OK] Tabela de turmas carregada com {dlg.tabela_turmas.rowCount()} turmas")

        # Seleciona turma 0
        dlg.tabela_turmas.selectRow(0)
        dlg._on_turma_selecionada()
        assert dlg.tabela_alunos.rowCount() == 3
        print(f"  [OK] Turma 0 tem {dlg.tabela_alunos.rowCount()} alunos exibidos")

        # Seleciona turma 1
        dlg.tabela_turmas.selectRow(1)
        dlg._on_turma_selecionada()
        assert dlg.tabela_alunos.rowCount() == 2
        print(f"  [OK] Turma 1 tem {dlg.tabela_alunos.rowCount()} alunos exibidos")

        # Seleciona turma 2
        dlg.tabela_turmas.selectRow(2)
        dlg._on_turma_selecionada()
        assert dlg.tabela_alunos.rowCount() == 2
        print(f"  [OK] Turma 2 tem {dlg.tabela_alunos.rowCount()} alunos exibidos")

        print("🎉 Teste do diálogo de importação concluído com sucesso!")
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    test_dialog()
