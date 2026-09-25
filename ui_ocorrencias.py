"""
ui_ocorrencias.py — Aba de Ocorrências de Alunos.
Permite registrar, visualizar e excluir ocorrências disciplinares/observações
dos alunos, com busca por nome (autocomplete) e listagem cronológica.
"""

from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QCompleter, QDateEdit, QMessageBox, QGroupBox, QSizePolicy,
    QAbstractItemView, QScrollArea
)
from PySide6.QtCore import QStringListModel

import db
from icones import get_icon


# ---------------------------------------------------------------------------
# Diálogo / Formulário inline de nova ocorrência
# ---------------------------------------------------------------------------
class FormOcorrencia(QFrame):
    """Formulário embutido para adicionar uma nova ocorrência."""
    registrado = Signal()   # emitido quando uma ocorrência é salva
    cancelado = Signal()    # emitido quando o usuário cancela

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alunos: list[dict] = []
        self._aluno_selecionado: dict | None = None
        self._build_ui()
        self._carregar_alunos()

    def _build_ui(self):
        self.setStyleSheet("""
            FormOcorrencia {
                background: #1E2538;
                border: 1px solid #3A4560;
                border-radius: 12px;
            }
            QLabel { color: #B0BAD0; font-size: 13px; background: transparent; border: none; }
            QLabel#destaque { color: #6C63FF; font-weight: bold; font-size: 13px; }
            QLineEdit, QTextEdit, QDateEdit {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 8px 12px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
                border: 1px solid #6C63FF;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(14)

        # Título
        titulo = QLabel("Nova Ocorrência")
        titulo.setStyleSheet("color: #E0E6F0; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        outer.addWidget(titulo)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background: #3A4560; border: none; max-height: 1px; margin: 0;")
        outer.addWidget(div)

        # Linha 1: aluno + data
        linha1 = QHBoxLayout()
        linha1.setSpacing(16)

        # Busca de aluno (com autocomplete)
        campo_aluno = QVBoxLayout()
        campo_aluno.setSpacing(4)
        lbl_aluno = QLabel("Aluno *")
        campo_aluno.addWidget(lbl_aluno)

        self.busca_aluno = QLineEdit()
        self.busca_aluno.setPlaceholderText("Digite o nome do aluno...")
        self.busca_aluno.setMinimumWidth(280)
        campo_aluno.addWidget(self.busca_aluno)

        self._completer = QCompleter()
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.popup().setStyleSheet("""
            QAbstractItemView {
                background: #252B3D; color: #E0E6F0; border: 1px solid #3A4560;
                selection-background-color: #3D3580; font-size: 13px;
            }
        """)
        self.busca_aluno.setCompleter(self._completer)
        self.busca_aluno.textEdited.connect(self._ao_editar_busca)
        self._completer.activated.connect(self._ao_selecionar_aluno)

        linha1.addLayout(campo_aluno, 2)

        # Data
        campo_data = QVBoxLayout()
        campo_data.setSpacing(4)
        lbl_data = QLabel("Data da Ocorrência")
        campo_data.addWidget(lbl_data)
        self.data_edit = QDateEdit()
        self.data_edit.setDate(QDate.currentDate())
        self.data_edit.setDisplayFormat("dd/MM/yyyy")
        self.data_edit.setCalendarPopup(True)
        self.data_edit.setMinimumWidth(160)
        campo_data.addWidget(self.data_edit)
        linha1.addLayout(campo_data, 1)

        outer.addLayout(linha1)

        # Info do aluno selecionado
        self.info_aluno_lbl = QLabel("")
        self.info_aluno_lbl.setObjectName("destaque")
        self.info_aluno_lbl.setVisible(False)
        outer.addWidget(self.info_aluno_lbl)

        # Descrição
        campo_desc = QVBoxLayout()
        campo_desc.setSpacing(4)
        lbl_desc = QLabel("Descrição da Ocorrência *")
        campo_desc.addWidget(lbl_desc)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Descreva a ocorrência com detalhes...")
        self.desc_edit.setMinimumHeight(100)
        self.desc_edit.setMaximumHeight(150)
        campo_desc.addWidget(self.desc_edit)
        outer.addLayout(campo_desc)

        # Botões
        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setIcon(get_icon("excluir"))
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background: #2A3050; color: #9AA3C0; border: 1px solid #3A4560;
                border-radius: 8px; padding: 9px 22px; font-size: 13px;
            }
            QPushButton:hover { background: #3A4560; color: #E0E6F0; }
        """)
        btn_cancelar.clicked.connect(self._cancelar)

        btn_registrar = QPushButton("Registrar Ocorrência")
        btn_registrar.setIcon(get_icon("novo"))
        btn_registrar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
                color: white; border-radius: 8px; padding: 9px 22px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #7C75FF; }
        """)
        btn_registrar.clicked.connect(self._registrar)

        btns.addWidget(btn_cancelar)
        btns.addWidget(btn_registrar)
        outer.addLayout(btns)

    def _carregar_alunos(self):
        self._alunos = db.listar_nomes_alunos()
        nomes = [a["nome"] for a in self._alunos]
        model = QStringListModel(nomes)
        self._completer.setModel(model)

    def _ao_editar_busca(self, texto: str):
        """Quando o usuário edita o campo, reseta aluno selecionado."""
        self._aluno_selecionado = None
        self.info_aluno_lbl.setVisible(False)

    def _ao_selecionar_aluno(self, nome: str):
        """Quando um nome é selecionado no autocomplete."""
        for a in self._alunos:
            if a["nome"].lower() == nome.lower():
                self._aluno_selecionado = a
                self.info_aluno_lbl.setText(
                    f"  Curso: {a['curso']}  |  Turmas: {a['turmas']}"
                )
                self.info_aluno_lbl.setVisible(True)
                self.busca_aluno.setText(nome)
                break

    def _registrar(self):
        nome_digitado = self.busca_aluno.text().strip()
        descricao = self.desc_edit.toPlainText().strip()

        # Verifica se o aluno está selecionado (ou tenta buscar pelo nome digitado)
        if self._aluno_selecionado is None:
            for a in self._alunos:
                if a["nome"].lower() == nome_digitado.lower():
                    self._aluno_selecionado = a
                    break

        if not self._aluno_selecionado:
            QMessageBox.warning(
                self, "Atenção",
                "Selecione um aluno válido da lista de sugestões.\n"
                "Use o autocomplete para encontrar o aluno."
            )
            self.busca_aluno.setFocus()
            return

        if not descricao:
            QMessageBox.warning(self, "Atenção", "A descrição da ocorrência é obrigatória.")
            self.desc_edit.setFocus()
            return

        qd = self.data_edit.date()
        data_str = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

        db.criar_ocorrencia(self._aluno_selecionado["id"], descricao, data_str)
        self.registrado.emit()
        self._limpar()

    def _cancelar(self):
        self._limpar()
        self.cancelado.emit()

    def _limpar(self):
        self.busca_aluno.clear()
        self.desc_edit.clear()
        self.data_edit.setDate(QDate.currentDate())
        self._aluno_selecionado = None
        self.info_aluno_lbl.setVisible(False)

    def recarregar_alunos(self):
        self._carregar_alunos()


# ---------------------------------------------------------------------------
# Aba Principal — Ocorrências
# ---------------------------------------------------------------------------
class AbaOcorrencias(QWidget):
    def __init__(self):
        super().__init__()
        self._form_visivel = False
        self._build_ui()
        self.atualizar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Toolbar superior
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Busca
        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText("🔍  Buscar por nome do aluno ou descrição...")
        self.busca_edit.setStyleSheet("""
            QLineEdit {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 8px 12px; font-size: 13px; min-width: 280px;
            }
            QLineEdit:focus { border: 1px solid #6C63FF; }
        """)
        self.busca_edit.textChanged.connect(self.atualizar)
        toolbar.addWidget(self.busca_edit)

        toolbar.addStretch()

        # Botão Atualizar
        btn_att = QPushButton("Atualizar")
        btn_att.setIcon(get_icon("atualizar"))
        btn_att.setStyleSheet(self._btn_secondary())
        btn_att.clicked.connect(self.atualizar)
        toolbar.addWidget(btn_att)

        # Botão Adicionar Ocorrência
        self.btn_nova = QPushButton("Adicionar Ocorrência")
        self.btn_nova.setIcon(get_icon("novo"))
        self.btn_nova.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
                color: white; border-radius: 8px; padding: 9px 18px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #7C75FF; }
        """)
        self.btn_nova.clicked.connect(self._toggle_form)
        toolbar.addWidget(self.btn_nova)

        layout.addLayout(toolbar)

        # Formulário de nova ocorrência (oculto por padrão)
        self.form = FormOcorrencia()
        self.form.setVisible(False)
        self.form.registrado.connect(self._apos_registrar)
        self.form.cancelado.connect(self._fechar_form)
        layout.addWidget(self.form)

        # Área com a tabela
        grp = QGroupBox("Ocorrências Registradas")
        grp.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3A4560; border-radius: 10px;
                margin-top: 8px; color: #9AA3C0; font-size: 13px; font-weight: bold;
                background: #1A1F2E; padding: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; }
        """)
        grp_lay = QVBoxLayout(grp)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Data", "Aluno", "Curso / Turmas", "Descrição", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabela.setColumnWidth(0, 100)
        self.tabela.setColumnWidth(4, 80)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setWordWrap(True)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background: #1A1F2E; border: 1px solid #2A3050;
                border-radius: 8px; color: #E0E6F0;
                gridline-color: #2A3050; font-size: 12px;
            }
            QTableWidget::item { padding: 6px 8px; }
            QTableWidget::item:selected { background: #3D3580; }
            QTableWidget::item:alternate { background: #1E2535; }
            QHeaderView::section {
                background: #252B3D; color: #9AA3C0; padding: 8px;
                border: none; font-size: 12px; font-weight: bold;
            }
        """)
        grp_lay.addWidget(self.tabela)

        self.contador_lbl = QLabel("")
        self.contador_lbl.setStyleSheet("color: #6C63FF; font-size: 12px; background: transparent; border: none;")
        grp_lay.addWidget(self.contador_lbl)

        layout.addWidget(grp, stretch=1)

    def _toggle_form(self):
        self._form_visivel = not self._form_visivel
        self.form.setVisible(self._form_visivel)
        if self._form_visivel:
            self.form.recarregar_alunos()
            self.btn_nova.setText("Fechar Formulário")
            self.form.busca_aluno.setFocus()
        else:
            self.btn_nova.setText("Adicionar Ocorrência")

    def _fechar_form(self):
        self._form_visivel = False
        self.form.setVisible(False)
        self.btn_nova.setText("Adicionar Ocorrência")

    def _apos_registrar(self):
        self.atualizar()
        self._fechar_form()

    def atualizar(self):
        busca = self.busca_edit.text().strip()
        ocorrencias = db.listar_ocorrencias(busca=busca)

        self.tabela.setRowCount(len(ocorrencias))
        for row_i, occ in enumerate(ocorrencias):
            # Data
            try:
                dt = datetime.strptime(occ["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                dt = occ["data"]
            item_data = QTableWidgetItem(dt)
            item_data.setForeground(QColor("#9AA3C0"))
            self.tabela.setItem(row_i, 0, item_data)

            # Nome do aluno
            item_nome = QTableWidgetItem(occ["aluno_nome"])
            item_nome.setForeground(QColor("#E0E6F0"))
            self.tabela.setItem(row_i, 1, item_nome)

            # Curso / Turmas
            curso_turmas = f"{occ['curso']}\n{occ['turmas']}"
            item_ct = QTableWidgetItem(curso_turmas)
            item_ct.setForeground(QColor("#9AA3C0"))
            self.tabela.setItem(row_i, 2, item_ct)

            # Descrição
            item_desc = QTableWidgetItem(occ["descricao"])
            item_desc.setForeground(QColor("#E0E6F0"))
            self.tabela.setItem(row_i, 3, item_desc)

            # Botão excluir
            btn_del = QPushButton()
            btn_del.setIcon(get_icon("excluir"))
            btn_del.setToolTip("Excluir esta ocorrência")
            btn_del.setFixedSize(34, 34)
            btn_del.setStyleSheet("""
                QPushButton {
                    background: #3B1F1F; border-radius: 6px; padding: 4px;
                    border: 1px solid #7F1D1D;
                }
                QPushButton:hover { background: #7F1D1D; }
            """)
            oc_id = occ["id"]
            nome_aluno = occ["aluno_nome"]
            btn_del.clicked.connect(
                lambda _, oid=oc_id, n=nome_aluno: self._excluir_ocorrencia(oid, n)
            )

            btn_widget = QWidget()
            btn_lay = QHBoxLayout(btn_widget)
            btn_lay.setContentsMargins(4, 2, 4, 2)
            btn_lay.addWidget(btn_del)
            btn_lay.addStretch()
            self.tabela.setCellWidget(row_i, 4, btn_widget)
            self.tabela.setRowHeight(row_i, 48)

        self.contador_lbl.setText(f"{len(ocorrencias)} ocorrência(s) registrada(s)")

        if not ocorrencias:
            self.tabela.setRowCount(1)
            vazio = QTableWidgetItem(
                "Nenhuma ocorrência registrada."
                if not busca else
                f"Nenhuma ocorrência encontrada para '{busca}'."
            )
            vazio.setForeground(QColor("#6A7490"))
            vazio.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(0, 0, vazio)
            self.tabela.setSpan(0, 0, 1, 5)

    def _excluir_ocorrencia(self, oc_id: int, nome_aluno: str):
        resp = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Excluir a ocorrência do aluno '{nome_aluno}'?\nEssa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            db.excluir_ocorrencia(oc_id)
            self.atualizar()

    def recarregar_tudo(self):
        self.form.recarregar_alunos()
        self.atualizar()

    def _btn_secondary(self):
        return """QPushButton {
            background: #2A3050; color: #9AA3C0; border-radius: 8px;
            padding: 8px 14px; font-size: 12px; border: 1px solid #3A4560;
        }
        QPushButton:hover { background: #3A4560; color: #E0E6F0; }"""
