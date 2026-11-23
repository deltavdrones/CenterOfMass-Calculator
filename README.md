# CM-Calc — Calculadora de Centro de Massa

Ferramenta para calcular e visualizar o centro de massa (CM) de montagens mecânicas projetadas no Autodesk Fusion 360.

O projeto combina:
- **Fusion 360 + Python API:** extração das coordenadas e volumes dos componentes/corpos selecionados.
- **Python:** cadastro das massas, cálculo do centro de massa e visualização 3D.
- **Excel:** banco de dados de massas dos componentes.
- **CSV:** arquivo intermediário com posições e volumes.

> Esta versão migra o processamento que antes era feito em MATLAB para Python. Os arquivos MATLAB originais foram preservados em `legacy_matlab/` como referência.

## 1. Estrutura do projeto

```text
CM-Calc-Python/
├── CM2CSV/
│   ├── CM2CSV.py
│   ├── CM2CSV.manifest
│   └── ScriptIcon.svg
├── src/
│   ├── att_massas.py
│   └── main.py
├── data/
│   ├── componentes_posicao.csv
│   └── banco_de_massas.xlsx
├── legacy_matlab/
│   ├── att_massas.m
│   └── main.m
├── .gitignore
├── README.md
└── requirements.txt
```

### Função de cada arquivo

| Arquivo | Responsabilidade |
|---|---|
| `CM2CSV/CM2CSV.py` | Executa dentro do Fusion 360 e exporta os dados geométricos. |
| `CM2CSV/CM2CSV.manifest` | Metadados necessários para registrar o script no Fusion 360. |
| `CM2CSV/ScriptIcon.svg` | Ícone do script do Fusion 360. |
| `src/att_massas.py` | Cadastra massas de componentes novos e atualiza o Excel. |
| `src/main.py` | Cruza posições e massas, calcula o CM e gera o gráfico 3D. |
| `data/componentes_posicao.csv` | Posições X, Y, Z e volumes exportados do Fusion 360. |
| `data/banco_de_massas.xlsx` | Banco de massas em gramas. |
| `legacy_matlab/` | Versões MATLAB originais, preservadas para consulta e comparação. |
| `requirements.txt` | Bibliotecas Python necessárias. |

## 2. Requisitos

- Autodesk Fusion 360 (para gerar/atualizar o CSV).
- Python 3.10 ou superior (recomendado).
- Windows, Linux ou macOS para executar os módulos Python.
- Excel ou aplicativo compatível com `.xlsx` para consultar o banco de massas (não é necessário ter Excel instalado para o Python ler/escrever o arquivo).

## 3. Instalação no Windows (CMD)

Abra o CMD na pasta raiz do projeto.

### 3.1. Criar ambiente virtual

```cmd
python -m venv .venv
```

### 3.2. Ativar ambiente virtual

```cmd
.venv\Scripts\activate
```

### 3.3. Instalar dependências

```cmd
python -m pip install -r requirements.txt
```

Bibliotecas utilizadas:
- `numpy`: operações numéricas e cálculo vetorizado.
- `pandas`: leitura, cruzamento e manipulação das tabelas.
- `openpyxl`: leitura e escrita de arquivos Excel `.xlsx`.
- `matplotlib`: visualização tridimensional e interação com os pontos.

## 4. Instalar o script no Fusion 360

1. Abra o Autodesk Fusion 360.
2. Abra **Scripts and Add-ins** (atalho `Shift + S`).
3. Na aba **Scripts**, clique no botão `+` para adicionar um script existente.
4. Selecione a pasta `CM2CSV` deste repositório.
5. Confirme a seleção. O script `CM2CSV` deverá aparecer na lista.
6. Selecione o script e clique em **Run**.

### Exportar a montagem

1. Abra a montagem no Fusion 360.
2. Selecione os componentes ou corpos que devem entrar no cálculo.
3. Execute `CM2CSV`.
4. O script grava/atualiza `data/componentes_posicao.csv`.

**Atenção:** a exportação substitui o CSV anterior. Selecione todos os itens que devem participar do cálculo em cada exportação. Feche o CSV no Excel antes de executar o script.

O exportador grava o CSV em UTF-8 com BOM para preservar caracteres acentuados.

## 5. Fluxo de execução em Python

Execute os comandos a partir da pasta raiz do projeto.

### Etapa 1 — Atualizar o banco de massas

```cmd
python src/att_massas.py
```

O programa:
1. Lê `data/componentes_posicao.csv`.
2. Lê `data/banco_de_massas.xlsx`.
3. Compara os nomes dos componentes.
4. Solicita a massa, em gramas, dos componentes ainda não cadastrados.
5. Se for digitado `PLA`, estima a massa com base no volume e na densidade configurada.
6. Atualiza o arquivo Excel.

