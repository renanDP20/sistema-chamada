<div align="center">

  <img src="app_icon.png" alt="Logo Sistema de Chamada" width="120" height="120" />

  # 📋 Sistema de Chamada — ABDA
  ### *Digital Makers (Informática Básica) & ARENA (Robótica)*

  <p align="center">
    <b>Sistema desktop moderno, 100% offline e independente para gestão escolar, controle de presença, histórico de ocorrências e relatórios estatísticos em PDF.</b>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
    <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt)-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6 Qt" />
    <img src="https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite3" />
    <img src="https://img.shields.io/badge/PDF%20Engine-ReportLab-FF6F00?style=for-the-badge" alt="ReportLab" />
    <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows" />
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License MIT" />
  </p>

</div>

---

## 📌 Visão Geral

O **Sistema de Chamada ABDA** é um aplicativo desktop projetado para simplificar e automatizar o controle diário de turmas extracurriculares de **Informática Básica (Digital Makers)** e **Robótica (ARENA)**.

Desenvolvido para operar **totalmente offline** — sem necessidade de internet, logins em nuvem ou configurações complexas de servidores —, o sistema garante velocidade instantânea, privacidade integral dos dados e portabilidade completa em pendrives ou computadores locais.

---

## ✨ Funcionalidades Principais

### 🎓 1. Gestão de Alunos
- Cadastro completo: Nome, Data de Nascimento, Idade calculada dinamicamente, Gênero e Observações individuais.
- **Ordenação Dinâmica de Colunas:** Clique nos cabeçalhos (`Nome`, `Idade`, `Gênero`, `Curso`, `Turmas`) para ordenar em ordem crescente/decrescente com indicadores visuais (`▲`, `▼`).
- **Filtros e Busca em Tempo Real:** Pesquisa instantânea por nome e filtragem por turma específica.
- Histórico do aluno com contagem de presenças, faltas e percentual de frequência.

### 📅 2. Calendário Interativo & Status de Chamadas
- Visão mensal em grade estruturada (Segunda a Sexta com turmas ativas).
- **Indicadores de Status:**
  - ⚠️ Marcador de chamadas pendentes no dia.
  - ✅ Indicador visual de chamadas realizadas e consolidadas.
- **Painel Interativo:** Clique em qualquer dia para abrir as turmas daquela data e ir diretamente para a realização da chamada.
- Métricas mensais no topo: Total de aulas, chamadas realizadas, pendentes e taxa de conclusão do mês.

### 📝 3. Chamada e Controle de Frequência
- Lançamento rápido de presença/ausência com botões de 1 clique: *"Marcar Todos Presentes"* e *"Marcar Todos Ausentes"*.
- Histórico completo de chamadas anteriores com permissão de edição e atualização.
- Atualização instantânea com atalho **`F5`** / **`Ctrl+R`**.

### ⚠️ 4. Central de Ocorrências
- Registro disciplinar e pedagógico de alunos.
- **Campo Inteligente com Autocompletar (`QCompleter`):** Sugere nomes de alunos cadastrados enquanto você digita.
- Histórico com data, nome, descrição detalhada e exclusão segura.

### 📊 5. Estatísticas Avançadas & Relatórios em PDF
- Resumo executivo na tela com cartões visuais e tabelas consolidadas.
- **Geração de Relatório Oficial em PDF (via ReportLab):**
  - Carga horária mensal por curso (horas e minutos).
  - Tabela de cursos e turmas ativas no mês.
  - Frequência e presença consolidada por curso.
  - **Frequência detalhada por Faixa Etária e Sexo.**
  - **Quantidade absoluta de alunos matriculados por Idade e Sexo.**
  - Comparativo quadrimestral (1º, 2º e 3º Quadrimestres).
  - Cabeçalho institucional com numeração automática de páginas e rodapé formal.

### 🔄 6. Importação e Exportação Estruturada (.txt)
- Exportação e importação simétrica de turmas e alunos com sintaxe legível em blocos:
  ```txt
  SEGUNDA_8H_9H {
  ALUNO EXEMPLO;01/05/2012;Masculino;
  }
  ```
- Pré-visualização com validação antes de importar para o banco.

