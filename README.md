# 🚀 Guía Completa: Deployment y Simulación de Cadena de Frío

## 📋 Índice
1. Instalación de Dependencias
2. Configuración de Anvil
3. Compilación del Contrato
4. Deployment Automatizado
5. Ejecución del Simulador


---

## 1. Instalación de Dependencias

### Instalar Foundry (incluye Anvil)
```bash
# Linux/MacOS
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Windows (usar WSL o Git Bash)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Instalar Python y librerías
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install web3 eth-account py-solc-x
```

### Instalar Solidity Compiler
```bash
# Usando py-solc-x (dentro de Python)
python -c "from solcx import install_solc; install_solc('0.8.0')"
```

---

## 2. Configuración de Anvil

### Iniciar Anvil
Abre una terminal y ejecuta:

```bash
anvil
```

Deberías ver algo como:
```
                             _   _
                            (_) | |
      __ _   _ __  __   __  _  | |
     / _` | | '_ \ \ \ / / | | | |
    | (_| | | | | | \ V /  | | | |
     \__,_| |_| |_|  \_/   |_| |_|

    0.2.0 (...)

Available Accounts
==================
(0) 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000.000000000000000000 ETH)
(1) 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 (10000.000000000000000000 ETH)
...

Listening on 127.0.0.1:8545
```

**✅ Mantén esta terminal abierta mientras trabajas**

---

## 3. Compilación del Contrato

### Opción A: Con Foundry (Recomendado)

1. **Crear estructura de proyecto:**
```bash
mkdir cadena-frio-blockchain
cd cadena-frio-blockchain
forge init --no-git
```

2. **Guardar el contrato:**
Copia el contrato Solidity en `src/CadenaFrioVacunas.sol`

3. **Compilar:**
```bash
forge build
```

El bytecode y ABI estarán en: `out/CadenaFrioVacunas.sol/CadenaFrioVacunas.json`

### Opción B: Con solc directo
```bash
# Guardar el contrato como CadenaFrioVacunas.sol
solc --bin --abi --optimize CadenaFrioVacunas.sol -o ./build
```

---

## 4. Deployment Automatizado

### Script de Deployment (`deploy.py`)

Crea un archivo `deploy.py`:

```python
from web3 import Web3
from eth_account import Account
import json

# Conectar a Anvil
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Cuenta owner (primera cuenta de Anvil)
owner_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
owner = Account.from_key(owner_key)

print(f"Deploying from: {owner.address}")

# Cargar ABI y Bytecode
with open('out/CadenaFrioVacunas.sol/CadenaFrioVacunas.json', 'r') as f:
    contract_json = json.load(f)
    abi = contract_json['abi']
    bytecode = contract_json['bytecode']['object']

# Crear contrato
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Desplegar
print("Deploying contract...")
nonce = w3.eth.get_transaction_count(owner.address)
tx = Contract.constructor().build_transaction({
    'from': owner.address,
    'nonce': nonce,
    'gas': 3000000,
    'gasPrice': w3.eth.gas_price
})

signed_tx = w3.eth.account.sign_transaction(tx, owner_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"Transaction hash: {tx_hash.hex()}")
print("Waiting for confirmation...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"\n✅ Contract deployed at: {receipt.contractAddress}")
print(f"Gas used: {receipt.gasUsed}")

# Guardar dirección
with open('contract_address.txt', 'w') as f:
    f.write(receipt.contractAddress)

print("\n📝 Address saved to contract_address.txt")
```

### Ejecutar deployment:
```bash
python deploy.py
```

---

## 5. Ejecución del Simulador

### Paso 1: Actualizar el script del simulador

En `sensor_simulator.py`, actualiza la línea:
```python
CONTRACT_ADDRESS = "0x..."  # Pega la dirección del contrato desplegado
```

### Paso 2: Script completo con setup (`run_simulation.py`)

```python
from web3 import Web3
from eth_account import Account
import json
import time
from sensor_simulator import CadenaFrioSimulator

def main():
    # Cargar dirección del contrato
    with open('contract_address.txt', 'r') as f:
        contract_address = f.read().strip()
    
    print(f"Using contract at: {contract_address}")
    
    # Cargar ABI
    with open('out/CadenaFrioVacunas.sol/CadenaFrioVacunas.json', 'r') as f:
        contract_json = json.load(f)
        abi = contract_json['abi']
    
    # Inicializar simulador
    simulator = CadenaFrioSimulator()
    simulator.contract = simulator.w3.eth.contract(
        address=contract_address,
        abi=abi
    )
    
    # Setup inicial
    print("\n1️⃣ Registrando participantes...")
    simulator.setup_participantes()
    
    time.sleep(2)
    
    # Crear lote
    lote_id = "VAC-2025-001"
    print(f"\n2️⃣ Creando lote {lote_id}...")
    simulator.crear_lote(lote_id)
    
    time.sleep(2)
    
    # Iniciar simulación
    print(f"\n3️⃣ Iniciando simulación...")
    print("⏰ Cada sensor registrará cada 15 segundos")
    print("📊 10 registros por fase (Lab → Logística → Farmacia)")
    print("\nPresiona Ctrl+C para detener\n")
    
    try:
        simulator.simular_cadena(lote_id, registros_por_fase=10)
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulación detenida por el usuario")
        simulator.mostrar_resumen(lote_id)

if __name__ == "__main__":
    main()
```

### Paso 3: Ejecutar simulación completa

```bash
python run_simulation.py
```

### Output esperado:
```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         🧪 SIMULADOR DE CADENA DE FRÍO - BLOCKCHAIN 🧪        ║
║              Trazabilidad de Vacunas con IoT                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

✅ Conectado a Anvil
👤 Owner: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
🔬 Laboratorio: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
🚚 Logística: 0x3C44CdDdB
