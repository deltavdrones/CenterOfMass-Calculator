"""
CM-Calc - Atualização do banco de massas.

Lê os componentes exportados pelo Fusion 360 e cadastra as massas
que ainda não existem em data/banco_de_massas.xlsx.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FILE_POS = DATA_DIR / "componentes_posicao.csv"
FILE_MASS = DATA_DIR / "banco_de_massas.xlsx"

RHO_PLA = 0.00124  # g/mm³


def read_positions() -> pd.DataFrame:
    if not FILE_POS.exists():
        raise FileNotFoundError(
            f"Arquivo de posições não encontrado: {FILE_POS}\n"
            "Execute primeiro o script CM2CSV no Fusion 360."
        )

    # utf-8-sig lê tanto CSV UTF-8 com BOM quanto CSV UTF-8 comum.
    # cp1252 é mantido como fallback para o CSV antigo exportado no Windows.
    try:
        positions = pd.read_csv(FILE_POS, encoding="utf-8-sig")
    except UnicodeDecodeError:
        positions = pd.read_csv(FILE_POS, encoding="cp1252")

    positions.columns = [str(c).strip().lower() for c in positions.columns]
    required = {"nome", "vol_mm3"}
    missing = required - set(positions.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(sorted(missing))}")

    positions["nome"] = positions["nome"].astype(str).str.strip()
    return positions


def read_mass_database() -> pd.DataFrame:
    if not FILE_MASS.exists():
        return pd.DataFrame(columns=["nome", "massa"])

    masses = pd.read_excel(FILE_MASS)
    if len(masses.columns) != 2:
        raise ValueError(
            "O banco_de_massas.xlsx deve conter exatamente duas colunas: nome e massa."
        )

    masses.columns = ["nome", "massa"]
    masses["nome"] = masses["nome"].astype(str).str.strip()
    masses["massa"] = pd.to_numeric(masses["massa"], errors="coerce")

    if masses["nome"].duplicated().any():
        duplicated = masses.loc[masses["nome"].duplicated(), "nome"].tolist()
        raise ValueError(f"Há nomes duplicados no banco de massas: {duplicated}")

    if masses["massa"].isna().any() or (masses["massa"] <= 0).any():
        raise ValueError("O banco de massas contém massas ausentes, inválidas ou não positivas.")

    return masses


def att_massas() -> None:
    print("\n===== CM-CALC | CADASTRO DE MASSAS =====\n")

    positions = read_positions()
    masses = read_mass_database()

    registered = {
        name.casefold()
        for name in masses["nome"].dropna().astype(str)
    }

    new_components = []
    seen = set()

    for _, component in positions.iterrows():
        name = str(component["nome"]).strip()
        normalized = name.casefold()
        if normalized not in registered and normalized not in seen:
            new_components.append(component)
            seen.add(normalized)

    if not new_components:
        print("Todos os componentes já possuem massa cadastrada.")
        return

    print(f"Novos componentes encontrados: {len(new_components)}")

    new_records = []
    for component in new_components:
        name = str(component["nome"]).strip()
        while True:
            entry = input(f'Massa para "{name}" (g) ou PLA: ').strip()

            if entry.casefold() == "pla":
                volume = pd.to_numeric(component["vol_mm3"], errors="coerce")
                if pd.isna(volume) or volume <= 0:
                    print("Volume ausente ou inválido. Não é possível calcular a massa por PLA.")
                    continue
                mass = float(volume) * RHO_PLA
                print(f"  -> Massa estimada: {mass:.3f} g")
                break

            try:
                mass = float(entry.replace(",", "."))
                if not pd.notna(mass) or mass <= 0:
                    print("Informe uma massa maior que zero.")
                    continue
                break
            except ValueError:
                print("Entrada inválida. Digite um número (em gramas) ou PLA.")

        new_records.append({"nome": name, "massa": mass})

    updated = pd.concat([masses, pd.DataFrame(new_records)], ignore_index=True)

    try:
        updated.to_excel(FILE_MASS, index=False)
    except PermissionError as exc:
        raise PermissionError(
            "Não foi possível atualizar o Excel. Feche banco_de_massas.xlsx e tente novamente."
        ) from exc

    print("\nBanco de massas atualizado!")
    print(f"Novos registros: {len(new_records)}")
    print(f"Total cadastrado: {len(updated)}")
    print(f"Arquivo: {FILE_MASS}\n")


if __name__ == "__main__":
    att_massas()
