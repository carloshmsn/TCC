# Meu Controle — Demo de Controle Financeiro Pessoal

Projeto acadêmico de demonstração feito com Python, Flask, SQLite, HTML, CSS e JavaScript.

## Funcionalidades
- Dashboard com saldo, receitas e despesas do mês atual.
- Cadastro e exclusão de movimentações.
- Orçamentos mensais por categoria com barras de progresso e alertas.
- Metas financeiras com contribuições.
- Dados de demonstração inseridos automaticamente na primeira execução.

## Como executar

Requer Python 3.10 ou mais recente.

1. Abra o terminal na pasta do projeto.
2. (Opcional, recomendado) Crie e ative um ambiente virtual:
   - Windows: `python -m venv .venv` e `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` e `source .venv/bin/activate`
3. Instale as dependências: `pip install -r requirements.txt`
4. Inicie o servidor: `python app.py`
5. Abra `http://127.0.0.1:5000` no navegador.

O banco `financeiro.db` é criado automaticamente na pasta do projeto.

## Estrutura
- `app.py`: rotas, validação, consultas SQLite e regras do sistema.
- `templates/index.html`: estrutura das páginas e formulários.
- `static/style.css`: estilos e layout responsivo.
- `static/script.js`: pequenos comportamentos da interface.
- `requirements.txt`: dependências Python.

## Limitações importantes da demo
- É uma demonstração local para estudo, sem cadastro/login de usuários.
- Não está pronta para publicação na internet nem para armazenar dados financeiros reais.
- A chave Flask no código é apenas para desenvolvimento e deve ser substituída.
- As contribuições de metas são registradas separadamente e não alteram automaticamente o saldo das transações.
- O botão de adicionar orçamento atualiza o limite da categoria para o mês se já existir.

## Próximas melhorias possíveis
1. Adicionar autenticação segura e separar os dados por usuário.
2. Adicionar edição de transações.
3. Criar gráficos com Chart.js.
4. Criar testes automatizados para os cálculos financeiros.
5. Adicionar exportação de relatórios CSV.
