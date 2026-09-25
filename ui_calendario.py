"""
ui_calendario.py — Aba de Calendário Mensal e Agendamento de Chamadas.
Exibe todos os dias do mês com as turmas agendadas de Segunda a Sexta
(Informática e Robótica), status de chamada pendente (!) e realizada (✓),
e diálogo interativo para seleção de turma e chamada direta.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor, QFont, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QFrame, QScrollArea,
    QDialog, QSizePolicy, QMessageBox
)

import db
from icones import get_icon


# Mapeamento dos dias em português
DIAS_SEMANA_NOMES = [
    "Segunda-feira", "Terça-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"
]

DIAS_SEMANA_CURTO = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


# ---------------------------------------------------------------------------
# Diálogo para escolher a turma e horário do dia
# ---------------------------------------------------------------------------
class DialogEscolherTurmaDia(QDialog):
    """Diálogo modal aberto ao clicar em um dia do calendário."""
    turma_selecionada = Signal(str, str)  # (turma_id, data_str)

    def __init__(self, data_alvo: date, turmas: list, status_chamadas: dict, parent=None):
        super().__init__(parent)
        self.data_alvo = data_alvo
        self.turmas = turmas
        self.status_chamadas = status_chamadas
        self.data_str = data_alvo.strftime("%Y-%m-%d")

        dia_sem_idx = data_alvo.weekday()
        dia_sem_nome = DIAS_SEMANA_NOMES[dia_sem_idx]
        data_fmt = data_alvo.strftime("%d/%m/%Y")

        self.setWindowTitle(f"Chamada — {dia_sem_nome}, {data_fmt}")
        self.setMinimumWidth(560)
        self.setStyleSheet("""
            QDialog {
                background-color: #1A1F2E;
                color: #E0E6F0;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
            }
            QLabel { color: #E0E6F0; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Cabeçalho
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        data_title = QLabel(f"📅  {dia_sem_nome}, {data_fmt}")
        data_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(data_title)

        sub_title = QLabel("Selecione o horário e turma abaixo para realizar ou editar a chamada:")
        sub_title.setStyleSheet("font-size: 13px; color: #9AA3C0;")
        header_layout.addWidget(sub_title)

        layout.addLayout(header_layout)

        # Divisor
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: #2A3050; margin: 4px 0;")
        layout.addWidget(div)

        # Área de rolagem para os cards de turmas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1A1F2E; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #3A4560; border-radius: 4px; }
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 8, 0)
        c_layout.setSpacing(12)

        if not turmas:
            aviso = QLabel("Não há aulas regulares cadastradas para este dia.")
            aviso.setStyleSheet("color: #6A7490; font-size: 14px; padding: 24px; text-align: center;")
            aviso.setAlignment(Qt.AlignCenter)
            c_layout.addWidget(aviso)
        else:
            for t in turmas:
                card = self._criar_card_turma(t)
                c_layout.addWidget(card)

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        # Botão Fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet("""
            QPushButton {
                background: #252B3D; color: #9AA3C0; border: 1px solid #3A4560;
                border-radius: 8px; padding: 8px 24px; font-size: 13px;
            }
            QPushButton:hover { background: #3A4560; color: #FFFFFF; }
        """)
        btn_fechar.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(btn_fechar)
        layout.addLayout(footer)

    def _criar_card_turma(self, turma: dict | sqlite3.Row) -> QFrame:
        turma = dict(turma)
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #252B3D; border: 1px solid #3A4560;
                border-radius: 10px; padding: 4px;
            }
            QFrame:hover {
                border-color: #6C63FF; background: #2B334B;
            }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Informações da Turma
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Horário e Curso
        topo_layout = QHBoxLayout()
        topo_layout.setSpacing(8)

        hora_lbl = QLabel(f"⏰ {turma.get('horario_inicio', '')} – {turma.get('horario_fim', '')}")
        hora_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")
        topo_layout.addWidget(hora_lbl)

        curso = turma.get("curso", "Informática")
        tag_bg = "#1E3A5F" if curso == "Informática" else "#3B2667"
        tag_fg = "#38BDF8" if curso == "Informática" else "#C084FC"

        curso_tag = QLabel(f" {curso} ")
        curso_tag.setStyleSheet(f"""
            background: {tag_bg}; color: {tag_fg}; border-radius: 4px;
            font-size: 11px; font-weight: 600; padding: 2px 6px;
        """)
        topo_layout.addWidget(curso_tag)
        topo_layout.addStretch()
        info_layout.addLayout(topo_layout)

        # Nome da turma
        nome_lbl = QLabel(turma.get("nome", turma.get("id", "")))
        nome_lbl.setStyleSheet("font-size: 12px; color: #9AA3C0;")
        info_layout.addWidget(nome_lbl)

        layout.addLayout(info_layout, stretch=1)

        # Status da Chamada
        key = f"{turma['id']}_{self.data_str}"
        chamada_info = self.status_chamadas.get(key)

        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_layout.setSpacing(6)

        if chamada_info:
            tot_p = chamada_info["total_presentes"]
            tot_a = chamada_info["total_ausentes"]
            tot = chamada_info["total_alunos"]
            status_lbl = QLabel(f"✓ Realizada ({tot_p} pres. / {tot_a} aus.)")
            status_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 12px;")

            btn_acao = QPushButton("Editar Chamada")
            btn_acao.setIcon(get_icon("editar"))
            btn_acao.setStyleSheet("""
                QPushButton {
                    background: #2A3050; color: #38BDF8; border: 1px solid #38BDF8;
                    border-radius: 6px; padding: 7px 16px; font-size: 12px; font-weight: bold;
                }
                QPushButton:hover { background: #38BDF8; color: #0F172A; }
            """)
        else:
            status_lbl = QLabel("! Chamada Pendente")
            status_lbl.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 12px;")

            btn_acao = QPushButton("Realizar Chamada")
            btn_acao.setIcon(get_icon("chamada"))
            btn_acao.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6C63FF,stop:1 #8B85FF);
                    color: white; border: none; border-radius: 6px;
                    padding: 7px 16px; font-size: 12px; font-weight: bold;
                }
                QPushButton:hover { background: #7C75FF; }
            """)

        status_layout.addWidget(status_lbl, alignment=Qt.AlignRight)
        status_layout.addWidget(btn_acao, alignment=Qt.AlignRight)

        turma_id_capturado = turma["id"]
        btn_acao.clicked.connect(lambda: self._acionar_chamada(turma_id_capturado))

        layout.addLayout(status_layout)
        return card

    def _acionar_chamada(self, turma_id: str):
        self.turma_selecionada.emit(turma_id, self.data_str)
        self.accept()


# ---------------------------------------------------------------------------
# Card individual de cada dia do calendário
# ---------------------------------------------------------------------------
class CardDiaCalendario(QFrame):
    """Card visual para representar um dia na grade mensal."""
    clicado = Signal(object)  # data alvo (date)

    def __init__(self, data_dia: date, turmas_dia: list, status_chamadas: dict, eh_mes_atual: bool = True):
        super().__init__()
        self.data_dia = data_dia
        self.turmas_dia = turmas_dia
        self.status_chamadas = status_chamadas
        self.eh_mes_atual = eh_mes_atual

        self.data_str = data_dia.strftime("%Y-%m-%d")
        self.eh_hoje = (data_dia == date.today())
        self.eh_fim_semana = (data_dia.weekday() >= 5)

        self._configurar_ui()

    def _configurar_ui(self):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(115)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Cores e bordas dependendo do status do dia
        borda = "#6C63FF" if self.eh_hoje else ("#2A3050" if self.eh_fim_semana else "#3A4560")
        bg = "#1F2637" if self.eh_fim_semana else "#252B3D"
        opacity = "0.6" if not self.eh_mes_atual else "1.0"

        self.setStyleSheet(f"""
            CardDiaCalendario {{
                background-color: {bg};
                border: 1.5px solid {borda};
                border-radius: 10px;
            }}
            CardDiaCalendario:hover {{
                border-color: #8B85FF;
                background-color: #2D354C;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Cabeçalho do Card (Número do dia e Badges)
        header = QHBoxLayout()
        header.setSpacing(4)

        num_lbl = QLabel(str(self.data_dia.day))
        if self.eh_hoje:
            num_lbl.setStyleSheet("""
                background: #6C63FF; color: white; border-radius: 11px;
                font-size: 12px; font-weight: bold; min-width: 22px; max-width: 22px;
                min-height: 22px; max-height: 22px; qproperty-alignment: AlignCenter;
            """)
        else:
            cor_num = "#E0E6F0" if self.eh_mes_atual else "#6A7490"
            num_lbl.setStyleSheet(f"color: {cor_num}; font-size: 13px; font-weight: bold; background: transparent;")

        header.addWidget(num_lbl)

        if self.eh_hoje:
            badge_hoje = QLabel("Hoje")
            badge_hoje.setStyleSheet("color: #8B85FF; font-size: 10px; font-weight: bold; background: transparent;")
            header.addWidget(badge_hoje)

        header.addStretch()

        # Se houver aulas, calcula resumo de chamadas pendentes / realizadas
        total_turmas = len(self.turmas_dia)
        total_realizadas = 0

        for t in self.turmas_dia:
            key = f"{t['id']}_{self.data_str}"
            if key in self.status_chamadas:
                total_realizadas += 1

        total_pendentes = total_turmas - total_realizadas

        if total_turmas > 0:
            if total_pendentes > 0:
                # Ícone / Badge de Alerta (!)
                alerta_badge = QLabel(f"! {total_pendentes}")
                alerta_badge.setToolTip(f"{total_pendentes} chamada(s) pendente(s)")
                alerta_badge.setStyleSheet("""
                    background: #F59E0B; color: #1E1B4B; border-radius: 9px;
                    font-size: 10px; font-weight: bold; padding: 2px 6px;
                """)
                header.addWidget(alerta_badge)
            else:
                # Todas realizadas (✓)
                ok_badge = QLabel("✓")
                ok_badge.setToolTip("Todas as chamadas deste dia foram realizadas!")
                ok_badge.setStyleSheet("""
                    background: #10B981; color: white; border-radius: 9px;
                    font-size: 10px; font-weight: bold; padding: 2px 6px;
                """)
                header.addWidget(ok_badge)

        layout.addLayout(header)

        # Lista de turmas compacta
        corpo = QVBoxLayout()
        corpo.setSpacing(2)

        if self.eh_fim_semana:
            msg_fs = QLabel("Fim de semana")
            msg_fs.setStyleSheet("color: #5A6380; font-size: 11px; font-style: italic; background: transparent;")
            msg_fs.setAlignment(Qt.AlignCenter)
            corpo.addStretch()
            corpo.addWidget(msg_fs)
            corpo.addStretch()
        elif total_turmas == 0:
            msg_vazio = QLabel("Sem aulas")
            msg_vazio.setStyleSheet("color: #5A6380; font-size: 11px; background: transparent;")
            msg_vazio.setAlignment(Qt.AlignCenter)
            corpo.addStretch()
            corpo.addWidget(msg_vazio)
            corpo.addStretch()
        else:
            # Mostra até 3 turmas com indicativo e o restante em resumo
            max_mostrar = 3
            for t in self.turmas_dia[:max_mostrar]:
                t_dict = dict(t)
                key = f"{t_dict['id']}_{self.data_str}"
                realizada = (key in self.status_chamadas)

                simbolo = "✓" if realizada else "!"
                cor_simb = "#10B981" if realizada else "#F59E0B"
                h_ini = t_dict.get("horario_inicio", "")
                curso_str = t_dict.get("curso", "")[:4]

                t_lbl = QLabel(f"<span style='color:{cor_simb}; font-weight:bold;'>{simbolo}</span> {h_ini} {curso_str}")
                t_lbl.setTextFormat(Qt.RichText)
                t_lbl.setStyleSheet("font-size: 11px; background: transparent;")
                corpo.addWidget(t_lbl)

            if total_turmas > max_mostrar:
                mais_lbl = QLabel(f"+ {total_turmas - max_mostrar} turma(s)...")
                mais_lbl.setStyleSheet("color: #6C63FF; font-size: 10px; font-weight: bold; background: transparent;")
                corpo.addWidget(mais_lbl)

        layout.addLayout(corpo, stretch=1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicado.emit(self.data_dia)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Aba Principal de Calendário
# ---------------------------------------------------------------------------
class AbaCalendario(QWidget):
    """Aba principal do Calendário que exibe a visão mensal e gerencia as chamadas."""
    navegar_para_chamada = Signal(str, str)  # (turma_id, data_str)

    def __init__(self):
        super().__init__()
        hoje = date.today()
        self.ano_atual = hoje.year
        self.mes_atual = hoje.month

        self._build_ui()
        self.recarregar_mes()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(14)
        main.setContentsMargins(16, 14, 16, 14)

        # -------------------------------------------------------------------
        # Barra Superior: Controles de Navegação e Filtros
        # -------------------------------------------------------------------
        nav_frame = QFrame()
        nav_frame.setStyleSheet("""
            QFrame {
                background: #252B3D; border-radius: 12px;
                border: 1px solid #3A4560;
            }
            QLabel { color: #9AA3C0; font-size: 12px; }
            QPushButton {
                background: #1A1F2E; color: #E0E6F0; border: 1px solid #3A4560;
                border-radius: 8px; padding: 7px 14px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: #3A4560; color: #FFFFFF; border-color: #6C63FF; }
            QComboBox {
                background: #1A1F2E; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 6px 12px; font-size: 13px; font-weight: 600;
            }
            QComboBox QAbstractItemView {
                background: #252B3D; color: #E0E6F0; selection-background-color: #3D3580;
            }
            QSpinBox {
                background: #1A1F2E; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; padding: 6px 10px; font-size: 13px; font-weight: 600;
            }
        """)

        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(16, 12, 16, 12)
        nav_layout.setSpacing(12)

        # Botão Mês Anterior
        self.btn_ant = QPushButton("◀ Anterior")
        self.btn_ant.setToolTip("Ir para o mês anterior")
        self.btn_ant.clicked.connect(self._mes_anterior)
        nav_layout.addWidget(self.btn_ant)

        # Seletor de Mês
        self.combo_mes = QComboBox()
        for m in MESES_PT:
            self.combo_mes.addItem(m)
        self.combo_mes.setCurrentIndex(self.mes_atual - 1)
        self.combo_mes.currentIndexChanged.connect(self._ao_mudar_mes_ano)
        nav_layout.addWidget(self.combo_mes)

        # Seletor de Ano
        self.spin_ano = QSpinBox()
        self.spin_ano.setRange(2020, 2035)
        self.spin_ano.setValue(self.ano_atual)
        self.spin_ano.valueChanged.connect(self._ao_mudar_mes_ano)
        nav_layout.addWidget(self.spin_ano)

        # Botão Próximo Mês
        self.btn_prox = QPushButton("Próximo ▶")
        self.btn_prox.setToolTip("Ir para o próximo mês")
        self.btn_prox.clicked.connect(self._proximo_mes)
        nav_layout.addWidget(self.btn_prox)

        # Botão Hoje
        self.btn_hoje = QPushButton("Hoje")
        self.btn_hoje.setIcon(get_icon("atualizar"))
        self.btn_hoje.setStyleSheet("""
            QPushButton {
                background: #2A3050; color: #8B85FF; border: 1px solid #6C63FF;
                border-radius: 8px; padding: 7px 16px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #6C63FF; color: white; }
        """)
        self.btn_hoje.clicked.connect(self._ir_para_hoje)
        nav_layout.addWidget(self.btn_hoje)

        nav_layout.addSpacing(16)

        # Filtro de Curso
        nav_layout.addWidget(QLabel("Curso:"))
        self.combo_curso = QComboBox()
        self.combo_curso.addItems(["Todos os Cursos", "Informática", "Robótica"])
        self.combo_curso.currentIndexChanged.connect(self.recarregar_mes)
        nav_layout.addWidget(self.combo_curso)

        nav_layout.addStretch()

        # Legenda Visual
        legenda_layout = QHBoxLayout()
        legenda_layout.setSpacing(14)

        leg_pend = QLabel("<span style='color:#F59E0B; font-weight:bold; font-size:14px;'>!</span> Chamada Pendente")
        leg_pend.setTextFormat(Qt.RichText)
        leg_pend.setStyleSheet("color: #9AA3C0; font-size: 12px;")

        leg_ok = QLabel("<span style='color:#10B981; font-weight:bold; font-size:14px;'>✓</span> Realizada")
        leg_ok.setTextFormat(Qt.RichText)
        leg_ok.setStyleSheet("color: #9AA3C0; font-size: 12px;")

        legenda_layout.addWidget(leg_pend)
        legenda_layout.addWidget(leg_ok)
        nav_layout.addLayout(legenda_layout)

        main.addWidget(nav_frame)

        # -------------------------------------------------------------------
        # Banner com Resumo Estatístico do Mês
        # -------------------------------------------------------------------
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet("""
            QFrame {
                background: #1E2535; border: 1px solid #2A3050;
                border-radius: 10px; padding: 6px 14px;
            }
            QLabel { color: #E0E6F0; font-size: 12px; }
        """)
        self.banner_layout = QHBoxLayout(self.banner_frame)
        self.banner_layout.setContentsMargins(12, 6, 12, 6)

        self.lbl_stats_mes = QLabel("")
        self.banner_layout.addWidget(self.lbl_stats_mes)
        self.banner_layout.addStretch()

        dica_lbl = QLabel("💡 <i>Clique em qualquer dia com aulas para abrir a lista de horários e fazer a chamada.</i>")
        dica_lbl.setStyleSheet("color: #6A7490; font-size: 11px;")
        self.banner_layout.addWidget(dica_lbl)

        main.addWidget(self.banner_frame)

        # -------------------------------------------------------------------
        # Cabeçalho dos Dias da Semana (Segunda a Domingo)
        # -------------------------------------------------------------------
        dias_header_frame = QFrame()
        dias_header_frame.setStyleSheet("background: transparent; border: none;")
        dias_header_layout = QGridLayout(dias_header_frame)
        dias_header_layout.setContentsMargins(0, 0, 0, 0)
        dias_header_layout.setSpacing(8)

        for col, dia_curto in enumerate(DIAS_SEMANA_CURTO):
            eh_fs = (col >= 5)
            lbl = QLabel(f"{dia_curto.upper()}")
            cor = "#6A7490" if eh_fs else "#8B85FF"
            lbl.setStyleSheet(f"""
                color: {cor}; font-size: 12px; font-weight: bold;
                padding: 6px; text-align: center;
            """)
            lbl.setAlignment(Qt.AlignCenter)
            dias_header_layout.addWidget(lbl, 0, col)

        main.addWidget(dias_header_frame)

        # -------------------------------------------------------------------
        # Área Rolável para a Grade Mensal
        # -------------------------------------------------------------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1A1F2E; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #3A4560; border-radius: 4px; }
        """)

        self.grade_container = QWidget()
        self.grade_container.setStyleSheet("background: transparent;")
        self.grade_layout = QGridLayout(self.grade_container)
        self.grade_layout.setContentsMargins(0, 0, 0, 0)
        self.grade_layout.setSpacing(8)

        scroll_area.setWidget(self.grade_container)
        main.addWidget(scroll_area, stretch=1)

    # -----------------------------------------------------------------------
    # Navegação de Mês / Ano
    # -----------------------------------------------------------------------
    def _ao_mudar_mes_ano(self):
        self.mes_atual = self.combo_mes.currentIndex() + 1
        self.ano_atual = self.spin_ano.value()
        self.recarregar_mes()

    def _mes_anterior(self):
        if self.mes_atual == 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        else:
            self.mes_atual -= 1

        self.combo_mes.blockSignals(True)
        self.spin_ano.blockSignals(True)
        self.combo_mes.setCurrentIndex(self.mes_atual - 1)
        self.spin_ano.setValue(self.ano_atual)
        self.combo_mes.blockSignals(False)
        self.spin_ano.blockSignals(False)

        self.recarregar_mes()

    def _proximo_mes(self):
        if self.mes_atual == 12:
            self.mes_atual = 1
            self.ano_atual += 1
        else:
            self.mes_atual += 1

        self.combo_mes.blockSignals(True)
        self.spin_ano.blockSignals(True)
        self.combo_mes.setCurrentIndex(self.mes_atual - 1)
        self.spin_ano.setValue(self.ano_atual)
        self.combo_mes.blockSignals(False)
        self.spin_ano.blockSignals(False)

        self.recarregar_mes()

    def _ir_para_hoje(self):
        hoje = date.today()
        self.mes_atual = hoje.month
        self.ano_atual = hoje.year

        self.combo_mes.blockSignals(True)
        self.spin_ano.blockSignals(True)
        self.combo_mes.setCurrentIndex(self.mes_atual - 1)
        self.spin_ano.setValue(self.ano_atual)
        self.combo_mes.blockSignals(False)
        self.spin_ano.blockSignals(False)

        self.recarregar_mes()

    # -----------------------------------------------------------------------
    # Renderização da Grade
    # -----------------------------------------------------------------------
    def recarregar_mes(self):
        """Reconstrói a grade do calendário para o mês e ano selecionados."""
        # Limpa widgets anteriores da grade
        while self.grade_layout.count():
            item = self.grade_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        curso_filtro = self.combo_curso.currentText()
        curso_param = None if curso_filtro == "Todos os Cursos" else curso_filtro

        # Carrega dados do mês
        status_chamadas = db.status_chamadas_mes(self.ano_atual, self.mes_atual)

        # Pré-carrega turmas por dia da semana (0=Segunda ... 4=Sexta)
        turmas_por_dia = {}
        for d_idx, d_nome in enumerate(["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]):
            turmas_por_dia[d_idx] = db.turmas_por_dia_semana(d_nome, curso=curso_param)

        # Gera matriz do mês com calendar.monthcalendar (começa na segunda-feira)
        cal = calendar.Calendar(firstweekday=0)
        semanas = cal.monthdays2calendar(self.ano_atual, self.mes_atual)

        total_aulas_mes = 0
        total_realizadas_mes = 0

        for row_idx, semana in enumerate(semanas):
            for col_idx, (dia_num, dia_sem_idx) in enumerate(semana):
                if dia_num == 0:
                    # Dia de fora do mês (preenchimento visual sutil)
                    vazio = QFrame()
                    vazio.setStyleSheet("background: #141824; border: 1px dashed #22293C; border-radius: 10px;")
                    vazio.setMinimumHeight(115)
                    self.grade_layout.addWidget(vazio, row_idx, col_idx)
                    continue

                data_dia = date(self.ano_atual, self.mes_atual, dia_num)
                turmas_dia = turmas_por_dia.get(dia_sem_idx, [])

                # Contabiliza estatísticas
                data_str = data_dia.strftime("%Y-%m-%d")
                total_aulas_mes += len(turmas_dia)
                for t in turmas_dia:
                    key = f"{t['id']}_{data_str}"
                    if key in status_chamadas:
                        total_realizadas_mes += 1

                card = CardDiaCalendario(data_dia, turmas_dia, status_chamadas, eh_mes_atual=True)
                card.clicado.connect(self._abrir_dialog_dia)
                self.grade_layout.addWidget(card, row_idx, col_idx)

        # Atualiza o banner com resumo do mês
        pendentes_mes = total_aulas_mes - total_realizadas_mes
        nome_mes = MESES_PT[self.mes_atual - 1]
        pct = (total_realizadas_mes / total_aulas_mes * 100) if total_aulas_mes > 0 else 0

        texto_stats = (
            f"<b>{nome_mes} de {self.ano_atual}</b> — "
            f"Total de Aulas: <b>{total_aulas_mes}</b> | "
            f"<span style='color:#10B981; font-weight:bold;'>✓ Realizadas: {total_realizadas_mes}</span> | "
            f"<span style='color:#F59E0B; font-weight:bold;'>! Pendentes: {pendentes_mes}</span> | "
            f"Progresso: <b>{pct:.1f}%</b>"
        )
        self.lbl_stats_mes.setText(texto_stats)

    # -----------------------------------------------------------------------
    # Ação de Clique em um Dia
    # -----------------------------------------------------------------------
    def _abrir_dialog_dia(self, data_dia: date):
        dia_sem_idx = data_dia.weekday()
        if dia_sem_idx >= 5:
            # Fim de semana não tem turmas cadastradas por padrão
            QMessageBox.information(
                self, "Fim de Semana",
                f"O dia {data_dia.strftime('%d/%m/%Y')} é um {DIAS_SEMANA_NOMES[dia_sem_idx]}.\n"
                "Não há aulas regulares cadastradas aos sábados e domingos."
            )
            return

        nome_dia = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_sem_idx]
        curso_filtro = self.combo_curso.currentText()
        curso_param = None if curso_filtro == "Todos os Cursos" else curso_filtro
        turmas = db.turmas_por_dia_semana(nome_dia, curso=curso_param)

        status_chamadas = db.status_chamadas_mes(data_dia.year, data_dia.month)

        dlg = DialogEscolherTurmaDia(data_dia, turmas, status_chamadas, self)
        dlg.turma_selecionada.connect(self._redirecionar_para_chamada)
        dlg.exec()

    def _redirecionar_para_chamada(self, turma_id: str, data_str: str):
        """Emite o sinal global para navegar diretamente à aba de Chamada."""
        self.navegar_para_chamada.emit(turma_id, data_str)
