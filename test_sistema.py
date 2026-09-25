"""
test_sistema.py — Testes automatizados do novo sistema de importação estruturada e atualização.
"""

import sys
import os
import shutil
import tempfile
from pathlib import Path

# Configura ambiente offscreen para testes Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import db
from PySide6.QtWidgets import QApplication

def test_parsing_headers():
    print("--- Teste 1: Parsing de cabeçalhos de turmas ---")
    casos = [
        ("SEGUNDA_8H_9H", "Segunda", "08:00", "09:00", "Informática"),
        ("SEGUNDA_9H_10H", "Segunda", "09:00", "10:00", "Informática"),
        ("TERCA_8H_9H", "Terça", "08:00", "09:00", "Robótica"),
        ("QUINTA_15H30_17H", "Quinta", "15:30", "17:00", "Robótica"),
        ("SEXTA_08H00_09H00", "Sexta", "08:00", "09:00", "Informática"),
        ("ROBOTICA_TERCA_08:00_09:30", "Terça", "08:00", "09:30", "Robótica"),
    ]
    for header, dia_esp, h_ini_esp, h_fim_esp, curso_esp in casos:
        info = db.parse_header_turma(header)
        assert info["dia_semana"] == dia_esp, f"Esperado {dia_esp}, obtido {info['dia_semana']}"
        assert info["horario_inicio"] == h_ini_esp, f"Esperado {h_ini_esp}, obtido {info['horario_inicio']}"
        assert info["horario_fim"] == h_fim_esp, f"Esperado {h_fim_esp}, obtido {info['horario_fim']}"
        assert info["curso"] == curso_esp, f"Esperado {curso_esp}, obtido {info['curso']}"
        print(f"  [OK] {header} -> {info['dia_semana']} {info['horario_inicio']}–{info['horario_fim']} ({info['curso']})")

def test_parsing_datas():
    print("\n--- Teste 2: Parsing de datas de nascimento ---")
    casos = [
        ("01/08/2017", "2017-08-01"),
        ("11/08/2016", "2016-08-11"),
        ("22/06/2016", "2016-06-22"),
        ("21/01/2011", "2011-01-21"),
        ("2011-01-21", "2011-01-21"),
        ("invalido", ""),
        ("", ""),
    ]
    for raw, esp in casos:
        res = db.parse_data_nascimento(raw)
        assert res == esp, f"Esperado {esp}, obtido {res}"
        print(f"  [OK] '{raw}' -> '{res}'")

def test_parse_arquivo_exemplo_usuario():
    print("\n--- Teste 3: Parsing do exemplo completo do usuário ---")
    conteudo_exemplo = """
SEGUNDA_8H_9H {
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
    parsed = db.parse_arquivo_importacao(conteudo_exemplo)
    assert parsed["formato"] == "estruturado"
    assert parsed["total_turmas"] == 3
    assert parsed["total_alunos"] == 7

    t1, t2, t3 = parsed["turmas"]
    assert t1["header_original"] == "SEGUNDA_8H_9H"
    assert len(t1["alunos"]) == 3
    assert t1["alunos"][0]["nome"] == "ANNA ALICE SANTOS FERREIRA DA SILVA"
    assert t1["alunos"][0]["data_nascimento_iso"] == "2017-08-01"
    assert t1["alunos"][0]["genero"] == "Feminino"

    assert t2["header_original"] == "SEGUNDA_9H_10H"
    assert len(t2["alunos"]) == 2
    assert t2["alunos"][0]["nome"] == "GABRIEL SILVA AFONSO"
    assert t2["alunos"][0]["genero"] == "Masculino"

    assert t3["header_original"] == "TERCA_8H_9H"
    assert len(t3["alunos"]) == 2
    assert t3["alunos"][1]["nome"] == "BRYAN FRANCO DE MELO"
    assert t3["alunos"][1]["data_nascimento_iso"] == "2012-04-24"
    assert t3["alunos"][1]["genero"] == "Masculino"

    print("  [OK] 3 turmas e 7 alunos identificados com sucesso e sem mistura!")

def test_executar_importacao():
    print("\n--- Teste 4: Executar importação no banco ---")
    conteudo_exemplo = """
SEGUNDA_8H_9H {
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
    parsed = db.parse_arquivo_importacao(conteudo_exemplo)
    turmas_config = []
    for t in parsed["turmas"]:
        t_id = t["turma_existente_id"]
        criar_nova = False
        nova_dados = None
        if not t_id:
            criar_nova = True
            nova_dados = {
                "id": t["info"]["id_sugerido"],
                "curso": t["info"]["curso"],
                "dia_semana": t["info"]["dia_semana"],
                "horario_inicio": t["info"]["horario_inicio"],
                "horario_fim": t["info"]["horario_fim"],
                "nome": t["info"]["nome_turma"],
            }
            t_id = t["info"]["id_sugerido"]
        turmas_config.append({
            "turma_id": t_id,
            "criar_turma_nova": criar_nova,
            "nova_turma_dados": nova_dados,
            "alunos": t["alunos"],
        })

    stats = db.executar_importacao_estruturada(turmas_config, atualizar_dados_cadastrais=True)
    print(f"  Stats importação: {stats}")
    assert stats["turmas_processadas"] == 3
    assert stats["alunos_criados"] + stats["alunos_vinculados"] >= 7

    # Verifica integridade dos alunos cadastrados
    aluno1 = db.get_aluno_por_nome("ANNA ALICE SANTOS FERREIRA DA SILVA")
    assert aluno1 is not None
    assert aluno1["data_nascimento"] == "2017-08-01"
    assert aluno1["genero"] == "Feminino"

    turmas_a1 = db.turmas_do_aluno(aluno1["id"])
    assert len(turmas_a1) >= 1
    print(f"  [OK] Aluno {aluno1['nome']} cadastrado e vinculado à turma {turmas_a1[0]['nome']}")

def test_janela_principal_e_f5():
    print("\n--- Teste 5: MainWindow, botão de Atualizar e atalho F5 ---")
    app = QApplication.instance() or QApplication(sys.argv)
    from main import MainWindow
    window = MainWindow()

    # Verifica botão de atualizar no Header
    assert hasattr(window.header, "btn_atualizar")
    assert "Atualizar (F5)" in window.header.btn_atualizar.text()
    assert not window.header.btn_atualizar.icon().isNull()

    # Verifica atalhos de teclado
    assert hasattr(window, "shortcut_f5")
    assert hasattr(window, "shortcut_ctrl_r")

    # Testa chamada de atualizar_pagina_atual em cada uma das abas
    for tab_idx in range(3):
        window.tabs.setCurrentIndex(tab_idx)
        window.atualizar_pagina_atual()
        print(f"  [OK] Aba {tab_idx} ({window.tabs.tabText(tab_idx)}) atualizada via atualizar_pagina_atual()")

    print("\n🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")

if __name__ == "__main__":
    db.init_db()
    test_parsing_headers()
    test_parsing_datas()
    test_parse_arquivo_exemplo_usuario()
    test_executar_importacao()
    test_janela_principal_e_f5()
