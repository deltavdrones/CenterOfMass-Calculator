"""
CM-Calc - Cálculo e visualização do centro de massa.

Combina as coordenadas exportadas pelo Fusion 360 com o banco de massas,
calcula o CM ponderado pela massa e apresenta uma visualização 3D interativa.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FILE_POS = DATA_DIR / "componentes_posicao.csv"
FILE_MASS = DATA_DIR / "banco_de_massas.xlsx"


def read_positions() -> pd.DataFrame:
    if not FILE_POS.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {FILE_POS}")

    try:
        positions = pd.read_csv(FILE_POS, encoding="utf-8-sig")
    except UnicodeDecodeError:
        positions = pd.read_csv(FILE_POS, encoding="cp1252")

    positions.columns = [str(c).strip().lower() for c in positions.columns]
    required = {"nome", "x_mm", "y_mm", "z_mm"}
    missing = required - set(positions.columns)
    if missing:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(sorted(missing))}")

    positions["nome"] = positions["nome"].astype(str).str.strip()
    return positions


def calcular_cm():
    if not FILE_MASS.exists():
        raise FileNotFoundError(
            f"Banco de massas não encontrado: {FILE_MASS}\n"
            "Execute primeiro: python src/att_massas.py"
        )

    positions = read_positions()
    masses = pd.read_excel(FILE_MASS)

    if len(masses.columns) != 2:
        raise ValueError("O Excel deve conter as colunas nome e massa.")
    masses.columns = ["nome", "massa"]
    masses["nome"] = masses["nome"].astype(str).str.strip()
    masses["massa"] = pd.to_numeric(masses["massa"], errors="coerce")

    if masses["nome"].duplicated().any():
        duplicated = masses.loc[masses["nome"].duplicated(), "nome"].tolist()
        raise ValueError(f"Há nomes duplicados no banco de massas: {duplicated}")

    # Verifica os componentes sem massa antes do cruzamento.
    mass_names = {name.casefold() for name in masses["nome"].dropna().astype(str)}
    missing_names = [
        name for name in positions["nome"].astype(str)
        if name.casefold() not in mass_names
    ]
    if missing_names:
        unique_missing = list(dict.fromkeys(missing_names))
        raise ValueError(
            "Há componentes sem massa cadastrada: "
            + ", ".join(unique_missing)
            + "\nExecute: python src/att_massas.py"
        )

    # Mantém a associação por nome usada no innerjoin do MATLAB.
    data = positions.merge(
        masses,
        on="nome",
        how="inner",
        validate="many_to_one"
    )

    numeric_columns = ["x_mm", "y_mm", "z_mm", "massa"]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    values = data[numeric_columns].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Existem coordenadas ou massas ausentes/inválidas.")

    if (data["massa"] <= 0).any():
        raise ValueError("Todas as massas devem ser maiores que zero.")

    total_mass = float(data["massa"].sum())
    if total_mass <= 0:
        raise ValueError("A massa total precisa ser maior que zero.")

    # Convenção preservada do main.m original: inverter o sinal do eixo Y.
    data["y_mm"] = -data["y_mm"]

    coordinates = data[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
    component_masses = data["massa"].to_numpy(dtype=float)

    # CM = soma(m_i * r_i) / soma(m_i)
    center_of_mass = np.sum(
        coordinates * component_masses[:, np.newaxis],
        axis=0
    ) / total_mass

    print("\n========== CM-CALC ==========")
    print(f"Massa Total: {total_mass:.2f} g")
    print("CM Final:")
    print(f"X: {center_of_mass[0]:.4f} mm")
    print(f"Y: {center_of_mass[1]:.4f} mm")
    print(f"Z: {center_of_mass[2]:.4f} mm")
    print("============================\n")

    return data, center_of_mass, total_mass


def visualizar_cm(data: pd.DataFrame, center_of_mass: np.ndarray) -> None:
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")

    points = ax.scatter(
        data["x_mm"], data["y_mm"], data["z_mm"],
        s=50, color="blue", alpha=0.6, picker=5,
        label="Componentes"
    )

    ax.scatter(
        center_of_mass[0], center_of_mass[1], center_of_mass[2],
        s=100, color=(0.5, 0.5, 0.5), label="Centro de Massa"
    )
    ax.text(
        center_of_mass[0], center_of_mass[1], center_of_mass[2],
        "  CM", fontweight="bold"
    )

    ax.scatter(0, 0, 0, s=80, color="red", label="Origem")
    ax.text(0, 0, 0, "  Origem", color="red")

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("Distribuição de Massas e CM")
    ax.grid(True)
    ax.legend()
    ax.view_init(elev=25, azim=-55)

    # Aproxima a escala igual nos três eixos.
    ranges = np.array([
        data["x_mm"].max() - data["x_mm"].min(),
        data["y_mm"].max() - data["y_mm"].min(),
        data["z_mm"].max() - data["z_mm"].min()
    ], dtype=float)
    ranges[ranges == 0] = 1.0
    ax.set_box_aspect(ranges)

    # Mesmo sentido visual do eixo Y configurado no MATLAB (YDir = reverse).
    ax.invert_yaxis()

    annotation = None

    def on_pick(event):
        nonlocal annotation
        if event.artist is not points or len(event.ind) == 0:
            return

        index = int(event.ind[0])
        component = data.iloc[index]

        message = (
            f"Comp: {component['nome']}\n"
            f"Massa: {component['massa']:.2f} g\n"
            f"Pos: [{component['x_mm']:.1f}, "
            f"{component['y_mm']:.1f}, "
            f"{component['z_mm']:.1f}] mm"
        )

        if annotation is not None:
            annotation.remove()

        annotation = ax.text2D(
            0.02, 0.96, message,
            transform=ax.transAxes,
            va="top",
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9}
        )
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", on_pick)
    plt.tight_layout()
    plt.show()


def main():
    data, center_of_mass, _ = calcular_cm()
    visualizar_cm(data, center_of_mass)


if __name__ == "__main__":
    main()