Densidade configurada para PLA:

\[
\rho_{PLA} = 0{,}00124\ \text{g/mm}^3
\]

A massa é estimada por:

\[
m = \rho \cdot V
\]

onde `V` é o volume exportado pelo Fusion em mm³. A massa calculada é uma estimativa: a densidade efetiva de uma peça impressa depende de material, paredes, preenchimento e parâmetros de fabricação.

Se todos os componentes já estiverem cadastrados, o programa informa isso e não altera o banco.

### Etapa 2 — Calcular e visualizar o centro de massa

```cmd
python src/main.py
```

O programa:
1. Lê as posições do CSV.
2. Lê as massas do Excel.
3. Verifica se todos os componentes exportados possuem massa cadastrada.
4. Calcula a massa total.
5. Calcula as coordenadas X, Y e Z do centro de massa.
6. Imprime os resultados no terminal.
7. Abre um gráfico 3D interativo.

No gráfico:
- Azul: componentes.
- Cinza: centro de massa.
- Vermelho: origem.
- Clique em um ponto azul para consultar nome, massa e posição do componente.
- Use o mouse para girar e inspecionar a montagem.

## 6. Equações utilizadas

A massa total é:

\[
M = \sum_{i=1}^{n} m_i
\]

As coordenadas do centro de massa são:

\[
X_{CM} = \frac{\sum_{i=1}^{n} m_i x_i}{\sum_{i=1}^{n}m_i}
\]

\[
Y_{CM} = \frac{\sum_{i=1}^{n} m_i y_i}{\sum_{i=1}^{n}m_i}
\]

\[
Z_{CM} = \frac{\sum_{i=1}^{n} m_i z_i}{\sum_{i=1}^{n}m_i}
\]

O código preserva a convenção do `main.m` original, invertendo o sinal das coordenadas Y antes do cálculo e da visualização.

## 7. Unidades e convenções

| Grandeza | Unidade |
|---|---|
| Coordenadas X, Y, Z | mm |
| Volume | mm³ |
| Massa | g |
| Densidade do PLA | g/mm³ |

O script do Fusion converte as coordenadas de centímetros para milímetros (multiplicação por 10) e o volume de cm³ para mm³ (multiplicação por 1000).

O centro de massa de cada componente/corpo é usado como ponto representativo, ponderado pela massa informada no banco. O resultado depende da qualidade da geometria, da seleção feita no Fusion e da massa cadastrada.

## 8. Atualizar o banco de massas manualmente

O arquivo `data/banco_de_massas.xlsx` deve conter duas colunas:

| nome | massa |
|---|---:|
| Nome do componente | Massa em gramas |

Os nomes precisam corresponder aos nomes exportados pelo Fusion. Evite nomes duplicados.

## 9. Solução de problemas

**Erro: arquivo CSV não encontrado**
- Execute primeiro o script `CM2CSV` no Fusion.
- Verifique se o arquivo está em `data/componentes_posicao.csv`.

**Erro: banco de massas não encontrado**
- Verifique se `data/banco_de_massas.xlsx` existe.
- Se ainda não existir, execute `src/att_massas.py` para iniciar o cadastro.

**Há componentes sem massa cadastrada**
- Execute `python src/att_massas.py`.
- Cadastre os componentes solicitados.
- Execute novamente `python src/main.py`.

**Erro ao salvar o Excel**
- Feche `banco_de_massas.xlsx` caso esteja aberto no Excel.
- Execute novamente `python src/att_massas.py`.

**O Fusion não consegue atualizar o CSV**
- Feche o CSV em qualquer editor ou planilha.
- Verifique se a pasta `data` existe e permite gravação.

## 10. Observações para publicação no GitHub

- Não envie o ambiente virtual `.venv/`.
- Não envie pastas `__pycache__/` nem arquivos `.pyc`.
- Revise os arquivos de montagem e o banco de massas antes de tornar o repositório público: eles podem revelar informações do projeto, componentes, massa e configuração do UAV.
- O CSV incluído é uma amostra de dados da montagem recebida. Substitua-o por uma amostra autorizada ou remova-o se não puder divulgar essas informações.
- Os arquivos MATLAB foram mantidos em `legacy_matlab/` apenas como referência histórica.

## 11. Licença

Nenhuma licença foi definida nesta versão. Antes de publicar o repositório como software de uso público, escolha uma licença compatível com os direitos sobre o código, o modelo CAD e os dados utilizados.
