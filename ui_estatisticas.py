"""
ui_estatisticas.py — Aba de Estatísticas Mensais + Geração de Relatório em PDF.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QFrame, QGridLayout, QGroupBox, QSpinBox,
    QFileDialog, QMessageBox, QSizePolicy, QDoubleSpinBox
)

import db
from icones import get_icon

_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

_BTN_PRIMARY = """QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
    color: white; border-radius: 8px; padding: 8px 18px; font-size: 13px; font-weight: bold;
}
QPushButton:hover { background: #7C75FF; }"""

_BTN_PDF = """QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #DC2626,stop:1 #EF4444);
    color: white; border-radius: 8px; padding: 8px 18px; font-size: 13px; font-weight: bold;
}
QPushButton:hover { background: #EF4444; }"""


def _card(titulo: str, valor: str, subtitulo: str = "", cor_val: str = "#6C63FF") -> QFrame:
    frame = QFrame()
    frame.setStyleSheet("QFrame { background: #252B3D; border-radius: 12px; border: 1px solid #3A4560; }")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(4)

    t = QLabel(titulo)
    t.setStyleSheet("color: #9AA3C0; font-size: 11px; font-weight: bold; border: none;")
    lay.addWidget(t)

    v = QLabel(valor)
    v.setStyleSheet(f"color: {cor_val}; font-size: 24px; font-weight: bold; border: none;")
    lay.addWidget(v)

    if subtitulo:
        s = QLabel(subtitulo)
        s.setStyleSheet("color: #8A94B0; font-size: 11px; border: none;")
        s.setWordWrap(True)
        lay.addWidget(s)

    return frame


class AbaEstatisticas(QWidget):
    def __init__(self):
        super().__init__()
        self._dyn_widget: QWidget | None = None
        self._build_ui()
        self.atualizar()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(container)
        self._content_layout.setSpacing(16)
        self._content_layout.setContentsMargins(16, 16, 16, 16)

        scroll.setWidget(container)
        outer.addWidget(scroll)

        # --- Barra de controles ---
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("QFrame { background: #1E2233; border-radius: 10px; border: 1px solid #2F3852; }")
        ctrl = QHBoxLayout(ctrl_frame)
        ctrl.setContentsMargins(14, 10, 14, 10)
        ctrl.setSpacing(12)

        ctrl_label = QLabel("Período:")
        ctrl_label.setStyleSheet("color: #9AA3C0; font-size: 13px; font-weight: bold;")
        ctrl.addWidget(ctrl_label)

        self.mes_combo = QComboBox()
        for m in _MESES:
            self.mes_combo.addItem(m)
        self.mes_combo.setCurrentIndex(date.today().month - 1)
        self.mes_combo.setStyleSheet(self._combo_style())
        ctrl.addWidget(self.mes_combo)

        self.ano_spin = QSpinBox()
        self.ano_spin.setRange(2020, 2050)
        self.ano_spin.setValue(date.today().year)
        self.ano_spin.setStyleSheet("""
            QSpinBox {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 7px 10px; font-size: 13px; min-width: 80px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #3A4560; border-radius: 4px; width: 18px;
            }
        """)
        ctrl.addWidget(self.ano_spin)

        btn_att = QPushButton("Atualizar")
        btn_att.setIcon(get_icon("atualizar"))
        btn_att.setStyleSheet(_BTN_PRIMARY)
        btn_att.clicked.connect(self.atualizar)
        ctrl.addWidget(btn_att)

        limite_label = QLabel("Alerta de frequência <")
        limite_label.setStyleSheet("color: #9AA3C0; font-size: 12px; margin-left: 10px;")
        ctrl.addWidget(limite_label)

        self.limite_spin = QDoubleSpinBox()
        self.limite_spin.setRange(0, 100)
        self.limite_spin.setValue(75.0)
        self.limite_spin.setSuffix("%")
        self.limite_spin.setDecimals(0)
        self.limite_spin.setStyleSheet("""
            QDoubleSpinBox {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 7px 10px; font-size: 13px; min-width: 80px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background: #3A4560; border-radius: 4px; width: 18px;
            }
        """)
        ctrl.addWidget(self.limite_spin)

        ctrl.addStretch()

        btn_pdf = QPushButton("Gerar Relatório PDF")
        btn_pdf.setIcon(get_icon("pdf"))
        btn_pdf.setStyleSheet(_BTN_PDF)
        btn_pdf.clicked.connect(self._gerar_pdf)
        ctrl.addWidget(btn_pdf)

        self._content_layout.addWidget(ctrl_frame)

    def atualizar(self):
        mes = self.mes_combo.currentIndex() + 1
        ano = self.ano_spin.value()
        limite = self.limite_spin.value()

        # CORREÇÃO DE BUG VISUAL:
        # Destrói completamente o widget dinâmico anterior antes de criar o novo
        if self._dyn_widget is not None:
            self._dyn_widget.setParent(None)
            self._dyn_widget.deleteLater()
            self._dyn_widget = None

        self._dyn_widget = QWidget()
        self._dyn_widget.setStyleSheet("background: transparent;")
        dyn_lay = QVBoxLayout(self._dyn_widget)
        dyn_lay.setSpacing(18)
        dyn_lay.setContentsMargins(0, 0, 0, 0)
        self._content_layout.addWidget(self._dyn_widget)

        stats = db.estatisticas_mes(mes, ano)
        mes_nome = _MESES[mes - 1]
        titulo_periodo = f"{mes_nome} de {ano}"

        # Cabeçalho da seção
        hdr_box = QHBoxLayout()
        titulo = QLabel(f"Estatísticas Gerais — {titulo_periodo}")
        titulo.setStyleSheet("color: #E0E6F0; font-size: 18px; font-weight: bold;")
        hdr_box.addWidget(titulo)
        hdr_box.addStretch()
        dyn_lay.addLayout(hdr_box)

        # -------------------------------------------------------------------
        # 1. CARDS PRINCIPAIS
        # -------------------------------------------------------------------
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        # Horas
        h_info = stats["horas_curso"].get("Informática", {})
        h_robo = stats["horas_curso"].get("Robótica", {})
        cards_grid.addWidget(
            _card(
                "Horas de Aula no Mês",
                f"{stats['total_horas']}h",
                f"Informática: {h_info.get('horas', 0)}h | Robótica: {h_robo.get('horas', 0)}h",
                "#F59E0B"
            ),
            0, 0
        )

        # Total Alunos
        cnt = stats["contagem"]
        tot_alunos = (cnt.get("so_info") or 0) + (cnt.get("so_robo") or 0) + (cnt.get("ambos") or 0)
        cards_grid.addWidget(
            _card(
                "Total de Alunos",
                str(tot_alunos),
                f"Só Info: {cnt.get('so_info', 0)} | Só Robô: {cnt.get('so_robo', 0)} | Ambos: {cnt.get('ambos', 0)}",
                "#6C63FF"
            ),
            0, 1
        )

        # Presença Mensal Informática
        pres_info = stats["presenca_mensal_cursos"].get("Informática", {})
        p_info_pct = f"{pres_info.get('pct')}%" if pres_info.get("pct") is not None else "Sem aulas"
        p_info_sub = f"Presenças: {pres_info.get('presentes', 0)} | Faltas: {pres_info.get('ausentes', 0)}"
        cards_grid.addWidget(
            _card("Presença Mensal — Informática", p_info_pct, p_info_sub, "#10B981"),
            0, 2
        )

        # Presença Mensal Robótica
        pres_robo = stats["presenca_mensal_cursos"].get("Robótica", {})
        p_robo_pct = f"{pres_robo.get('pct')}%" if pres_robo.get("pct") is not None else "Sem aulas"
        p_robo_sub = f"Presenças: {pres_robo.get('presentes', 0)} | Faltas: {pres_robo.get('ausentes', 0)}"
        cards_grid.addWidget(
            _card("Presença Mensal — Robótica", p_robo_pct, p_robo_sub, "#10B981"),
            0, 3
        )

        dyn_lay.addLayout(cards_grid)

        # -------------------------------------------------------------------
        # 2. CURSOS OFERECIDOS NO MÊS
        # -------------------------------------------------------------------
        grp_cursos = QGroupBox("Cursos Oferecidos no Mês")
        grp_cursos.setStyleSheet(self._grp_style())
        gc_lay = QVBoxLayout(grp_cursos)

        tbl_cursos = QTableWidget()
        tbl_cursos.setColumnCount(6)
        tbl_cursos.setHorizontalHeaderLabels([
            "Curso", "Turmas Cadastradas", "Turmas Ativas no Mês", "Aulas Ministradas", "Carga Horária (Mês)", "Matrículas Vinculadas"
        ])
        tbl_cursos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for ci in range(1, 6):
            tbl_cursos.horizontalHeader().setSectionResizeMode(ci, QHeaderView.ResizeToContents)
        tbl_cursos.setAlternatingRowColors(True)
        tbl_cursos.verticalHeader().setVisible(False)
        tbl_cursos.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl_cursos.setStyleSheet(self._table_style())
        tbl_cursos.setRowCount(2)

        for ri, c_nome in enumerate(["Informática", "Robótica"]):
            c_info = stats["cursos_oferecidos"].get(c_nome, {})
            tbl_cursos.setItem(ri, 0, QTableWidgetItem(f"{c_nome} Básica" if c_nome == "Informática" else c_nome))
            tbl_cursos.setItem(ri, 1, QTableWidgetItem(str(c_info.get("total_turmas", 0))))
            tbl_cursos.setItem(ri, 2, QTableWidgetItem(str(c_info.get("turmas_ativas", 0))))
            tbl_cursos.setItem(ri, 3, QTableWidgetItem(str(c_info.get("aulas_no_mes", 0))))
            tbl_cursos.setItem(ri, 4, QTableWidgetItem(f"{c_info.get('horas', 0)}h ({c_info.get('minutos', 0)} min)"))
            tbl_cursos.setItem(ri, 5, QTableWidgetItem(str(c_info.get("matriculas", 0))))
            tbl_cursos.setRowHeight(ri, 34)

        tbl_cursos.setFixedHeight(105)
        gc_lay.addWidget(tbl_cursos)
        dyn_lay.addWidget(grp_cursos)

        # -------------------------------------------------------------------
        # 3. PRESENÇA MENSAL DETALHADA POR IDADE E SEXO
        # -------------------------------------------------------------------
        grp_detalhada = QGroupBox("Presença Mensal Detalhada por Idade e Sexo")
        grp_detalhada.setStyleSheet(self._grp_style())
        gd_lay = QVBoxLayout(grp_detalhada)

        # Resumo por sexo
        s_box = QHBoxLayout()
        s_box.setSpacing(16)
        sexo_m = stats["presenca_por_sexo"]["Masculino"]
        sexo_f = stats["presenca_por_sexo"]["Feminino"]

        lbl_m = QLabel(
            f"<b>Masculino:</b> Frequência: <span style='color:#60A5FA; font-weight:bold;'>"
            f"{sexo_m['pct'] if sexo_m['pct'] is not None else '—'}%</span> "
            f"({sexo_m['presentes']} presenças / {sexo_m['total']} chamadas)"
        )
        lbl_m.setStyleSheet("color: #E0E6F0; font-size: 13px; background: #1E2538; padding: 6px 12px; border-radius: 6px;")

        lbl_f = QLabel(
            f"<b>Feminino:</b> Frequência: <span style='color:#F472B6; font-weight:bold;'>"
            f"{sexo_f['pct'] if sexo_f['pct'] is not None else '—'}%</span> "
            f"({sexo_f['presentes']} presenças / {sexo_f['total']} chamadas)"
        )
        lbl_f.setStyleSheet("color: #E0E6F0; font-size: 13px; background: #1E2538; padding: 6px 12px; border-radius: 6px;")

        s_box.addWidget(lbl_m)
        s_box.addWidget(lbl_f)
        s_box.addStretch()
        gd_lay.addLayout(s_box)

        # Tabela por Idade e Sexo
        tbl_idade_sexo = QTableWidget()
        tbl_idade_sexo.setColumnCount(5)
        tbl_idade_sexo.setHorizontalHeaderLabels([
            "Idade", "Presença Masculino", "Presença Feminino", "Frequência Geral da Idade", "Total de Registros"
        ])
        tbl_idade_sexo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for ci in range(1, 5):
            tbl_idade_sexo.horizontalHeader().setSectionResizeMode(ci, QHeaderView.Stretch)
        tbl_idade_sexo.setAlternatingRowColors(True)
        tbl_idade_sexo.verticalHeader().setVisible(False)
        tbl_idade_sexo.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl_idade_sexo.setStyleSheet(self._table_style())

        idades_dados = stats.get("presenca_por_idade", {})
        if idades_dados:
            tbl_idade_sexo.setRowCount(len(idades_dados))
            for ri, ida in enumerate(sorted(idades_dados.keys())):
                d = idades_dados[ida]
                m_txt = f"{d['Masculino']['pct']}% ({d['Masculino']['presentes']}/{d['Masculino']['total']})" if d['Masculino']['pct'] is not None else "—"
                f_txt = f"{d['Feminino']['pct']}% ({d['Feminino']['presentes']}/{d['Feminino']['total']})" if d['Feminino']['pct'] is not None else "—"
                g_txt = f"{d['pct']}%" if d['pct'] is not None else "—"

                tbl_idade_sexo.setItem(ri, 0, QTableWidgetItem(f"{ida} anos"))
                tbl_idade_sexo.setItem(ri, 1, QTableWidgetItem(m_txt))
                tbl_idade_sexo.setItem(ri, 2, QTableWidgetItem(f_txt))

                item_g = QTableWidgetItem(g_txt)
                if d['pct'] is not None:
                    item_g.setForeground(QColor("#10B981") if d['pct'] >= 75 else QColor("#F87171"))
                tbl_idade_sexo.setItem(ri, 3, item_g)

                tbl_idade_sexo.setItem(ri, 4, QTableWidgetItem(f"{d['total_presentes']}/{d['total_registros']} presenças"))
                tbl_idade_sexo.setRowHeight(ri, 32)
            tbl_idade_sexo.setFixedHeight(min(240, 36 + len(idades_dados) * 32))
            gd_lay.addWidget(tbl_idade_sexo)
        else:
            sem_dados = QLabel("Nenhuma chamada realizada com registro de nascimento neste mês.")
            sem_dados.setStyleSheet("color: #8A94B0; font-size: 12px; padding: 6px;")
            gd_lay.addWidget(sem_dados)

        dyn_lay.addWidget(grp_detalhada)

        # -------------------------------------------------------------------
        # 4. NÚMERO DE ALUNOS POR CURSO A CADA 4 MESES (QUADRIMESTRES)
        # -------------------------------------------------------------------
        grp_quad = QGroupBox(f"Evolução de Alunos por Curso a Cada 4 Meses — {ano}")
        grp_quad.setStyleSheet(self._grp_style())
        gq_lay = QVBoxLayout(grp_quad)

        tbl_quad = QTableWidget()
        tbl_quad.setColumnCount(5)
        tbl_quad.setHorizontalHeaderLabels([
            "Período (Quadrimestre)", "Informática", "Robótica", "Ambos os Cursos", "Total de Alunos"
        ])
        tbl_quad.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for ci in range(1, 5):
            tbl_quad.horizontalHeader().setSectionResizeMode(ci, QHeaderView.ResizeToContents)
        tbl_quad.setAlternatingRowColors(True)
        tbl_quad.verticalHeader().setVisible(False)
        tbl_quad.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl_quad.setStyleSheet(self._table_style())

        quads = stats.get("quadrimestres", [])
        tbl_quad.setRowCount(len(quads))
        for ri, q in enumerate(quads):
            tbl_quad.setItem(ri, 0, QTableWidgetItem(q["quadrimestre"]))
            if q["teve_aulas"]:
                tbl_quad.setItem(ri, 1, QTableWidgetItem(f"{q['info_ativos']} ativos"))
                tbl_quad.setItem(ri, 2, QTableWidgetItem(f"{q['robo_ativos']} ativos"))
                tbl_quad.setItem(ri, 3, QTableWidgetItem(f"{q['ambos_ativos']} ativos"))
                tbl_quad.setItem(ri, 4, QTableWidgetItem(f"{q['total_ativos']} alunos ativos"))
            else:
                tbl_quad.setItem(ri, 1, QTableWidgetItem(f"{q['info_cadastrados']} matriculados"))
                tbl_quad.setItem(ri, 2, QTableWidgetItem(f"{q['robo_cadastrados']} matriculados"))
                tbl_quad.setItem(ri, 3, QTableWidgetItem(f"{q['ambos_cadastrados']} matriculados"))
                tbl_quad.setItem(ri, 4, QTableWidgetItem(f"{q['total_cadastrados']} matriculados"))
            tbl_quad.setRowHeight(ri, 34)

        tbl_quad.setFixedHeight(140)
        gq_lay.addWidget(tbl_quad)
        dyn_lay.addWidget(grp_quad)

        # -------------------------------------------------------------------
        # 5. DISTRIBUIÇÃO CADASTRAL: GÊNERO E IDADES GERAIS
        # -------------------------------------------------------------------
        linha_cad = QHBoxLayout()
        linha_cad.setSpacing(12)

        # Gênero
        grp_genero = QGroupBox("Distribuição Cadastral por Gênero")
        grp_genero.setStyleSheet(self._grp_style())
        gen_lay = QVBoxLayout(grp_genero)
        gen_data = defaultdict(lambda: {"Masculino": 0, "Feminino": 0})
        for g in stats["genero"]:
            curso = g["curso"] if g["curso"] in ("Informática", "Robótica") else "Ambos"
            gen_data[curso][g["genero"]] = g["qtd"]

        for curso_g in ("Informática", "Robótica", "Ambos"):
            masc = gen_data[curso_g]["Masculino"]
            fem = gen_data[curso_g]["Feminino"]
            lbl = QLabel(
                f"<b>{curso_g}:</b>  Masculino: <span style='color:#60A5FA; font-weight:bold;'>{masc}</span>  |  "
                f"Feminino: <span style='color:#F472B6; font-weight:bold;'>{fem}</span>"
            )
            lbl.setStyleSheet("color: #E0E6F0; font-size: 12px; padding: 3px 0;")
            gen_lay.addWidget(lbl)
        linha_cad.addWidget(grp_genero, 1)

        # Idades
        grp_idades = QGroupBox("Distribuição Geral de Idades")
        grp_idades.setStyleSheet(self._grp_style())
        ida_lay = QVBoxLayout(grp_idades)

        idades_counter: defaultdict[int, int] = defaultdict(int)
        hoje = datetime.now().date()
        for row in stats["idades_rows"]:
            try:
                d = datetime.strptime(row["data_nascimento"], "%Y-%m-%d").date()
                idade = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
                idades_counter[idade] += 1
            except Exception:
                pass

        if idades_counter:
            res_ida = []
            for idade_val in sorted(idades_counter.keys()):
                res_ida.append(f"<b>{idade_val} anos:</b> {idades_counter[idade_val]}")
            # Divide em duas colunas ou formato compacto
            lbl_ida = QLabel("   •   ".join(res_ida))
            lbl_ida.setWordWrap(True)
            lbl_ida.setStyleSheet("color: #9AA3C0; font-size: 12px; line-height: 18px;")
            ida_lay.addWidget(lbl_ida)
        else:
            ida_lay.addWidget(QLabel("Sem dados de nascimento cadastrados."))
        linha_cad.addWidget(grp_idades, 1)

        dyn_lay.addLayout(linha_cad)

        # -------------------------------------------------------------------
        # 6. ALERTA DE FREQUÊNCIA BAIXA
        # -------------------------------------------------------------------
        baixa = db.alunos_freq_baixa(mes, ano, limite)
        grp_alerta = QGroupBox(f"Alerta: Frequência Abaixo de {int(limite)}%")
        grp_alerta.setStyleSheet("""
            QGroupBox {
                border: 1px solid #F59E0B; border-radius: 10px;
                margin-top: 8px; color: #FBBF24; font-size: 13px; font-weight: bold;
                background: #1F1A00; padding: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
        """)
        alerta_lay = QVBoxLayout(grp_alerta)

        if baixa:
            tbl_alerta = QTableWidget()
            tbl_alerta.setColumnCount(5)
            tbl_alerta.setHorizontalHeaderLabels(["Aluno", "Curso", "Turmas", "Presenças", "Frequência"])
            tbl_alerta.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            tbl_alerta.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            tbl_alerta.setColumnWidth(1, 100)
            tbl_alerta.setColumnWidth(3, 90)
            tbl_alerta.setColumnWidth(4, 100)
            tbl_alerta.setAlternatingRowColors(True)
            tbl_alerta.verticalHeader().setVisible(False)
            tbl_alerta.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl_alerta.setMaximumHeight(220)
            tbl_alerta.setStyleSheet("""
                QTableWidget { background: #1A1500; border: none; color: #FBBF24;
                    gridline-color: #3A2A00; font-size: 12px; }
                QTableWidget::item:alternate { background: #1F1A00; }
                QHeaderView::section { background: #2A2000; color: #F59E0B;
                    padding: 8px; border: none; font-size: 12px; font-weight: bold; }
            """)
            tbl_alerta.setRowCount(len(baixa))
            for ri, b in enumerate(baixa):
                tbl_alerta.setItem(ri, 0, QTableWidgetItem(b["nome"]))
                tbl_alerta.setItem(ri, 1, QTableWidgetItem(b["curso"]))
                tbl_alerta.setItem(ri, 2, QTableWidgetItem(b["turmas"]))
                tbl_alerta.setItem(ri, 3, QTableWidgetItem(f"{b['presentes']}/{b['total']}"))
                freq_item = QTableWidgetItem(f"{b['pct']}%")
                freq_item.setForeground(QColor("#F87171"))
                tbl_alerta.setItem(ri, 4, freq_item)
            alerta_lay.addWidget(tbl_alerta)
        else:
            ok_lbl = QLabel(f"Nenhum aluno com frequência abaixo de {int(limite)}% neste período.")
            ok_lbl.setStyleSheet("color: #4ADE80; font-size: 13px; font-weight: bold;")
            alerta_lay.addWidget(ok_lbl)

        dyn_lay.addWidget(grp_alerta)

    def _gerar_pdf(self):
        mes = self.mes_combo.currentIndex() + 1
        ano = self.ano_spin.value()
        periodo = f"{_MESES[mes-1]}_{ano}"

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório PDF",
            str(Path.home() / f"Relatorio_ABDA_{periodo}.pdf"),
            "PDF (*.pdf)"
        )
        if not caminho:
            return

        try:
            self._gerar_pdf_reportlab(caminho, mes, ano)
            QMessageBox.information(self, "Relatório Concluído",
                                    f"Relatório salvo com sucesso em:\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar PDF", str(e))

    def _gerar_pdf_reportlab(self, caminho: str, mes: int, ano: int):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        stats = db.estatisticas_mes(mes, ano)
        baixa = db.alunos_freq_baixa(mes, ano, self.limite_spin.value())
        periodo = f"{_MESES[mes-1]} de {ano}"

        doc = SimpleDocTemplate(
            caminho, pagesize=A4,
            leftMargin=1.8*cm, rightMargin=1.8*cm,
            topMargin=1.8*cm, bottomMargin=1.8*cm
        )
        styles = getSampleStyleSheet()
        story = []

        # Estilos tipográficos limpos (sem emojis para evitar erros de fontes)
        title_style = ParagraphStyle(
            "Title2", parent=styles["Title"],
            fontSize=18, textColor=colors.HexColor("#1A1F2E"),
            spaceAfter=3, alignment=0
        )
        sub_style = ParagraphStyle(
            "Sub", parent=styles["Normal"],
            fontSize=10, textColor=colors.HexColor("#6C63FF"),
            spaceAfter=12
        )
        h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12,
                             textColor=colors.HexColor("#252B3D"), spaceBefore=12, spaceAfter=6)
        small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=9,
                                textColor=colors.HexColor("#555"), leading=13)

        # Cabeçalho oficial
        story.append(Paragraph("Sistema de Chamada ABDA", title_style))
        story.append(Paragraph("João Victor Pavanelli &amp; Renan Denadai de Paula  •  Relatório Mensal", sub_style))
        story.append(Paragraph(f"<b>Período de Referência:</b> {periodo}", small))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6C63FF")))
        story.append(Spacer(1, 10))

        # 1. Resumo e Horas de Aula no Mês
        story.append(Paragraph("1. Horas por Mês e Resumo Geral de Cursos", h2))
        h_info = stats["horas_curso"].get("Informática", {})
        h_robo = stats["horas_curso"].get("Robótica", {})
        cnt = stats["contagem"]
        tot_alunos = (cnt.get("so_info") or 0) + (cnt.get("so_robo") or 0) + (cnt.get("ambos") or 0)

        data_resumo = [
            ["Métrica / Indicador", "Informática", "Robótica", "Total Geral"],
            ["Horas ministradas no mês", f"{h_info.get('horas', 0)}h ({h_info.get('minutos', 0)} min)",
             f"{h_robo.get('horas', 0)}h ({h_robo.get('minutos', 0)} min)", f"{stats['total_horas']}h ({stats['total_minutos']} min)"],
            ["Aulas registradas", str(h_info.get("aulas", 0)), str(h_robo.get("aulas", 0)),
             str(h_info.get("aulas", 0) + h_robo.get("aulas", 0))],
            ["Alunos cadastrados", str(cnt.get("so_info", 0)), str(cnt.get("so_robo", 0)), f"{tot_alunos} (Ambos: {cnt.get('ambos', 0)})"],
            ["Frequência média no mês", f"{stats['freq'].get('Informática') or '—'}%", f"{stats['freq'].get('Robótica') or '—'}%", "—"],
        ]
        t_resumo = Table(data_resumo, colWidths=[5.5*cm, 4*cm, 4*cm, 4*cm])
        t_resumo.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#6C63FF")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F8F9FD"), colors.white]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
            ("FONTSIZE", (0,1), (-1,-1), 9),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(t_resumo)
        story.append(Spacer(1, 12))

        # 2. Cursos Oferecidos Mensalmente
        story.append(Paragraph("2. Cursos Oferecidos no Mês", h2))
        data_cursos = [
            ["Curso", "Turmas Cadastradas", "Turmas Ativas no Mês", "Aulas no Mês", "Matrículas Ativas"]
        ]
        for c_nome in ("Informática", "Robótica"):
            ci = stats["cursos_oferecidos"].get(c_nome, {})
            data_cursos.append([
                c_nome,
                str(ci.get("total_turmas", 0)),
                str(ci.get("turmas_ativas", 0)),
                str(ci.get("aulas_no_mes", 0)),
                str(ci.get("matriculas", 0)),
            ])
        t_cursos = Table(data_cursos, colWidths=[4.5*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3.4*cm])
        t_cursos.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#252B3D")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F8F9FD"), colors.white]),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(t_cursos)
        story.append(Spacer(1, 12))

        # 3. Presença Mensal Detalhada por Idade e Sexo
        story.append(Paragraph("3. Presença Mensal Detalhada por Idade e Sexo", h2))
        sm = stats["presenca_por_sexo"]["Masculino"]
        sf = stats["presenca_por_sexo"]["Feminino"]
        data_sexo = [
            ["Sexo", "Presenças", "Faltas / Ausências", "Total de Registros", "Frequência (%)"],
            ["Masculino", str(sm["presentes"]), str(sm["ausentes"]), str(sm["total"]), f"{sm['pct'] if sm['pct'] is not None else '—'}%"],
            ["Feminino", str(sf["presentes"]), str(sf["ausentes"]), str(sf["total"]), f"{sf['pct'] if sf['pct'] is not None else '—'}%"],
        ]
        t_sexo = Table(data_sexo, colWidths=[4*cm, 3.2*cm, 3.8*cm, 3.5*cm, 3*cm])
        t_sexo.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t_sexo)
        story.append(Spacer(1, 8))

        # Tabela ano a ano de presenças
        idades_dados = stats.get("presenca_por_idade", {})
        if idades_dados:
            data_idade = [["Idade", "Freq. Masculino", "Freq. Feminino", "Freq. Geral da Idade", "Presenças / Total"]]
            for ida in sorted(idades_dados.keys()):
                d = idades_dados[ida]
                m_t = f"{d['Masculino']['pct']}%" if d['Masculino']['pct'] is not None else "—"
                f_t = f"{d['Feminino']['pct']}%" if d['Feminino']['pct'] is not None else "—"
                g_t = f"{d['pct']}%" if d['pct'] is not None else "—"
                data_idade.append([
                    f"{ida} anos", m_t, f_t, g_t, f"{d['total_presentes']}/{d['total_registros']}"
                ])
            t_idade = Table(data_idade, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
            t_idade.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4B5563")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F8F9FD"), colors.white]),
                ("FONTSIZE", (0,0), (-1,-1), 8.5),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(t_idade)
        story.append(Spacer(1, 12))

        # Alunos matriculados por idade e sexo
        story.append(Paragraph("3b. Quantidade de Alunos Matriculados por Idade e Sexo", h2))
        idades_rows = stats.get("idades_rows", [])
        if idades_rows:
            from collections import defaultdict as _dd
            from datetime import date as _date, datetime as _dt
            alunos_por_idade: dict = {}
            hoje_pdf = _date.today()
            for row in idades_rows:
                try:
                    d = _dt.strptime(row["data_nascimento"], "%Y-%m-%d").date()
                    ida = hoje_pdf.year - d.year - ((hoje_pdf.month, hoje_pdf.day) < (d.month, d.day))
                except Exception:
                    continue
                gen = row.get("genero") or "Não informado"
                if ida not in alunos_por_idade:
                    alunos_por_idade[ida] = {"Masculino": 0, "Feminino": 0, "Não informado": 0}
                alunos_por_idade[ida][gen] = alunos_por_idade[ida].get(gen, 0) + 1

            data_matr = [["Idade", "Masculino", "Feminino", "Não Informado", "Total"]]
            for ida in sorted(alunos_por_idade.keys()):
                d = alunos_por_idade[ida]
                masc = d.get("Masculino", 0)
                fem = d.get("Feminino", 0)
                ni = d.get("Não informado", 0)
                data_matr.append([
                    f"{ida} anos",
                    str(masc),
                    str(fem),
                    str(ni),
                    str(masc + fem + ni),
                ])
            t_matr = Table(data_matr, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 2.5*cm])
            t_matr.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F8F9FD"), colors.white]),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(t_matr)
        else:
            story.append(Paragraph("Nenhum aluno com data de nascimento cadastrada.", small))
        story.append(Spacer(1, 12))

        # 4. Número de Alunos por Curso a Cada 4 Meses (Quadrimestres)
        story.append(Paragraph(f"4. Evolução de Alunos por Curso a Cada 4 Meses — Ano {ano}", h2))
        data_quad = [
            ["Quadrimestre", "Informática", "Robótica", "Ambos os Cursos", "Total"]
        ]
        for q in stats.get("quadrimestres", []):
            sufixo = " ativos" if q["teve_aulas"] else " matriculados"
            data_quad.append([
                q["quadrimestre"],
                f"{q['info_ativos'] if q['teve_aulas'] else q['info_cadastrados']}{sufixo}",
                f"{q['robo_ativos'] if q['teve_aulas'] else q['robo_cadastrados']}{sufixo}",
                f"{q['ambos_ativos'] if q['teve_aulas'] else q['ambos_cadastrados']}{sufixo}",
                f"{q['total_ativos'] if q['teve_aulas'] else q['total_cadastrados']}{sufixo}",
            ])
        t_quad = Table(data_quad, colWidths=[5*cm, 3.2*cm, 3.2*cm, 3.2*cm, 2.9*cm])
        t_quad.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#6C63FF")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F8F9FD"), colors.white]),
            ("FONTSIZE", (0,0), (-1,-1), 8.5),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t_quad)
        story.append(Spacer(1, 12))

        # 5. Alerta de Frequência Baixa
        story.append(Paragraph(f"5. Alerta de Frequência Baixa (Abaixo de {int(self.limite_spin.value())}%)", h2))
        if baixa:
            al_rows = [["Aluno", "Curso", "Turmas", "Presenças", "Frequência"]]
            for b in baixa:
                al_rows.append([b["nome"], b["curso"], b["turmas"],
                                f"{b['presentes']}/{b['total']}", f"{b['pct']}%"])
            t_al = Table(al_rows, colWidths=[5*cm, 3.5*cm, 5.5*cm, 2*cm, 1.5*cm])
            t_al.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#92400E")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#FFF8E7"), colors.HexColor("#FFFDF0")]),
                ("TEXTCOLOR", (4,1), (4,-1), colors.HexColor("#DC2626")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D97706")),
                ("FONTSIZE", (0,0), (-1,-1), 8.5),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(t_al)
        else:
            story.append(Paragraph(f"Nenhum aluno com frequência abaixo de {int(self.limite_spin.value())}% neste período.", small))

        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCDD")))
        story.append(Spacer(1, 4))
        gerado_em = datetime.now().strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph(f"Relatório gerado em {gerado_em} — Sistema de Chamada ABDA", small))

        doc.build(story)

    def _combo_style(self):
        return """QComboBox {
            background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
            color: #E0E6F0; padding: 7px 12px; font-size: 13px; min-width: 130px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background: #252B3D; color: #E0E6F0; }"""

    def _grp_style(self):
        return """
        QGroupBox {
            border: 1px solid #3A4560; border-radius: 10px;
            margin-top: 8px; color: #9AA3C0; font-size: 12px; font-weight: bold;
            background: #1E2233; padding: 12px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; }
        QLabel { color: #E0E6F0; border: none; }"""

    def _table_style(self):
        return """
        QTableWidget {
            background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
            color: #E0E6F0; gridline-color: #2F3752; font-size: 12px;
        }
        QTableWidget::item { padding: 4px 6px; }
        QTableWidget::item:selected { background: #3D3580; color: white; }
        QTableWidget::item:alternate { background: #1E2435; }
        QHeaderView::section {
            background: #1E2233; color: #9AA3C0; padding: 6px;
            border: none; font-size: 11px; font-weight: bold;
        }"""
