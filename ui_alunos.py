"""
ui_alunos.py — Aba de Gerenciamento de Alunos.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDate, Signal, QSortFilterProxyModel
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QTextEdit, QDateEdit,
    QListWidget, QListWidgetItem, QCheckBox, QMessageBox, QFileDialog,
    QGroupBox, QScrollArea, QFrame, QSplitter, QAbstractItemView,
    QTabWidget, QGridLayout
)

import db
from icones import get_icon
from ui_importar import DialogImportarEstruturado

CURSO_OPCOES = ["Informática", "Robótica", "Ambos"]
GENERO_OPCOES = ["", "Masculino", "Feminino"]
ALERT_COLOR = QColor("#F59E0B")
ALERT_BG = QColor("#FFF8E7")


def calcular_idade(data_nasc_str: str) -> str:
    if not data_nasc_str:
        return "—"
    try:
        d = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
        hoje = date.today()
        anos = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
        return str(anos)
    except Exception:
        return "—"


# ---------------------------------------------------------------------------
# Diálogo de Cadastro / Edição de Aluno
# ---------------------------------------------------------------------------
class DialogAluno(QDialog):
    def __init__(self, parent=None, aluno_id: int | None = None):
        super().__init__(parent)
        self.aluno_id = aluno_id
        self.setWindowTitle("Novo Aluno" if aluno_id is None else "Editar Aluno")
        self.setMinimumWidth(520)
        self.setStyleSheet("""
            QDialog { background: #1E2233; color: #E0E6F0; }
            QLabel { color: #B0BAD0; font-size: 13px; }
            QLineEdit, QTextEdit, QDateEdit {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 6px;
                color: #E0E6F0; padding: 6px 10px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
                border: 1px solid #6C63FF;
            }
            QComboBox {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 6px;
                color: #E0E6F0; padding: 5px 10px; font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #252B3D; color: #E0E6F0; }
            QPushButton {
                background: #6C63FF; color: white; border-radius: 8px;
                padding: 8px 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #8B85FF; }
            QPushButton[flat="true"] {
                background: #2A3050; color: #9AA3C0;
            }
            QPushButton[flat="true"]:hover { background: #3A4560; color: #E0E6F0; }
            QGroupBox {
                border: 1px solid #3A4560; border-radius: 8px;
                margin-top: 8px; color: #9AA3C0; font-size: 12px; padding: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QListWidget {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 6px;
                color: #E0E6F0; font-size: 12px;
            }
        """)
        self._build_ui()
        if aluno_id:
            self._carregar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo do aluno")
        form.addRow("Nome *", self.nome_edit)

        # nascimento + idade
        nasc_layout = QHBoxLayout()
        self.nasc_edit = QDateEdit()
        self.nasc_edit.setDisplayFormat("dd/MM/yyyy")
        self.nasc_edit.setCalendarPopup(True)
        self.nasc_edit.setDate(QDate(2010, 1, 1))
        self.nasc_edit.setSpecialValueText("Não informado")
        self.idade_label = QLabel("Idade: —")
        self.idade_label.setStyleSheet("color: #6C63FF; font-weight: bold; font-size: 13px;")
        self._nasc_preenchido = False
        nasc_layout.addWidget(self.nasc_edit)
        nasc_layout.addWidget(self.idade_label)
        self.nasc_edit.dateChanged.connect(self._atualizar_idade)

        # Checkbox "não informar nascimento"
        self.sem_nasc_check = QCheckBox("Não informado")
        self.sem_nasc_check.setStyleSheet("color: #9AA3C0; font-size: 12px;")
        self.sem_nasc_check.stateChanged.connect(self._toggle_nasc)
        nasc_layout.addWidget(self.sem_nasc_check)
        form.addRow("Nascimento", nasc_layout)

        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["Não informado", "Masculino", "Feminino"])
        form.addRow("Gênero", self.genero_combo)

        self.curso_combo = QComboBox()
        self.curso_combo.addItems(CURSO_OPCOES)
        self.curso_combo.currentTextChanged.connect(self._atualizar_turmas)
        form.addRow("Curso *", self.curso_combo)

        layout.addLayout(form)

        # Turmas
        grp_turmas = QGroupBox("Turmas")
        grp_layout = QVBoxLayout(grp_turmas)
        grp_layout.setSpacing(4)
        self.turmas_list = QListWidget()
        self.turmas_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.turmas_list.setMaximumHeight(160)
        grp_layout.addWidget(self.turmas_list)
        layout.addWidget(grp_turmas)

        # Observação
        obs_label = QLabel("Observação")
        obs_label.setStyleSheet("color: #B0BAD0; font-size: 13px;")
        self.obs_edit = QTextEdit()
        self.obs_edit.setMaximumHeight(70)
        self.obs_edit.setPlaceholderText("Observações sobre o aluno...")
        layout.addWidget(obs_label)
        layout.addWidget(self.obs_edit)

        # Botões
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText("Salvar")
        btns.button(QDialogButtonBox.Cancel).setText("Cancelar")
        btns.button(QDialogButtonBox.Save).clicked.connect(self._salvar)
        btns.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        layout.addWidget(btns)

        self._atualizar_turmas()

    def _toggle_nasc(self, state):
        self.nasc_edit.setEnabled(state == 0)
        if state != 0:
            self.idade_label.setText("Idade: —")
            self._nasc_preenchido = False

    def _atualizar_idade(self, qdate: QDate):
        self._nasc_preenchido = True
        d = date(qdate.year(), qdate.month(), qdate.day())
        hoje = date.today()
        anos = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
        self.idade_label.setText(f"Idade: {anos} anos")

    def _atualizar_turmas(self):
        curso = self.curso_combo.currentText()
        self.turmas_list.clear()

        # guarda quais já estavam selecionadas
        turmas = db.listar_turmas()
        for t in turmas:
            if curso == "Ambos" or t["curso"] == curso:
                item = QListWidgetItem(t["nome"])
                item.setData(Qt.UserRole, t["id"])
                item.setCheckState(Qt.Unchecked)
                self.turmas_list.addItem(item)

    def _carregar(self):
        aluno = db.get_aluno(self.aluno_id)
        if not aluno:
            return
        self.nome_edit.setText(aluno["nome"])
        if aluno["data_nascimento"]:
            d = datetime.strptime(aluno["data_nascimento"], "%Y-%m-%d")
            self.nasc_edit.setDate(QDate(d.year, d.month, d.day))
            self._nasc_preenchido = True
            self._atualizar_idade(self.nasc_edit.date())
        else:
            self.sem_nasc_check.setChecked(True)

        idx_g = self.genero_combo.findText(aluno["genero"] or "Não informado")
        if idx_g >= 0:
            self.genero_combo.setCurrentIndex(idx_g)

        idx_c = self.curso_combo.findText(aluno["curso"])
        if idx_c >= 0:
            self.curso_combo.setCurrentIndex(idx_c)
        self._atualizar_turmas()

        turmas_do_aluno = {t["id"] for t in db.turmas_do_aluno(self.aluno_id)}
        for i in range(self.turmas_list.count()):
            item = self.turmas_list.item(i)
            if item.data(Qt.UserRole) in turmas_do_aluno:
                item.setCheckState(Qt.Checked)

        self.obs_edit.setPlainText(aluno["observacao"] or "")

    def _salvar(self):
        nome = self.nome_edit.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "O nome é obrigatório.")
            return

        nasc_str = ""
        if not self.sem_nasc_check.isChecked() and self._nasc_preenchido:
            qd = self.nasc_edit.date()
            nasc_str = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"

        genero = self.genero_combo.currentText()
        if genero == "Não informado":
            genero = ""
        curso = self.curso_combo.currentText()
        obs = self.obs_edit.toPlainText()

        turma_ids = []
        for i in range(self.turmas_list.count()):
            item = self.turmas_list.item(i)
            if item.checkState() == Qt.Checked:
                turma_ids.append(item.data(Qt.UserRole))

        if self.aluno_id is None:
            aid = db.criar_aluno(nome, nasc_str, genero, curso, obs)
            db.set_turmas_aluno(aid, turma_ids)
        else:
            db.atualizar_aluno(self.aluno_id, nome, nasc_str, genero, curso, obs)
            db.set_turmas_aluno(self.aluno_id, turma_ids)

        self.accept()


# ---------------------------------------------------------------------------
# Ficha Individual do Aluno
# ---------------------------------------------------------------------------
class FichaAluno(QDialog):
    def __init__(self, aluno_id: int, parent=None):
        super().__init__(parent)
        self.aluno_id = aluno_id
        self.setWindowTitle("Ficha do Aluno")
        self.setMinimumSize(720, 560)
        self.setStyleSheet("""
            QDialog { background: #1E2233; color: #E0E6F0; }
            QLabel { color: #B0BAD0; }
            QTabWidget::pane { border: 1px solid #3A4560; border-radius: 6px; }
            QTabBar::tab {
                background: #252B3D; color: #9AA3C0; padding: 8px 18px;
                border-radius: 4px 4px 0 0; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #6C63FF; color: white; }
            QTableWidget {
                background: #1A1F2E; border: none; color: #E0E6F0;
                gridline-color: #2A3050; font-size: 12px;
            }
            QTableWidget::item:alternate { background: #252B3D; }
            QHeaderView::section {
                background: #252B3D; color: #9AA3C0; padding: 8px;
                border: none; font-size: 12px; font-weight: bold;
            }
            QGroupBox {
                border: 1px solid #3A4560; border-radius: 8px;
                margin-top: 8px; color: #9AA3C0; padding: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
        """)
        self._build_ui()

    def _build_ui(self):
        aluno = db.get_aluno(self.aluno_id)
        if not aluno:
            return

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Cabeçalho
        header = QFrame()
        header.setStyleSheet("background: #252B3D; border-radius: 10px; padding: 4px;")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(16, 12, 16, 12)

        nome_lbl = QLabel(aluno["nome"])
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        nome_lbl.setFont(font)
        nome_lbl.setStyleSheet("color: #E0E6F0;")

        completo = db.aluno_cadastro_completo(aluno)
        status_lbl = QLabel("Cadastro completo" if completo else "Cadastro pendente")
        status_lbl.setStyleSheet(
            "color: #4ADE80; font-size: 12px; font-weight: bold;" if completo else "color: #F59E0B; font-size: 12px; font-weight: bold;"
        )

        hlay.addWidget(nome_lbl)
        hlay.addStretch()
        hlay.addWidget(status_lbl)
        layout.addWidget(header)

        # Dados
        grp_dados = QGroupBox("Dados Cadastrais")
        gdl = QGridLayout(grp_dados)
        gdl.setSpacing(8)

        idade = calcular_idade(aluno["data_nascimento"] or "")
        nasc = ""
        if aluno["data_nascimento"]:
            try:
                d = datetime.strptime(aluno["data_nascimento"], "%Y-%m-%d")
                nasc = d.strftime("%d/%m/%Y")
            except Exception:
                nasc = aluno["data_nascimento"]

        campos = [
            ("Nascimento:", nasc or "Não informado"),
            ("Idade:", f"{idade} anos" if idade != "—" else "—"),
            ("Gênero:", aluno["genero"] or "Não informado"),
            ("Curso:", aluno["curso"]),
        ]
        for i, (label, valor) in enumerate(campos):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #9AA3C0; font-size: 12px;")
            val = QLabel(valor)
            val.setStyleSheet("color: #E0E6F0; font-size: 13px; font-weight: bold;")
            gdl.addWidget(lbl, i // 2, (i % 2) * 2)
            gdl.addWidget(val, i // 2, (i % 2) * 2 + 1)

        turmas = db.turmas_do_aluno(self.aluno_id)
        turmas_str = "\n".join(t["nome"] for t in turmas) if turmas else "Nenhuma"
        t_lbl = QLabel("Turmas:")
        t_lbl.setStyleSheet("color: #9AA3C0; font-size: 12px;")
        t_val = QLabel(turmas_str)
        t_val.setStyleSheet("color: #E0E6F0; font-size: 12px;")
        t_val.setWordWrap(True)
        gdl.addWidget(t_lbl, 2, 0)
        gdl.addWidget(t_val, 2, 1, 1, 3)

        obs = aluno["observacao"] or ""
        if obs:
            o_lbl = QLabel("Observação:")
            o_lbl.setStyleSheet("color: #9AA3C0; font-size: 12px;")
            o_val = QLabel(obs)
            o_val.setWordWrap(True)
            o_val.setStyleSheet("color: #E0E6F0; font-size: 12px;")
            gdl.addWidget(o_lbl, 3, 0)
            gdl.addWidget(o_val, 3, 1, 1, 3)

        layout.addWidget(grp_dados)

        # Tabs de histórico
        tabs = QTabWidget()

        # Frequência por curso
        for curso in ("Informática", "Robótica"):
            if aluno["curso"] not in (curso, "Ambos"):
                continue
            tab = QWidget()
            tl = QVBoxLayout(tab)

            # Frequência geral
            hist = db.historico_aluno(self.aluno_id)
            hist_curso = [h for h in hist if True]  # todos

            # Tabela histórico
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Data", "Turma", "Status", "Observação"])
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.verticalHeader().setVisible(False)

            h_filtrado = db.historico_aluno(self.aluno_id)
            h_filtrado = [r for r in h_filtrado if
                          db.get_turma(r["turma_id"]) and
                          db.get_turma(r["turma_id"])["curso"] == curso]

            table.setRowCount(len(h_filtrado))
            presentes_t = 0
            for row_i, r in enumerate(h_filtrado):
                try:
                    dt = datetime.strptime(r["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception:
                    dt = r["data"]
                table.setItem(row_i, 0, QTableWidgetItem(dt))
                table.setItem(row_i, 1, QTableWidgetItem(r["turma_nome"]))
                presente = r["presente"]
                status_item = QTableWidgetItem("Presente" if presente else "Ausente")
                status_item.setForeground(QColor("#4ADE80") if presente else QColor("#F87171"))
                table.setItem(row_i, 2, status_item)
                table.setItem(row_i, 3, QTableWidgetItem(r["observacao"] or ""))
                if presente:
                    presentes_t += 1

            total_t = len(h_filtrado)
            pct = round(presentes_t / total_t * 100, 1) if total_t > 0 else 0
            resumo = QLabel(
                f"Total de aulas: {total_t} | Presenças: {presentes_t} | Frequência: {pct}%"
            )
            resumo.setStyleSheet("color: #6C63FF; font-size: 13px; font-weight: bold; padding: 6px 0;")
            tl.addWidget(resumo)
            tl.addWidget(table)
            tabs.addTab(tab, f"📊 {curso}")

        layout.addWidget(tabs)

        # Fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        btn_fechar.setStyleSheet("background: #2A3050; color: #9AA3C0;")
        layout.addWidget(btn_fechar, alignment=Qt.AlignRight)


# ---------------------------------------------------------------------------
# Aba Principal — Alunos
# ---------------------------------------------------------------------------
class AbaAlunos(QWidget):
    aluno_alterado = Signal()

    def __init__(self):
        super().__init__()
        self._sort_col = 1      # coluna padrão: Nome
        self._sort_asc = True   # ordem padrão: crescente
        self._alunos_cache: list = []
        self._build_ui()
        self.atualizar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Barra de ferramentas
        toolbar = QHBoxLayout()

        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText("🔍  Buscar por nome...")
        self.busca_edit.setStyleSheet("""
            QLineEdit {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 8px 12px; font-size: 13px; min-width: 220px;
            }
            QLineEdit:focus { border: 1px solid #6C63FF; }
        """)
        self.busca_edit.textChanged.connect(self.atualizar)
        toolbar.addWidget(self.busca_edit)

        self.filtro_curso = QComboBox()
        self.filtro_curso.addItems(["Todos", "Informática", "Robótica", "Ambos"])
        self.filtro_curso.setStyleSheet(self._combo_style())
        self.filtro_curso.currentTextChanged.connect(self.atualizar)
        toolbar.addWidget(self.filtro_curso)

        self.filtro_turma = QComboBox()
        self.filtro_turma.addItem("Todas as turmas", "")
        for t in db.listar_turmas():
            self.filtro_turma.addItem(t["nome"], t["id"])
        self.filtro_turma.setStyleSheet(self._combo_style())
        self.filtro_turma.setMaximumWidth(280)
        self.filtro_turma.currentIndexChanged.connect(self.atualizar)
        toolbar.addWidget(self.filtro_turma)

        self.pendentes_check = QCheckBox("Só pendentes")
        self.pendentes_check.setStyleSheet("color: #F59E0B; font-size: 12px;")
        self.pendentes_check.stateChanged.connect(self.atualizar)
        toolbar.addWidget(self.pendentes_check)

        toolbar.addStretch()

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setIcon(get_icon("atualizar"))
        btn_atualizar.setToolTip("Atualizar lista de alunos e turmas (F5)")
        btn_atualizar.clicked.connect(self.recarregar_tudo)
        btn_atualizar.setStyleSheet(self._btn_secondary())
        toolbar.addWidget(btn_atualizar)

        btn_novo = QPushButton("Novo Aluno")
        btn_novo.setIcon(get_icon("novo"))
        btn_novo.clicked.connect(self._novo_aluno)
        btn_novo.setStyleSheet(self._btn_primary())
        toolbar.addWidget(btn_novo)

        btn_exp = QPushButton("Exportar .txt")
        btn_exp.setIcon(get_icon("exportar"))
        btn_exp.clicked.connect(self._exportar)
        btn_exp.setStyleSheet(self._btn_secondary())
        toolbar.addWidget(btn_exp)

        btn_imp = QPushButton("Importar .txt")
        btn_imp.setIcon(get_icon("importar"))
        btn_imp.clicked.connect(self._importar_geral)
        btn_imp.setStyleSheet(self._btn_secondary())
        toolbar.addWidget(btn_imp)

        layout.addLayout(toolbar)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels(["", "Nome ↕", "Idade ↕", "Gênero ↕", "Curso ↕", "Turmas ↕", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setColumnWidth(0, 32)
        self.tabela.setColumnWidth(2, 60)
        self.tabela.setColumnWidth(3, 90)
        self.tabela.setColumnWidth(4, 100)
        self.tabela.setColumnWidth(6, 160)
        self.tabela.setStyleSheet(self._table_style())
        self.tabela.doubleClicked.connect(self._abrir_ficha)
        self.tabela.horizontalHeader().sectionClicked.connect(self._ao_clicar_cabecalho)
        self.tabela.horizontalHeader().setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.tabela)

        # Rodapé contador
        self.contador_label = QLabel("")
        self.contador_label.setStyleSheet("color: #6C63FF; font-size: 12px;")
        layout.addWidget(self.contador_label)

    def _ao_clicar_cabecalho(self, col: int):
        """Alterna ordenação ao clicar em um cabeçalho de coluna."""
        if col in (0, 6):  # colunas sem ordenação
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._renderizar_tabela()

    def _chave_sort(self, aluno) -> tuple:
        """Retorna a chave de ordenação para um aluno baseado na coluna selecionada."""
        col = self._sort_col
        if col == 1:  # Nome
            return (aluno["nome"].lower(),)
        elif col == 2:  # Idade (nascimento)
            nasc = aluno["data_nascimento"] or ""
            return (nasc if nasc else "9999",)  # sem data vai para o final
        elif col == 3:  # Gênero
            return ((aluno["genero"] or "").lower(),)
        elif col == 4:  # Curso
            return (aluno["curso"].lower(),)
        elif col == 5:  # Turmas
            turmas = db.turmas_do_aluno(aluno["id"])
            s = "; ".join(t["nome"] for t in turmas)
            return (s.lower(),)
        return (aluno["nome"].lower(),)

    def atualizar(self):
        busca = self.busca_edit.text()
        curso = self.filtro_curso.currentText()
        turma_id = self.filtro_turma.currentData() or ""
        apenas_pendentes = self.pendentes_check.isChecked()

        alunos = db.listar_alunos(busca, curso, turma_id, apenas_pendentes)
        self._alunos_cache = list(alunos)
        self._renderizar_tabela()

    def _renderizar_tabela(self):
        alunos = sorted(self._alunos_cache, key=self._chave_sort, reverse=not self._sort_asc)

        # Atualiza cabeçalhos para mostrar a coluna/direção atual
        cabecalhos = ["", "Nome", "Idade", "Gênero", "Curso", "Turmas", "Ações"]
        for ci, nome in enumerate(cabecalhos):
            if ci in (0, 6):
                self.tabela.horizontalHeaderItem(ci).setText(nome)
            elif ci == self._sort_col:
                seta = " ▲" if self._sort_asc else " ▼"
                self.tabela.horizontalHeaderItem(ci).setText(nome + seta)
            else:
                self.tabela.horizontalHeaderItem(ci).setText(nome + " ↕")

        self.tabela.setRowCount(len(alunos))

        for row_i, a in enumerate(alunos):
            completo = db.aluno_cadastro_completo(a)
            alert_item = QTableWidgetItem()
            if not completo:
                alert_item.setIcon(get_icon("alerta"))
                alert_item.setToolTip("Cadastro incompleto (falta nascimento ou gênero)")
            alert_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(row_i, 0, alert_item)

            nome_item = QTableWidgetItem(a["nome"])
            if not completo:
                nome_item.setForeground(QColor("#F59E0B"))
            self.tabela.setItem(row_i, 1, nome_item)

            self.tabela.setItem(row_i, 2, QTableWidgetItem(calcular_idade(a["data_nascimento"] or "")))
            self.tabela.setItem(row_i, 3, QTableWidgetItem(a["genero"] or "—"))
            self.tabela.setItem(row_i, 4, QTableWidgetItem(a["curso"]))

            turmas = db.turmas_do_aluno(a["id"])
            turmas_str = "; ".join(t["nome"].split("—")[1].strip() if "—" in t["nome"] else t["nome"]
                                   for t in turmas) if turmas else "Sem turma"
            self.tabela.setItem(row_i, 5, QTableWidgetItem(turmas_str))

            # Widget de ações com ícones vetoriais
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            btn_ver = QPushButton()
            btn_ver.setIcon(get_icon("ficha"))
            btn_ver.setToolTip("Ver ficha do aluno")
            btn_ver.setFixedSize(28, 28)
            btn_ver.setStyleSheet("background: #2A3050; border-radius: 6px; padding: 4px;")
            btn_ver.clicked.connect(lambda _, aid=a["id"]: self._abrir_ficha_id(aid))

            btn_edit = QPushButton()
            btn_edit.setIcon(get_icon("editar"))
            btn_edit.setToolTip("Editar dados do aluno")
            btn_edit.setFixedSize(28, 28)
            btn_edit.setStyleSheet("background: #2A3050; border-radius: 6px; padding: 4px;")
            btn_edit.clicked.connect(lambda _, aid=a["id"]: self._editar_aluno(aid))

            btn_del = QPushButton()
            btn_del.setIcon(get_icon("excluir"))
            btn_del.setToolTip("Excluir aluno")
            btn_del.setFixedSize(28, 28)
            btn_del.setStyleSheet("background: #2A3050; border-radius: 6px; padding: 4px;")
            btn_del.clicked.connect(lambda _, aid=a["id"], n=a["nome"]: self._excluir_aluno(aid, n))

            btn_layout.addWidget(btn_ver)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_del)
            btn_layout.addStretch()
            self.tabela.setCellWidget(row_i, 6, btn_widget)
            self.tabela.setRowHeight(row_i, 40)

        total_pendentes = sum(1 for a in alunos if not db.aluno_cadastro_completo(a))
        self.contador_label.setText(
            f"{len(alunos)} aluno(s) encontrado(s)"
            + (f" — {total_pendentes} com cadastro pendente" if total_pendentes else "")
        )

    def _novo_aluno(self):
        dlg = DialogAluno(self)
        if dlg.exec():
            self.atualizar()
            self.aluno_alterado.emit()

    def _editar_aluno(self, aid: int):
        dlg = DialogAluno(self, aluno_id=aid)
        if dlg.exec():
            self.atualizar()
            self.aluno_alterado.emit()

    def _excluir_aluno(self, aid: int, nome: str):
        resp = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Excluir o aluno '{nome}' e todo o seu histórico?\nEssa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            db.fazer_backup("antes_exclusao")
            db.excluir_aluno(aid)
            self.atualizar()
            self.aluno_alterado.emit()

    def _abrir_ficha(self, index):
        aid = None
        nome = self.tabela.item(index.row(), 1)
        if nome:
            alunos = db.listar_alunos(nome.text())
            if alunos:
                aid = alunos[0]["id"]
        if aid:
            self._abrir_ficha_id(aid)

    def _abrir_ficha_id(self, aid: int):
        dlg = FichaAluno(aid, self)
        dlg.exec()

    def _exportar(self):
        turma_id = self.filtro_turma.currentData()
        turma_nome = self.filtro_turma.currentText()

        exportar_apenas_selecionada = False
        if turma_id:
            box = QMessageBox(self)
            box.setWindowTitle("Exportar Alunos")
            box.setText(f"Você está com um filtro ativo para a turma:\n\n<b>{turma_nome}</b>\n\nComo deseja realizar a exportação?")
            btn_turma = box.addButton("Apenas esta Turma", QMessageBox.ButtonRole.AcceptRole)
            btn_todas = box.addButton("Todas as Turmas", QMessageBox.ButtonRole.ActionRole)
            btn_cancelar = box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_turma)
            box.exec()

            clicado = box.clickedButton()
            if clicado == btn_cancelar:
                return
            elif clicado == btn_turma:
                exportar_apenas_selecionada = True

        filtro_param = turma_id if exportar_apenas_selecionada else None
        nome_sugerido = f"alunos_{turma_id.lower().replace('-', '_')}.txt" if exportar_apenas_selecionada else "alunos_turmas.txt"

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar Alunos (.txt)", nome_sugerido, "Arquivo de texto (*.txt)"
        )
        if not caminho:
            return

        try:
            res = db.exportar_alunos_txt(caminho, turma_id=filtro_param)
            msg = (
                f"Alunos exportados com sucesso no formato estruturado!\n\n"
                f"• Turmas processadas: {res['total_turmas']}\n"
                f"• Total de registros: {res['total_alunos']}\n\n"
                f"Arquivo salvo em:\n{caminho}"
            )
            QMessageBox.information(self, "Exportação Concluída", msg)
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Ocorreu um erro ao exportar:\n{e}")


    def recarregar_turmas_filtro(self):
        atual = self.filtro_turma.currentData()
        self.filtro_turma.blockSignals(True)
        self.filtro_turma.clear()
        self.filtro_turma.addItem("Todas as turmas", "")
        for t in db.listar_turmas():
            self.filtro_turma.addItem(t["nome"], t["id"])
        idx = self.filtro_turma.findData(atual)
        if idx >= 0:
            self.filtro_turma.setCurrentIndex(idx)
        else:
            self.filtro_turma.setCurrentIndex(0)
        self.filtro_turma.blockSignals(False)

    def recarregar_tudo(self):
        self.recarregar_turmas_filtro()
        self.atualizar()
        self.aluno_alterado.emit()

    def _importar_geral(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar Alunos (.txt)", "", "Arquivo de texto (*.txt)"
        )
        if not caminho:
            return

        dlg = DialogImportarEstruturado(caminho, self)
        if dlg.exec():
            self.recarregar_tudo()

    # Estilos
    def _btn_primary(self):
        return """QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
            color: white; border-radius: 8px; padding: 8px 16px;
            font-size: 13px; font-weight: bold;
        }
        QPushButton:hover { background: #8B85FF; }"""

    def _btn_secondary(self):
        return """QPushButton {
            background: #2A3050; color: #9AA3C0; border-radius: 8px;
            padding: 8px 14px; font-size: 12px;
        }
        QPushButton:hover { background: #3A4560; color: #E0E6F0; }"""

    def _combo_style(self):
        return """QComboBox {
            background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
            color: #E0E6F0; padding: 7px 10px; font-size: 12px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background: #252B3D; color: #E0E6F0; }"""

    def _table_style(self):
        return """
        QTableWidget {
            background: #1A1F2E; border: 1px solid #2A3050;
            border-radius: 8px; color: #E0E6F0;
            gridline-color: #2A3050; font-size: 12px;
        }
        QTableWidget::item { padding: 6px; }
        QTableWidget::item:selected { background: #3D3580; }
        QTableWidget::item:alternate { background: #1E2535; }
        QHeaderView::section {
            background: #252B3D; color: #9AA3C0; padding: 8px;
            border: none; font-size: 12px; font-weight: bold;
        }"""
