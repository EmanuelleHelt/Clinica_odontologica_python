Clinica Odontológica - funcionamento
Este repositório contém o sistema de gerenciamento para a sua clínica, desenvolvido com o intuito de ser funcional, minimamente estético.

Pré-requisitos
Você precisa ter o Python 3.10 ou superior instalado na sua máquina. Se você não sabe verificar sua versão, digite python --version no seu terminal.

Instalação
O projeto depende estritamente do framework Flask para servir a interface web e gerenciar as rotas. Para instalar a dependência necessária, execute o comando abaixo no diretório raiz do projeto:

> pip install flask


Como rodar o sistema:

Abra o seu terminal na pasta do projeto.

Execute o servidor:

> python app.py

O terminal mostrará um endereço (geralmente http://127.0.0.1:5000/). Copie e cole no seu navegador.

Estrutura do Banco de Dados
O sistema utiliza SQLite (banco de dados em arquivo).

Ao iniciar o programa pela primeira vez, ele criará automaticamente o arquivo clinica_real.db se não existir.