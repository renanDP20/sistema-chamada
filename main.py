"""
main.py — Janela principal do Sistema de Chamada.
"""

import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStatusBar, QMessageBox, QFrame
)

import db
from icones import get_icon
from ui_alunos import AbaAlunos
from ui_chamada import AbaChamada
from ui_calendario import AbaCalendario
from ui_estatisticas import AbaEstatisticas
from ui_ocorrencias import AbaOcorrencias

# ---------------------------------------------------------------------------
# Paleta global dark
# ---------------------------------------------------------------------------
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1A1F2E;
    color: #E0E6F0;
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
}
QTabWidget::pane {
    border: 1px solid #2A3050;
    border-radius: 0 8px 8px 8px;
    background: #1A1F2E;
}
QTabBar::tab {
    background: #252B3D;
    color: #9AA3C0;
    padding: 10px 28px;
    border-radius: 8px 8px 0 0;
    margin-right: 3px;
    font-size: 13px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
    color: white;
}
QTabBar::tab:hover:!selected {
    background: #2A3050;
    color: #E0E6F0;
}
QScrollBar:vertical {
    background: #1A1F2E; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3A4560; border-radius: 4px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #1A1F2E; height: 8px; border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #3A4560; border-radius: 4px; min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QToolTip {
    background: #252B3D; color: #E0E6F0; border: 1px solid #3A4560;
    font-size: 12px; padding: 4px 8px; border-radius: 4px;
}
QMessageBox {
    background: #1E2233;
    color: #E0E6F0;
}
QMessageBox QLabel { color: #E0E6F0; font-size: 13px; }
QMessageBox QPushButton {
    background: #6C63FF; color: white; border-radius: 6px;
    padding: 6px 16px; font-size: 12px; min-width: 80px;
}
QMessageBox QPushButton:hover { background: #8B85FF; }
"""


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F1220,
                    stop:0.5 #1A1F2E,
                    stop:1 #0F1220
                );
                border-bottom: 1px solid #3A4560;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo / Título
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("app_icon").pixmap(26, 26))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(icon_lbl)

        logo_lbl = QLabel("Sistema de Chamada")
        font = QFont("Segoe UI", 16)
        font.setBold(True)
        logo_lbl.setFont(font)
        logo_lbl.setStyleSheet("color: #E0E6F0; border: none; background: transparent; margin-left: 6px;")
        layout.addWidget(logo_lbl)

        sub = QLabel("Sistema de chamada ABDA - João Victor Pavanelli & Renan Denadai de Paula")
        sub.setStyleSheet("color: #6C63FF; font-size: 11px; border: none; background: transparent; margin-left: 8px;")
        layout.addWidget(sub)

        layout.addStretch()

        # Botão atualizar
        self.btn_atualizar = QPushButton("Atualizar (F5)")
        self.btn_atualizar.setIcon(get_icon("atualizar"))
        self.btn_atualizar.setToolTip("Atualizar os dados da tela atual (Tecla F5)")
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background: #252B3D; color: #9AA3C0; border: 1px solid #3A4560;
                border-radius: 8px; padding: 7px 16px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: #3A4560; color: #E0E6F0; border-color: #6C63FF; }
        """)
        layout.addWidget(self.btn_atualizar)

        # Botão backup
        self.btn_backup = QPushButton("Fazer backup agora")
        self.btn_backup.setIcon(get_icon("backup"))
        self.btn_backup.setStyleSheet("""
            QPushButton {
                background: #252B3D; color: #9AA3C0; border: 1px solid #3A4560;
                border-radius: 8px; padding: 7px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #3A4560; color: #E0E6F0; }
        """)
        layout.addWidget(self.btn_backup)

        # Data/hora
        self.data_lbl = QLabel("")
        self.data_lbl.setStyleSheet("color: #6A7490; font-size: 11px; margin-left: 16px; border: none; background: transparent;")
        self._atualizar_data()
        layout.addWidget(self.data_lbl)

    def _atualizar_data(self):
        now = datetime.now()
        dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        dia_sem = dias[now.weekday()]
        self.data_lbl.setText(f"{dia_sem}, {now.strftime('%d/%m/%Y')}")


# ---------------------------------------------------------------------------
# Janela Principal
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Chamada — Digital Makers & Robótica")
        self.setWindowIcon(get_icon("app_icon"))
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)
        self.setStyleSheet(DARK_STYLE)

        # Widget central
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central)

        # Header
        self.header = Header()
        self.header.btn_atualizar.clicked.connect(self.atualizar_pagina_atual)
        self.header.btn_backup.clicked.connect(self._fazer_backup)
        main_layout.addWidget(self.header)

        # Atalho de teclado F5 e Ctrl+R para atualizar tela atual
        self.shortcut_f5 = QShortcut(QKeySequence("F5"), self)
        self.shortcut_f5.activated.connect(self.atualizar_pagina_atual)
        self.shortcut_ctrl_r = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut_ctrl_r.activated.connect(self.atualizar_pagina_atual)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        main_layout.addWidget(self.tabs)

        # Abas
        self.aba_alunos = AbaAlunos()
        self.aba_chamada = AbaChamada()
        self.aba_calendario = AbaCalendario()
        self.aba_stats = AbaEstatisticas()
        self.aba_ocorrencias = AbaOcorrencias()

        self.tabs.addTab(self.aba_alunos, get_icon("aluno"), "Alunos")
        self.tabs.addTab(self.aba_chamada, get_icon("chamada"), "Chamada")
        self.tabs.addTab(self.aba_calendario, get_icon("calendario"), "Calendário")
        self.tabs.addTab(self.aba_stats, get_icon("estatisticas"), "Estatísticas")
        self.tabs.addTab(self.aba_ocorrencias, get_icon("alerta"), "Ocorrências")

        # Conecta sinais
        self.aba_alunos.aluno_alterado.connect(self.aba_chamada.atualizar_turmas)
        self.aba_alunos.aluno_alterado.connect(self.aba_ocorrencias.recarregar_tudo)
        self.aba_calendario.navegar_para_chamada.connect(self._abrir_chamada_do_calendario)
        self.aba_chamada.btn_salvar.clicked.connect(self.aba_calendario.recarregar_mes)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Status bar
        self.status = QStatusBar()
        self.status.setStyleSheet("QStatusBar { background: #0F1220; color: #6A7490; font-size: 11px; }")
        self.setStatusBar(self.status)
        self.status.showMessage("Banco de dados carregado com sucesso — Pressione F5 para atualizar")

    def _abrir_chamada_do_calendario(self, turma_id: str, data_str: str):
        """Abre a aba de chamada e carrega a turma e data selecionadas no calendário."""
        self.aba_chamada.abrir_chamada_para(turma_id, data_str)
        self.tabs.setCurrentIndex(1)
        self.status.showMessage(f"Carregada chamada para {data_str}", 4000)

    def _on_tab_changed(self, index: int):
        if index == 2:
            self.aba_calendario.recarregar_mes()
        elif index == 3:
            self.aba_stats.atualizar()
        elif index == 4:
            self.aba_ocorrencias.atualizar()

    def atualizar_pagina_atual(self):
        """Atualiza os dados da aba atual exibida ao pressionar F5 ou clicar em Atualizar."""
        self.header._atualizar_data()
        idx = self.tabs.currentIndex()
        if idx == 0:
            self.aba_alunos.recarregar_tudo()
            self.status.showMessage("Lista de alunos atualizada com sucesso!", 4000)
        elif idx == 1:
            self.aba_chamada.recarregar_tudo()
            self.status.showMessage("Chamada da turma atualizada com sucesso!", 4000)
        elif idx == 2:
            self.aba_calendario.recarregar_mes()
            self.status.showMessage("Calendário atualizado com sucesso!", 4000)
        elif idx == 3:
            self.aba_stats.atualizar()
            self.status.showMessage("Estatísticas atualizadas com sucesso!", 4000)
        elif idx == 4:
            self.aba_ocorrencias.recarregar_tudo()
            self.status.showMessage("Ocorrências atualizadas com sucesso!", 4000)

    def _fazer_backup(self):
        try:
            dest = db.fazer_backup("manual")
            QMessageBox.information(
                self, "Backup realizado com sucesso",
                f"Backup salvo em:\n{dest}"
            )
            self.status.showMessage(f"Backup realizado: {dest.name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro no backup", str(e))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    # Permite que o Windows exiba o ícone correto na barra de tarefas
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("abda.sistema.chamada.2026")
    except Exception:
        pass

    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Chamada")
    app.setOrganizationName("Digital Makers & Robótica")
    app.setWindowIcon(get_icon("app_icon"))

    # Fonte padrão
    font = QFont("Segoe UI", 11)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
