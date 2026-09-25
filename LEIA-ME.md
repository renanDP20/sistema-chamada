# 📋 Sistema de Chamada — Digital Makers + Robótica

Programa de controle de presença para turmas extracurriculares de **Informática Básica (Digital Makers)** e **Robótica**.
Funciona 100% offline, sem internet, sem login.

---

## 🚀 Primeira Instalação (só precisa fazer uma vez)

### Passo 1 — Instalar o Python

1. Acesse: **https://www.python.org/downloads/**
2. Clique no botão amarelo **"Download Python 3.x.x"**
3. Execute o instalador baixado
4. **IMPORTANTE:** Na tela do instalador, marque a caixa:
   - ✅ **"Add Python to PATH"** (ou "Add python.exe to PATH")
5. Clique em **"Install Now"**
6. Aguarde a instalação terminar e feche o instalador

### Passo 2 — Instalar e abrir o programa

1. Na pasta `sistema-chamada`, dê **duplo clique** em:
   **`INSTALAR_E_EXECUTAR.bat`**
2. Uma janela preta vai aparecer e instalar tudo automaticamente
3. O programa abrirá automaticamente ao final

---

## ▶️ Uso diário (após a primeira instalação)

Dê duplo clique em **`EXECUTAR.bat`**

---

## 📁 Estrutura das pastas

```
sistema-chamada/
  dados/              ← Banco de dados + backups automáticos
    backups/          ← Cópias de segurança do banco
  relatorios/         ← PDFs exportados ficam aqui
  INSTALAR_E_EXECUTAR.bat  ← Primeira instalação
  EXECUTAR.bat             ← Execução diária
  main.py, db.py, ...      ← Código do programa
```

---

## 🔄 Atualização Rápida (Tecla F5 ou Botão)

- **Tecla F5 ou Ctrl+R:** Pressione a qualquer momento para atualizar imediatamente a aba atual (Alunos, Chamada ou Estatísticas) sem precisar reiniciar o sistema.
- **Botão `🔄 Atualizar (F5)`:** Disponível no cabeçalho superior direito e na barra de ferramentas da aba de Alunos.

---

## 📥 Importação Estruturada por Turmas e Horários (.txt)

O sistema aceita arquivos `.txt` organizados por turmas com blocos delimitados por chaves `{ }`:

```txt
SEGUNDA_8H_9H {
NOME DO ALUNO;DATA DE NASCIMENTO;GÊNERO;
NOME DO ALUNO;DATA DE NASCIMENTO;GÊNERO;
}

SEGUNDA_9H_10H {
NOME DO ALUNO;DATA DE NASCIMENTO;GÊNERO;
}

TERCA_8H_9H {
NOME DO ALUNO;DATA DE NASCIMENTO;GÊNERO;
}
```

### Regras de importação:
1. O texto antes de `{` identifica o dia da semana e os horários (ex: `SEGUNDA_8H_9H`, `QUINTA_15H30_17H`).
2. Cada aluno fica em uma linha no formato: `Nome;Data de nascimento;Gênero;`.
3. Datas são convertidas automaticamente (ex: `01/08/2017`).
4. Gêneros são reconhecidos automaticamente (`Feminino` ou `Masculino`).
5. Todos os alunos dentro de `{ }` são vinculados com precisão àquela turma, sem misturar.
6. A interface exibe uma pré-visualização completa com a contagem de turmas e alunos encontrados antes de confirmar.
7. Compatibilidade garantida com arquivos de lista simples legados.

---

## 💾 Backup

- **Automático:** O sistema cria backup antes de importações e exclusões
- **Manual:** Clique no botão **"💾 Fazer backup agora"** no canto superior direito a qualquer momento
- Os backups ficam em `dados/backups/` com data e hora no nome


---

## 🔨 Gerar .exe (opcional — para distribuição sem Python)

Se quiser um `.exe` standalone que rode sem Python instalado:

```
pip install pyinstaller
pyinstaller build.spec
```

O executável ficará em `dist/SistemaChamada.exe`

---

## 📌 Turmas pré-configuradas

### Informática — Digital Makers (18 turmas)
- **Segunda, Quarta e Sexta** nos horários:
  - 8h–9h (Kids 8–11 anos)
  - 9h10–10h10 (Teens 12–15 anos)
  - 14h–15h (Kids)
  - 15h10–16h10 (Teens)
  - 16h20–17h20 (Kids)
  - 17h20–18h20 (Teens)

### Robótica — ARENA (8 turmas)
- **Terça e Quinta** nos horários:
  - 8h–9h30
  - 9h30–11h
  - 14h–15h30
  - 15h30–17h

## Créditos ❤️

- João Victor Pavanelli & Renan Denadai de Paula