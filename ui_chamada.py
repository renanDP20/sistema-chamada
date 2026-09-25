"""
ui_chamada.py — Aba de Controle de Chamada.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QDateEdit, QMessageBox, QFileDialog, QFrame,
    QScrollArea, QLineEdit, QSizePolicy
)

import db
from icones import get_icon
from ui_importar import DialogImportarEstruturado

_COMBO = """QComboBox {
    background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
    color: #E0E6F0; padding: 7px 12px; font-size: 13px; min-width: 200px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #252B3D; color: #E0E6F0; selection-background-color: #3D3580; }"""

_BTN_PRIMARY = """QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
    color: white; border-radius: 8px; padding: 9px 20px; font-size: 13px; font-weight: bold;
}
QPushButton:hover { background: #7C75FF; }
QPushButton:disabled { background: #2A3050; color: #5A6380; }"""

_BTN_SECONDARY = """QPushButton {
    background: #2A3050; color: #9AA3C0; border-radius: 8px;
    padding: 9px 16px; font-size: 12px;
}
QPushButton:hover { background: #3A4560; color: #E0E6F0; }"""

_BTN_SUCCESS = """QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10B981);
    color: white; border-radius: 8px; padding: 9px 20px; font-size: 13px; font-weight: bold;
}
QPushButton:hover { background: #10B981; }
QPushButton:disabled { background: #2A3050; color: #5A6380; }"""


class AbaChamada(QWidget):
    def __init__(self):
        super().__init__()
        self._chamada_id: int | None = None
        self._alunos_rows: list = []
        self._build_ui()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(16)
        main.setContentsMargins(16, 16, 16, 16)

        # --- Painel de seleção ---
        sel_frame = QFrame()
        sel_frame.setStyleSheet("""
            QFrame {
                background: #252B3D; border-radius: 12px;
                border: 1px solid #3A4560;
            }
            QLabel { color: #9AA3C0; font-size: 12px; }
        """)
        sel_layout = QHBoxLayout(sel_frame)
        sel_layout.setContentsMargins(16, 12, 16, 12)
        sel_layout.setSpacing(16)

        # Curso
        c_label = QLabel("Curso")
        self.curso_combo = QComboBox()
        self.curso_combo.addItems(["Informática", "Robótica"])
        self.curso_combo.setStyleSheet(_COMBO)
        self.curso_combo.currentTextChanged.connect(self._atualizar_turmas)

        # Turma
        t_label = QLabel("Turma")
        self.turma_combo = QComboBox()
        self.turma_combo.setStyleSheet(_COMBO)
        self.turma_combo.setMaximumWidth(360)
        self.turma_combo.currentIndexChanged.connect(self._turma_selecionada)

        # Data
        d_label = QLabel("Data da aula")
        self.data_edit = QDateEdit()
        self.data_edit.setDisplayFormat("dd/MM/yyyy")
        self.data_edit.setDate(QDate.currentDate())
        self.data_edit.setCalendarPopup(True)
        self.data_edit.setStyleSheet("""
            QDateEdit {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 7px 10px; font-size: 13px; min-width: 130px;
            }
            QDateEdit:focus { border: 1px solid #6C63FF; }
        """)
        self.data_edit.dateChanged.connect(self._verificar_chamada_existente)

        btn_carregar = QPushButton("Carregar chamada")
        btn_carregar.setIcon(get_icon("chamada"))
        btn_carregar.setStyleSheet(_BTN_PRIMARY)
        btn_carregar.clicked.connect(self._carregar_chamada)

        sel_layout.addWidget(c_label)
        sel_layout.addWidget(self.curso_combo)
        sel_layout.addWidget(t_label)
        sel_layout.addWidget(self.turma_combo)
        sel_layout.addWidget(d_label)
        sel_layout.addWidget(self.data_edit)
        sel_layout.addWidget(btn_carregar)
        sel_layout.addStretch()

        main.addWidget(sel_frame)

        # --- Alerta de chamada já existente ---
        self.alerta_frame = QFrame()
        self.alerta_frame.setStyleSheet("""
            QFrame { background: #3A2A10; border: 1px solid #F59E0B;
                     border-radius: 8px; padding: 2px; }
            QLabel { color: #FBBF24; font-size: 12px; }
        """)
        alerta_lay = QHBoxLayout(self.alerta_frame)
        alerta_lay.setContentsMargins(12, 8, 12, 8)
        self.alerta_lbl = QLabel("Atenção: Chamada já registrada para esta turma e data. Ao salvar, os dados serão atualizados.")
        self.alerta_lbl.setStyleSheet("color: #FBBF24; font-size: 12px; font-weight: bold;")
        alerta_lay.addWidget(self.alerta_lbl)
        self.alerta_frame.setVisible(False)
        main.addWidget(self.alerta_frame)

        # --- Informação da turma ---
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame { background: #1E2233; border-radius: 8px; border: 1px solid #2A3050; }
            QLabel { color: #E0E6F0; }
        """)
        info_lay = QHBoxLayout(self.info_frame)
        info_lay.setContentsMargins(16, 10, 16, 10)
        self.info_turma_lbl = QLabel("")
        self.info_turma_lbl.setStyleSheet("color: #6C63FF; font-size: 14px; font-weight: bold;")
        self.info_alunos_lbl = QLabel("")
        self.info_alunos_lbl.setStyleSheet("color: #9AA3C0; font-size: 12px;")
        info_lay.addWidget(self.info_turma_lbl)
        info_lay.addStretch()
        info_lay.addWidget(self.info_alunos_lbl)
        self.info_frame.setVisible(False)
        main.addWidget(self.info_frame)

        # --- Ações rápidas ---
        acao_layout = QHBoxLayout()
        self.btn_todos_presentes = QPushButton("Marcar todos presentes")
        self.btn_todos_presentes.setIcon(get_icon("check"))
        self.btn_todos_presentes.setStyleSheet(_BTN_SECONDARY)
        self.btn_todos_presentes.clicked.connect(lambda: self._marcar_todos(True))
        self.btn_todos_presentes.setEnabled(False)

        self.btn_todos_ausentes = QPushButton("Marcar todos ausentes")
        self.btn_todos_ausentes.setIcon(get_icon("ausente"))
        self.btn_todos_ausentes.setStyleSheet(_BTN_SECONDARY)
        self.btn_todos_ausentes.clicked.connect(lambda: self._marcar_todos(False))
        self.btn_todos_ausentes.setEnabled(False)

        self.btn_importar_turma = QPushButton("Importar alunos para esta turma")
        self.btn_importar_turma.setIcon(get_icon("importar"))
        self.btn_importar_turma.setStyleSheet(_BTN_SECONDARY)
        self.btn_importar_turma.clicked.connect(self._importar_para_turma)

        acao_layout.addWidget(self.btn_todos_presentes)
        acao_layout.addWidget(self.btn_todos_ausentes)
        acao_layout.addStretch()
        acao_layout.addWidget(self.btn_importar_turma)
        main.addLayout(acao_layout)

        # --- Tabela de chamada ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["Aluno", "Presente", "Observação do dia"])
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabela.setColumnWidth(1, 100)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background: #1A1F2E; border: 1px solid #2A3050;
                border-radius: 10px; color: #E0E6F0;
                gridline-color: #2A3050; font-size: 13px;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:alternate { background: #1E2535; }
            QHeaderView::section {
                background: #252B3D; color: #9AA3C0; padding: 10px;
                border: none; font-size: 13px; font-weight: bold;
            }
        """)
        main.addWidget(self.tabela, stretch=1)

        # --- Rodapé / Botões salvar ---
        footer = QHBoxLayout()
        self.resumo_label = QLabel("")
        self.resumo_label.setStyleSheet("color: #9AA3C0; font-size: 12px;")
        footer.addWidget(self.resumo_label)
        footer.addStretch()

        self.btn_salvar = QPushButton("Salvar Chamada")
        self.btn_salvar.setIcon(get_icon("backup"))
        self.btn_salvar.setStyleSheet(_BTN_SUCCESS)
        self.btn_salvar.clicked.connect(self._salvar_chamada)
        self.btn_salvar.setEnabled(False)

        self.btn_limpar = QPushButton("Nova consulta")
        self.btn_limpar.setIcon(get_icon("atualizar"))
        self.btn_limpar.setStyleSheet(_BTN_SECONDARY)
        self.btn_limpar.clicked.connect(self._limpar)

        footer.addWidget(self.btn_limpar)
        footer.addWidget(self.btn_salvar)
        main.addLayout(footer)

        self._atualizar_turmas()

    # -----------------------------------------------------------------------
    # Lógica
    # -----------------------------------------------------------------------
    def _atualizar_turmas(self):
        curso = self.curso_combo.currentText()
        self.turma_combo.clear()
        for t in db.listar_turmas(curso):
            self.turma_combo.addItem(t["nome"], t["id"])

    def _turma_selecionada(self):
        self._verificar_chamada_existente()

    def _verificar_chamada_existente(self):
        turma_id = self.turma_combo.currentData()
        if not turma_id:
            return
        qd = self.data_edit.date()
        data_str = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"
        existente = db.get_chamada(turma_id, data_str)
        self.alerta_frame.setVisible(existente is not None)

    def _carregar_chamada(self):
        turma_id = self.turma_combo.currentData()
        if not turma_id:
            QMessageBox.warning(self, "Atenção", "Selecione uma turma.")
            return

        qd = self.data_edit.date()
        data_str = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"
        self._data_str = data_str
        self._turma_id = turma_id

        turma = db.get_turma(turma_id)
        alunos = db.alunos_da_turma(turma_id)
        self._alunos_rows = alunos

        if not alunos:
            QMessageBox.information(self, "Turma vazia",
                                    "Nenhum aluno matriculado nesta turma.\n"
                                    "Cadastre alunos pela aba 'Alunos' ou use 'Importar alunos para esta turma'.")
            self.tabela.setRowCount(0)
            return

        # Info turma
        self.info_turma_lbl.setText(f"📋  {turma['nome']}")
        data_fmt = datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        self.info_alunos_lbl.setText(f"Data: {data_fmt} • {len(alunos)} alunos")
        self.info_frame.setVisible(True)

        # Verifica se já existe chamada salva
        chamada_existente = db.get_chamada(turma_id, data_str)
        presencas_existentes: dict[int, dict] = {}
        if chamada_existente:
            for p in db.get_presencas(chamada_existente["id"]):
                presencas_existentes[p["aluno_id"]] = dict(p)
            self._chamada_id = chamada_existente["id"]
        else:
            self._chamada_id = None

        # Preenche tabela
        self.tabela.setRowCount(len(alunos))
        self._checkboxes: list[QCheckBox] = []
        self._obs_edits: list[QLineEdit] = []

        for row_i, a in enumerate(alunos):
            nome_item = QTableWidgetItem(a["nome"])
            nome_item.setData(Qt.UserRole, a["id"])
            if not db.aluno_cadastro_completo(a):
                nome_item.setForeground(QColor("#F59E0B"))
                nome_item.setToolTip("⚠️ Cadastro incompleto")
            self.tabela.setItem(row_i, 0, nome_item)

            # Checkbox presente
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setStyleSheet("""
                QCheckBox::indicator { width: 22px; height: 22px; border-radius: 4px;
                    border: 2px solid #3A4560; background: #1A1F2E; }
                QCheckBox::indicator:checked { background: #10B981; border-color: #10B981; }
                QCheckBox::indicator:hover { border-color: #6C63FF; }
            """)
            # Pré-preenche se já havia chamada
            if a["id"] in presencas_existentes:
                cb.setChecked(bool(presencas_existentes[a["id"]]["presente"]))
            else:
                cb.setChecked(True)  # default: presente

            cb.stateChanged.connect(self._atualizar_resumo)
            self._checkboxes.append(cb)
            cb_layout.addWidget(cb)
            self.tabela.setCellWidget(row_i, 1, cb_widget)

            # Campo observação
            obs_edit = QLineEdit()
            obs_edit.setStyleSheet("""
                QLineEdit {
                    background: #252B3D; border: 1px solid #2A3050;
                    border-radius: 4px; color: #E0E6F0; padding: 4px 8px; font-size: 12px;
                }
                QLineEdit:focus { border: 1px solid #6C63FF; }
            """)
            obs_edit.setPlaceholderText("Observação (opcional)")
            if a["id"] in presencas_existentes:
                obs_edit.setText(presencas_existentes[a["id"]]["observacao"] or "")
            self._obs_edits.append(obs_edit)
            self.tabela.setCellWidget(row_i, 2, obs_edit)
            self.tabela.setRowHeight(row_i, 42)

        self.btn_salvar.setEnabled(True)
        self.btn_todos_presentes.setEnabled(True)
        self.btn_todos_ausentes.setEnabled(True)
        self._atualizar_resumo()

    def _marcar_todos(self, presente: bool):
        for cb in self._checkboxes:
            cb.setChecked(presente)

    def _atualizar_resumo(self):
        total = len(self._checkboxes)
        presentes = sum(1 for cb in self._checkboxes if cb.isChecked())
        ausentes = total - presentes
        self.resumo_label.setText(
            f"✅ Presentes: {presentes}  |  ❌ Ausentes: {ausentes}  |  Total: {total}"
        )

    def _salvar_chamada(self):
        if not self._alunos_rows:
            return

        turma_id = self._turma_id
        data_str = self._data_str

        # Verifica duplicata
        existente = db.get_chamada(turma_id, data_str)
        if existente and self._chamada_id == existente["id"]:
            # é edição normal — confirma sobrescrita
            resp = QMessageBox.question(
                self, "Chamada já existe",
                "Esta chamada já foi salva. Deseja sobrescrever com os dados atuais?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
        elif existente and self._chamada_id is None:
            resp = QMessageBox.question(
                self, "Chamada já existe",
                "Já existe uma chamada para esta turma nesta data.\nDeseja sobrescrever?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return

        chamada_id = db.criar_ou_obter_chamada(turma_id, data_str)
        presencas = []
        for i, a in enumerate(self._alunos_rows):
            presencas.append({
                "aluno_id": a["id"],
                "presente": 1 if self._checkboxes[i].isChecked() else 0,
                "observacao": self._obs_edits[i].text().strip(),
            })
        db.salvar_presencas(chamada_id, presencas)
        self._chamada_id = chamada_id

        presentes = sum(1 for p in presencas if p["presente"])
        ausentes = len(presencas) - presentes
        QMessageBox.information(
            self, "Chamada salva! ✅",
            f"Chamada registrada com sucesso.\n\n"
            f"✅ Presentes: {presentes}\n❌ Ausentes: {ausentes}"
        )
        self.alerta_frame.setVisible(True)

    def _limpar(self):
        self.tabela.setRowCount(0)
        self._alunos_rows = []
        self._checkboxes = []
        self._obs_edits = []
        self._chamada_id = None
        self.info_frame.setVisible(False)
        self.alerta_frame.setVisible(False)
        self.btn_salvar.setEnabled(False)
        self.btn_todos_presentes.setEnabled(False)
        self.btn_todos_ausentes.setEnabled(False)
        self.resumo_label.setText("")

    def _importar_para_turma(self):
        turma_id = self.turma_combo.currentData()
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar alunos (.txt)", "", "Arquivo de texto (*.txt)"
        )
        if not caminho:
            return

        dlg = DialogImportarEstruturado(caminho, self, turma_pre_selecionada=turma_id)
        if dlg.exec():
            self._atualizar_turmas()
            if turma_id:
                idx = self.turma_combo.findData(turma_id)
                if idx >= 0:
                    self.turma_combo.setCurrentIndex(idx)
            self._carregar_chamada()

    def recarregar_tudo(self):
        sel_t = self.turma_combo.currentData()
        self._atualizar_turmas()
        if sel_t:
            idx = self.turma_combo.findData(sel_t)
            if idx >= 0:
                self.turma_combo.setCurrentIndex(idx)
        if hasattr(self, "_turma_id") and self._turma_id:
            self._carregar_chamada()

    def atualizar_turmas(self):
        """Chamado externamente quando há mudança na aba de Alunos."""
        self.recarregar_tudo()

    def abrir_chamada_para(self, turma_id: str, data_str: str):
        """Abre diretamente a chamada de uma turma específica e data indicada."""
        turma = db.get_turma(turma_id)
        if not turma:
            return

        # Ajusta o filtro de curso correspondente
        curso = turma["curso"]
        idx_c = self.curso_combo.findText(curso)
        if idx_c >= 0:
            self.curso_combo.setCurrentIndex(idx_c)
        else:
            self._atualizar_turmas()

        # Seleciona a turma no combo
        idx_t = self.turma_combo.findData(turma_id)
        if idx_t >= 0:
            self.turma_combo.setCurrentIndex(idx_t)

        # Ajusta a data
        qd = QDate.fromString(data_str, "yyyy-MM-dd")
        if qd.isValid():
            self.data_edit.setDate(qd)

        # Carrega a chamada
        self._carregar_chamada()