### 💾 7. Persistência e Backups Automáticos
- Banco de dados SQLite local (`dados/dados.db`).
- Backups automáticos gerados a cada importação ou operação crítica.
- Botão manual de backup com 1 clique (`dados/backups/`).

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| **[Python 3.11+](https://www.python.org/)** | Linguagem principal do ecossistema |
| **[PySide6 (Qt for Python)](https://doc.qt.io/qtforpython/)** | Interface gráfica rica, moderna e responsiva |
| **[SQLite3](https://www.sqlite.org/)** | Armazenamento de dados relacional embutido e veloz |
| **[ReportLab](https://www.reportlab.com/)** | Renderização programática de documentos PDF |
| **[PyInstaller](https://pyinstaller.org/)** | Compilação em executável standalone (`.exe`) para Windows |

---

## 📂 Estrutura do Projeto

```text
sistema-chamada/
├── icones/                   # Ícones vetoriais profissionais (SVG)
├── dados/                    # Banco de dados SQLite permanente
│   ├── dados.db              # Base de dados local
│   └── backups/              # Cópias de segurança automáticas
├── relatorios/               # PDFs exportados pelo sistema
├── main.py                   # Ponto de entrada e janela principal (MainWindow)
├── db.py                     # Camada de dados, esquemas SQLite e consultas
├── icones.py                 # Gerenciador de ícones SVG e renderização
├── ui_alunos.py              # Interface da aba de Alunos e ordenação
├── ui_calendario.py          # Interface da aba de Calendário mensal
├── ui_chamada.py             # Interface da aba de Chamada e presença
├── ui_estatisticas.py        # Interface de Estatísticas e gerador de PDF
├── ui_ocorrencias.py         # Interface da aba de Ocorrências (com autocompletar)
├── ui_importar.py            # Diálogo de importação estruturada (.txt)
├── app_icon.ico              # Ícone do aplicativo multi-resolução para Windows
├── app_icon.png              # Logotipo em alta resolução (256x256)
├── build.spec                # Configuração de empacotamento PyInstaller
├── requirements.txt          # Dependências do projeto
├── LICENSE                   # Licença MIT
└── README.md                 # Documentação oficial
```

---

## 🚀 Como Executar

### Opção 1: Executável Standalone (.exe) — Recomendado para Usuários Finais
Não necessita de Python instalado na máquina:
1. Baixe a versão compilada em [Releases](../../releases) ou utilize o executável gerado na pasta `dist/SistemaChamada.exe`.
2. Dê duplo clique em **`SistemaChamada.exe`**.

---

### Opção 2: A Partir do Código-Fonte (Python)

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/renanDP20/sistema-chamada.git
   cd sistema-chamada
   ```

2. **Crie e ative um ambiente virtual (opcional, recomendado):**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o programa:**
   ```bash
   python main.py
   ```

---

## 🔨 Como Compilar o Executável (.exe)

O projeto possui configuração completa para gerar o `.exe` standalone através do PyInstaller:

1. Instale o PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Execute a compilação:
   ```bash
   python -m PyInstaller build.spec --clean --noconfirm
   ```
3. O executável standalone será criado em:
   ```text
   dist/SistemaChamada.exe
   ```

---

## 👥 Autores & Colaboradores

Projeto desenvolvido em colaboração por:

<table align="center">
  <tr>
    <td align="center" width="220">
      <a href="https://github.com/renanDP20">
        <img src="https://github.com/renanDP20.png" width="110px;" alt="Renan Denadai de Paula" style="border-radius: 50%;"/><br />
        <sub><b>Renan Denadai de Paula</b></sub>
      </a>
      <br />
      <sub>Desenvolvedor</sub>
    </td>
    <td align="center" width="220">
      <a href="https://github.com/vitinhodeveloper">
        <img src="https://github.com/vitinhodeveloper.png" width="110px;" alt="João Victor Pavanelli" style="border-radius: 50%;"/><br />
        <sub><b>João Victor Pavanelli</b></sub>
      </a>
      <br />
      <sub>Desenvolvedor</sub>
    </td>
  </tr>
</table>

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE) — veja o arquivo [`LICENSE`](LICENSE) para mais detalhes.
