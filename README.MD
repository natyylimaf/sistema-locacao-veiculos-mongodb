# Sistema de Locação de Veículos 🚗

Projeto desenvolvido em grupo como trabalho académico da disciplina de **Banco de Dados** do curso de **Análise e Desenvolvimento de Sistemas**.

## 🎓 Informações académicas

- **Disciplina:** Banco de Dados
- **Curso:** Análise e Desenvolvimento de Sistemas
- **Turma:** 4DC1
- **Professor:** Howard Roatti

## 👥 Integrantes

- [Bryan Monteiro](https://github.com/anonimo172006)
- [Davi Pitangui](https://github.com/davzhin)
- [Gabryel Modesto](https://github.com/Gabryel-Modesto)
- [Nathália Lima](https://github.com/natyylimaf)
- [Walisson Pastori](https://github.com/WalissonP)

## 🎥 Apresentação do projeto

[Assistir ao vídeo de apresentação](https://youtu.be/hZdArTAy-lg?is=VViYpDGDII4-ZQxM)

## 📋 Descrição

O Sistema de Locação de Veículos é uma aplicação desenvolvida em Python, integrada ao **MongoDB**, responsável pelo gerenciamento das operações de uma locadora de veículos.

O sistema permite inserir, atualizar e excluir clientes, locadoras, categorias, veículos, funcionários, aluguéis e pagamentos, além de disponibilizar relatórios gerados por pipelines de agregação do MongoDB.

## 🛠 Tecnologias utilizadas

- Python 3.10+
- MongoDB
- PyMongo (`pymongo`)
- Docker e Docker Compose
- Ubuntu Linux
- Git e GitHub

## 📂 Estrutura do projeto

```text
sistema-locacao-veiculos-mongodb/
├── diagrams/       -> Diagramas do banco de dados e do sistema
├── src/
│   ├── conexion/   -> Conexão com o banco de dados
│   ├── controller/ -> Controladores responsáveis pelas operações CRUD
│   ├── model/      -> Classes e entidades do sistema
│   ├── reports/    -> Relatórios e pipelines de agregação no MongoDB
│   ├── utils/      -> Configurações, splash screen e utilitários
│   ├── principal.py
│   │               -> Arquivo principal da aplicação
│   └── requirements.txt
│                   -> Dependências do projeto
├── .gitignore      -> Arquivos ignorados pelo Git
├── LICENSE         -> Licença do projeto
├── PROMPTS.md      -> Registro do uso de ferramentas de IA
└── README.MD       -> Documentação do projeto