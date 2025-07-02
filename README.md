# 🤖 Assistente Financeiro para WhatsApp

![Status do Projeto](https://img.shields.io/badge/status-em_desenvolvimento-yellow)
![Linguagem](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Framework](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![Database](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)

> Um chatbot para WhatsApp focado em controle financeiro pessoal, permitindo registrar despesas (à vista ou parceladas) e receitas de forma rápida e intuitiva, diretamente da conversa.

<br>
## 🎯 Funcionalidades Principais

*   **💸 Registro de Gastos:** Adicione despesas com valor, categoria, loja, forma de pagamento e conta.
*   **💳 Lançamento de Parcelas:** Reconhece compras parceladas e lança as parcelas futuras automaticamente.
*   **💰 Registro de Receitas:** Adicione entradas de dinheiro de forma simples.
*   **📈 Consultas Rápidas:** Veja os últimos gastos, gastos do dia ou do mês atual.
*   **📊 Resumos Inteligentes:** Obtenha resumos de gastos por:
    *   Categoria
    *   Forma de Pagamento
    *   Conta (Cartão de Crédito)
*   **💬 Interface Conversacional:** Interaja usando linguagem natural.

<br>

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído utilizando as seguintes tecnologias:

*   **Linguagem Principal:** [Python](https://www.python.org/)
*   **Framework Web:** [Flask](https://flask.palletsprojects.com/)
*   **API de Mensagens:** [Twilio](https://www.twilio.com/)
*   **Banco de Dados:** [SQLite 3](https://www.sqlite.org/index.html)
*   **Túnel para Desenvolvimento Local:** [Ngrok](https://ngrok.com/)

<br>

## 🚀 Como Executar o Projeto

Siga os passos abaixo para rodar o projeto em sua máquina.

**Pré-requisitos:**
*   [Python 3.x](https://www.python.org/downloads/)
*   [Git](https://git-scm.com/downloads)
*   Uma conta na [Twilio](https://www.twilio.com/) com o Sandbox do WhatsApp ativado.
*   [Ngrok](https://ngrok.com/download) para expor sua aplicação localmente.

---

**1. Clone o repositório:**
```bash
git clone https://github.com/RegianeHonorato/assistente-financeiro-chatbot.git
