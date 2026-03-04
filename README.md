# ₿ Panel DCA Bitcoin

Aplicación web local para registrar y visualizar tu estrategia de compra DCA (Dollar Cost Averaging) de Bitcoin.

## Características

- Registro de compras en **MXN**, con conversión automática a **USD** vía API
- Tipo de cambio MXN/USD obtenido automáticamente (sin llave de API)
- Precio actual de BTC obtenido de CoinGecko para calcular rendimiento
- Historial completo con exportación a CSV
- Gráficas interactivas de acumulación, inversión y precio promedio
- Base de datos **SQLite** local (sin configuración de servidor)
- Zona horaria **CDMX** (America/Mexico_City)
- Compatible con **Ubuntu** y **Windows**

---

## Instalación

### Requisitos previos
- Python 3.10 o superior

### Ubuntu / Linux

```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la app
streamlit run app.py
```

### Windows

```bat
REM 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

REM 2. Instalar dependencias
pip install -r requirements.txt

REM 3. Ejecutar la app
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## Uso

### Pestaña "Registrar Compra"
1. El tipo de cambio MXN/USD se obtiene automáticamente (puedes editarlo si difiere del de tu exchange)
2. Ingresa los **MXN gastados**
3. Ingresa los **BTC adquiridos** (ver en tu exchange)
4. Ingresa el **precio de compra en USD**
5. Opcionalmente agrega notas
6. Presiona **Guardar registro**

### Pestaña "Historial"
- Ver todos los registros ordenados por fecha
- Eliminar registros incorrectos
- Descargar el historial en formato CSV

### Pestaña "Resumen & Gráficas"
- Total invertido en MXN y USD
- BTC acumulados
- Precio promedio ponderado
- Valor actual de tu portafolio y rendimiento (si hay conexión a internet)
- Gráficas de acumulación, inversión por compra y evolución del precio

---

## Archivos generados

| Archivo | Descripción |
|---|---|
| `dca_bitcoin.db` | Base de datos SQLite con todos tus registros |

> La base de datos se crea automáticamente en la misma carpeta de la app.


### Correr programa

Ejecutar programa en la terminal:
Ubuntu
cd "DCA BITCOIN"
source venv/bin/activate
streamlit run app.py

WIndows CMD

cd "DCA BITCOIN"
venv\Scripts\activate
streamlit run app.py

power shell

cd "DCA BITCOIN"
venv\Scripts\Activate.ps1
streamlit run app.py