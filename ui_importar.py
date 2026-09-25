"""
ui_importar.py — Diálogo moderno e avançado de importação estruturada de alunos (.txt).
Suporta importação organizada por Turmas e Horários e formato simples de compatibilidade.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QCheckBox, QMessageBox, QFrame, QSplitter, QWidget,
    QAbstractItemView, QSizePolicy
)

import db
from icones import get_icon


def _calcular_idade(data_nasc_str: str) -> str:
    if not data_nasc_str:
        return "—"
    try:
        d = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
        hoje = date.today()
        anos = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
        return f"{anos} anos"
    except Exception:
        return "—"


class DialogImportarEstruturado(QDialog):
    importacao_concluida = Signal()

    def __init__(self, caminho_arquivo: str, parent=None, turma_pre_selecionada: str | None = None):
        super().__init__(parent)
        self.caminho_arquivo = caminho_arquivo
        self.turma_pre_selecionada = turma_pre_selecionada
        self.setWindowTitle("Importar Alunos — Estrutura por Turmas e Horários")
        self.setMinimumSize(960, 680)
        self.resize(1050, 720)
        self.setStyleSheet("""
            QDialog { background: #1A1F2E; color: #E0E6F0; }
            QLabel { color: #E0E6F0; font-family: 'Segoe UI', Arial, sans-serif; }
            QTableWidget {
                background: #252B3D; border: 1px solid #3A4560; border-radius: 8px;
                color: #E0E6F0; gridline-color: #2F3752; font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background: #3D3580; color: white; }
            QTableWidget::item:alternate { background: #1E2435; }
            QHeaderView::section {
                background: #1E2233; color: #9AA3C0; padding: 8px;
                border: none; font-size: 12px; font-weight: bold;
            }
            QComboBox {
                background: #1E2233; border: 1px solid #3A4560; border-radius: 6px;
                color: #E0E6F0; padding: 5px 8px; font-size: 12px; min-width: 240px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1E2233; color: #E0E6F0; selection-background-color: #6C63FF;
            }
            QCheckBox { color: #B0BAD0; font-size: 12px; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid #3A4560; background: #252B3D;
            }
            QCheckBox::indicator:checked {
                background: #6C63FF; border-color: #6C63FF;
            }
        """)

        self._dados_arquivo: dict = {}
        self._combos_turmas: list[QComboBox] = []
        self._carregar_dados()
        self._build_ui()

    def _carregar_dados(self):
        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
        except UnicodeDecodeError:
            with open(self.caminho_arquivo, "r", encoding="latin-1", errors="replace") as f:
                conteudo = f.read()

        self._dados_arquivo = db.parse_arquivo_importacao(conteudo)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header card
        hdr = QFrame()
        hdr.setStyleSheet("background: #252B3D; border-radius: 10px; border: 1px solid #3A4560;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 12, 16, 12)

        file_name = Path(self.caminho_arquivo).name
        formato = self._dados_arquivo.get("formato", "estruturado")
        formato_txt = "Organizado por Turmas e Horários" if formato == "estruturado" else "Lista simples de alunos"
        
        info_v = QVBoxLayout()
        t_lbl = QLabel(f"Arquivo: {file_name}")
        t_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E6F0;")
        f_lbl = QLabel(f"Formato: {formato_txt}")
        f_lbl.setStyleSheet("font-size: 12px; color: #6C63FF;")
        info_v.addWidget(t_lbl)
        info_v.addWidget(f_lbl)
        hdr_lay.addLayout(info_v)
        hdr_lay.addStretch()

        # Métricas rápidas
        tot_turmas = self._dados_arquivo.get("total_turmas", 0)
        tot_alunos = self._dados_arquivo.get("total_alunos", 0)
        novos_count = 0
        existentes_count = 0

        if formato == "estruturado":
            for t in self._dados_arquivo.get("turmas", []):
                for a in t.get("alunos", []):
                    if a.get("ja_cadastrado"):
                        existentes_count += 1
                    else:
                        novos_count += 1
        else:
            for a in self._dados_arquivo.get("alunos_simples", []):
                if a.get("ja_cadastrado"):
                    existentes_count += 1
                else:
                    novos_count += 1

        def _metric_box(num: int, label: str, cor: str = "#6C63FF"):
            box = QFrame()
            box.setStyleSheet("background: #1A1F2E; border-radius: 8px; border: 1px solid #3A4560; padding: 4px 10px;")
            blay = QVBoxLayout(box)
            blay.setContentsMargins(6, 4, 6, 4)
            blay.setSpacing(2)
            n_lbl = QLabel(str(num))
            n_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {cor};")
            n_lbl.setAlignment(Qt.AlignCenter)
            l_lbl = QLabel(label)
            l_lbl.setStyleSheet("font-size: 10px; color: #9AA3C0;")
            l_lbl.setAlignment(Qt.AlignCenter)
            blay.addWidget(n_lbl)
            blay.addWidget(l_lbl)
            return box

        if formato == "estruturado":
            hdr_lay.addWidget(_metric_box(tot_turmas, "Turmas", "#6C63FF"))
        hdr_lay.addWidget(_metric_box(tot_alunos, "Total Alunos", "#38BDF8"))
        hdr_lay.addWidget(_metric_box(novos_count, "Novos", "#4ADE80"))
        hdr_lay.addWidget(_metric_box(existentes_count, "Já Cadastrados", "#F59E0B"))

        layout.addWidget(hdr)

        # Divisão principal
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: #3A4560; height: 3px; }")

        todas_turmas_db = db.listar_turmas()

        if formato == "estruturado":
            # Painel superior: Turmas encontradas
            top_widget = QWidget()
            top_lay = QVBoxLayout(top_widget)
            top_lay.setContentsMargins(0, 0, 0, 0)
            top_lay.setSpacing(6)

            lbl_t = QLabel("Turmas Encontradas no Arquivo (Selecione uma linha para ver os alunos abaixo):")
            lbl_t.setStyleSheet("font-size: 12px; font-weight: bold; color: #9AA3C0;")
            top_lay.addWidget(lbl_t)

            self.tabela_turmas = QTableWidget()
            self.tabela_turmas.setColumnCount(5)
            self.tabela_turmas.setHorizontalHeaderLabels([
                "Bloco no Arquivo", "Dia / Horário", "Destino no Sistema", "Alunos", "Situação"
            ])
            self.tabela_turmas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.tabela_turmas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tabela_turmas.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.tabela_turmas.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.tabela_turmas.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.tabela_turmas.setAlternatingRowColors(True)
            self.tabela_turmas.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tabela_turmas.setSelectionMode(QAbstractItemView.SingleSelection)
            self.tabela_turmas.verticalHeader().setVisible(False)

            turmas_list = self._dados_arquivo.get("turmas", [])
            self.tabela_turmas.setRowCount(len(turmas_list))
            self._combos_turmas = []

            for row_i, t in enumerate(turmas_list):
                info = t["info"]
                # 1. Bloco original
                item_header = QTableWidgetItem(t["header_original"])
                item_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.tabela_turmas.setItem(row_i, 0, item_header)

                # 2. Dia / Horário detectado
                h_desc = f"{info['dia_semana']}, {info['horario_inicio']} às {info['horario_fim']}"
                self.tabela_turmas.setItem(row_i, 1, QTableWidgetItem(h_desc))

                # 3. Combo de destino
                combo = QComboBox()
                # Opção vinculada existente se encontrou
                if t.get("turma_existente_id"):
                    combo.addItem(f"Vincular: {t['turma_existente_nome']}", t["turma_existente_id"])

                # Opção de criar nova turma específica
                nome_nova = f"Criar nova turma: {info['nome_turma']}"
                combo.addItem(nome_nova, f"__NOVA__{t['header_original']}")

                # Todas as outras turmas existentes
                for tdb in todas_turmas_db:
                    if tdb["id"] != t.get("turma_existente_id"):
                        combo.addItem(f"Vincular a: {tdb['nome']}", tdb["id"])

                self._combos_turmas.append(combo)
                self.tabela_turmas.setCellWidget(row_i, 2, combo)

                # 4. Total de alunos
                qtd_alunos = len(t.get("alunos", []))
                item_qtd = QTableWidgetItem(f"{qtd_alunos} aluno(s)")
                item_qtd.setTextAlignment(Qt.AlignCenter)
                self.tabela_turmas.setItem(row_i, 3, item_qtd)

                # 5. Detalhes de novos vs existentes
                novos_t = sum(1 for a in t.get("alunos", []) if not a.get("ja_cadastrado"))
                exist_t = qtd_alunos - novos_t
                status_str = f"{novos_t} novo(s)" + (f", {exist_t} existente(s)" if exist_t else "")
                item_status = QTableWidgetItem(status_str)
                item_status.setForeground(QColor("#4ADE80") if novos_t == qtd_alunos else QColor("#F59E0B"))
                self.tabela_turmas.setItem(row_i, 4, item_status)

                self.tabela_turmas.setRowHeight(row_i, 38)

            self.tabela_turmas.itemSelectionChanged.connect(self._on_turma_selecionada)
            top_lay.addWidget(self.tabela_turmas)
            splitter.addWidget(top_widget)

            # Painel inferior: Alunos da turma selecionada
            bottom_widget = QWidget()
            bottom_lay = QVBoxLayout(bottom_widget)
            bottom_lay.setContentsMargins(0, 6, 0, 0)
            bottom_lay.setSpacing(6)

            self.lbl_alunos_titulo = QLabel("Alunos da Turma Selecionada:")
            self.lbl_alunos_titulo.setStyleSheet("font-size: 12px; font-weight: bold; color: #9AA3C0;")
            bottom_lay.addWidget(self.lbl_alunos_titulo)

            self.tabela_alunos = QTableWidget()
            self.tabela_alunos.setColumnCount(5)
            self.tabela_alunos.setHorizontalHeaderLabels([
                "Nome Completo", "Nascimento", "Idade", "Gênero", "Status no Sistema"
            ])
            self.tabela_alunos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tabela_alunos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tabela_alunos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.tabela_alunos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.tabela_alunos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.tabela_alunos.setAlternatingRowColors(True)
            self.tabela_alunos.verticalHeader().setVisible(False)
            bottom_lay.addWidget(self.tabela_alunos)
            splitter.addWidget(bottom_widget)

            layout.addWidget(splitter, 1)

            # Seleciona a primeira turma por padrão
            if self.tabela_turmas.rowCount() > 0:
                self.tabela_turmas.selectRow(0)

        else:
            # Formato simples legado
            simples_widget = QWidget()
            s_lay = QVBoxLayout(simples_widget)
            s_lay.setContentsMargins(0, 0, 0, 0)
            s_lay.setSpacing(8)

            # Seletor de turma de destino para a lista simples
            dest_lay = QHBoxLayout()
            dest_lay.addWidget(QLabel("Vincular todos os alunos à turma:"))
            self.combo_simples_turma = QComboBox()
            self.combo_simples_turma.addItem("— Apenas cadastrar (sem turma inicial) —", "")
            for tdb in todas_turmas_db:
                self.combo_simples_turma.addItem(tdb["nome"], tdb["id"])
            if self.turma_pre_selecionada:
                idx = self.combo_simples_turma.findData(self.turma_pre_selecionada)
                if idx >= 0:
                    self.combo_simples_turma.setCurrentIndex(idx)
            dest_lay.addWidget(self.combo_simples_turma)
            dest_lay.addStretch()
            s_lay.addLayout(dest_lay)

            self.tabela_alunos = QTableWidget()
            self.tabela_alunos.setColumnCount(5)
            self.tabela_alunos.setHorizontalHeaderLabels([
                "Nome Completo", "Nascimento", "Idade", "Gênero", "Status no Sistema"
            ])
            self.tabela_alunos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tabela_alunos.setAlternatingRowColors(True)
            self.tabela_alunos.verticalHeader().setVisible(False)

            alunos_s = self._dados_arquivo.get("alunos_simples", [])
            self.tabela_alunos.setRowCount(len(alunos_s))
            for row_i, a in enumerate(alunos_s):
                self._preencher_linha_aluno(row_i, a)

            s_lay.addWidget(self.tabela_alunos)
            layout.addWidget(simples_widget, 1)

        # Opções inferiores
        opt_lay = QHBoxLayout()
        self.check_backup = QCheckBox("Fazer backup de segurança antes de importar")
        self.check_backup.setChecked(True)
        opt_lay.addWidget(self.check_backup)

        self.check_atualizar = QCheckBox("Atualizar data de nascimento e gênero de alunos já existentes")
        self.check_atualizar.setChecked(True)
        opt_lay.addWidget(self.check_atualizar)

        opt_lay.addStretch()
        layout.addLayout(opt_lay)

        # Botões de ação
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background: #252B3D; color: #9AA3C0; border: 1px solid #3A4560;
                border-radius: 8px; padding: 9px 20px; font-size: 13px;
            }
            QPushButton:hover { background: #3A4560; color: #E0E6F0; }
        """)
        btn_cancelar.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancelar)

        tot_al = self._dados_arquivo.get("total_alunos", 0)
        self.btn_confirmar = QPushButton(f"Confirmar Importação ({tot_al} alunos)")
        self.btn_confirmar.setIcon(get_icon("importar"))
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #059669,stop:1 #10B981);
                color: white; border-radius: 8px; padding: 9px 24px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #10B981; }
        """)
        self.btn_confirmar.clicked.connect(self._executar_importacao)
        btn_bar.addWidget(self.btn_confirmar)

        layout.addLayout(btn_bar)

    def _on_turma_selecionada(self):
        sel_rows = self.tabela_turmas.selectionModel().selectedRows()
        if not sel_rows:
            return
        row_idx = sel_rows[0].row()
        turmas_list = self._dados_arquivo.get("turmas", [])
        if row_idx < 0 or row_idx >= len(turmas_list):
            return

        t = turmas_list[row_idx]
        alunos = t.get("alunos", [])
        self.lbl_alunos_titulo.setText(
            f"👤 Alunos de [{t['header_original']}] — {len(alunos)} aluno(s) encontrado(s):"
        )

        self.tabela_alunos.setRowCount(len(alunos))
        for i, a in enumerate(alunos):
            self._preencher_linha_aluno(i, a)

    def _preencher_linha_aluno(self, row: int, a: dict):
        # 1. Nome
        item_nome = QTableWidgetItem(a["nome"])
        item_nome.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.tabela_alunos.setItem(row, 0, item_nome)

        # 2. Nascimento
        nasc_display = a.get("data_nascimento_raw") or "—"
        if a.get("data_nascimento_iso"):
            try:
                d = datetime.strptime(a["data_nascimento_iso"], "%Y-%m-%d")
                nasc_display = d.strftime("%d/%m/%Y")
            except Exception:
                pass
        item_nasc = QTableWidgetItem(nasc_display)
        item_nasc.setTextAlignment(Qt.AlignCenter)
        self.tabela_alunos.setItem(row, 1, item_nasc)

        # 3. Idade
        idade = _calcular_idade(a.get("data_nascimento_iso") or "")
        item_idade = QTableWidgetItem(idade)
        item_idade.setTextAlignment(Qt.AlignCenter)
        self.tabela_alunos.setItem(row, 2, item_idade)

        # 4. Gênero
        gen = a.get("genero") or "Não informado"
        item_gen = QTableWidgetItem(gen)
        item_gen.setTextAlignment(Qt.AlignCenter)
        self.tabela_alunos.setItem(row, 3, item_gen)

        # 5. Status
        ja = a.get("ja_cadastrado")
        status_txt = "Já cadastrado (vincular)" if ja else "Novo aluno"
        item_status = QTableWidgetItem(status_txt)
        item_status.setForeground(QColor("#F59E0B") if ja else QColor("#4ADE80"))
        item_status.setTextAlignment(Qt.AlignCenter)
        self.tabela_alunos.setItem(row, 4, item_status)

        self.tabela_alunos.setRowHeight(row, 34)

    def _executar_importacao(self):
        formato = self._dados_arquivo.get("formato", "estruturado")
        atualizar_cadastrais = self.check_atualizar.isChecked()

        if self.check_backup.isChecked():
            db.fazer_backup("antes_importacao_assistida")

        if formato == "estruturado":
            turmas_list = self._dados_arquivo.get("turmas", [])
            turmas_config = []

            for row_i, t in enumerate(turmas_list):
                combo = self._combos_turmas[row_i]
                turma_val = combo.currentData()
                info = t["info"]

                criar_nova = False
                nova_turma_dados = None

                if str(turma_val).startswith("__NOVA__"):
                    criar_nova = True
                    nova_turma_dados = {
                        "id": info["id_sugerido"],
                        "curso": info["curso"],
                        "dia_semana": info["dia_semana"],
                        "horario_inicio": info["horario_inicio"],
                        "horario_fim": info["horario_fim"],
                        "nome": info["nome_turma"],
                    }
                    turma_id = info["id_sugerido"]
                else:
                    turma_id = str(turma_val)

                turmas_config.append({
                    "turma_id": turma_id,
                    "criar_turma_nova": criar_nova,
                    "nova_turma_dados": nova_turma_dados,
                    "alunos": t.get("alunos", []),
                })

            stats = db.executar_importacao_estruturada(turmas_config, atualizar_cadastrais)

            # Mensagem de relatório
            detalhes_txt = []
            for d in stats.get("detalhes_turmas", []):
                detalhes_txt.append(f"• {d['turma_nome']}: {d['total']} aluno(s) ({d['criados']} novos, {d['vinculados']} vinculados)")

            msg = (
                f"<b>Importação concluída com sucesso!</b><br><br>"
                f"<b>Turmas processadas:</b> {stats['turmas_processadas']}<br>"
                f"<b>Novos alunos criados:</b> {stats['alunos_criados']}<br>"
                f"<b>Alunos vinculados/atualizados:</b> {stats['alunos_vinculados']}<br><br>"
                f"<b>Detalhamento por turma:</b><br>"
                + "<br>".join(detalhes_txt)
            )

            QMessageBox.information(self, "Importação Concluída", msg)

        else:
            # Importação simples
            alunos_s = self._dados_arquivo.get("alunos_simples", [])
            turma_dest = self.combo_simples_turma.currentData()

            criados = 0
            vinculados = 0

            with db.get_conn() as conn:
                for a in alunos_s:
                    nome = a["nome"]
                    data_nasc = a.get("data_nascimento_iso") or ""
                    genero = a.get("genero") or ""
                    existente = db.get_aluno_por_nome(nome)

                    if existente:
                        aid = existente["id"]
                        if atualizar_cadastrais:
                            dn = data_nasc if data_nasc else existente["data_nascimento"]
                            gn = genero if genero else existente["genero"]
                            conn.execute("UPDATE alunos SET data_nascimento=?, genero=? WHERE id=?", (dn, gn, aid))
                        if turma_dest:
                            conn.execute("INSERT OR IGNORE INTO aluno_turma (aluno_id, turma_id) VALUES (?,?)", (aid, turma_dest))
                            vinculados += 1
                    else:
                        cur = conn.execute(
                            "INSERT INTO alunos (nome, data_nascimento, genero, curso) VALUES (?,?,?,?)",
                            (nome, data_nasc, genero, "Informática")
                        )
                        new_id = cur.lastrowid
                        if turma_dest:
                            conn.execute("INSERT OR IGNORE INTO aluno_turma (aluno_id, turma_id) VALUES (?,?)", (new_id, turma_dest))
                        criados += 1
                conn.commit()

            msg = (
                f"✅ <b>Importação simples concluída!</b><br><br>"
                f"<b>Novos alunos cadastrados:</b> {criados}<br>"
                f"<b>Alunos já cadastrados vinculados:</b> {vinculados}"
            )
            QMessageBox.information(self, "Importação Concluída 🎉", msg)

        self.importacao_concluida.emit()
        self.accept()
