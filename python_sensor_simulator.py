"""
Simulador de Sensores IoT para Cadena de Frío
Simula 3 sensores (Laboratorio, Logística, Farmacia) que registran temperaturas cada 15 segundos
"""

import time
import random
from web3 import Web3
from eth_account import Account
from datetime import datetime
import json

# ===== CONFIGURACIÓN =====
ANVIL_RPC = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "TU_DIRECCION_DEL_CONTRATO_AQUI"  # Actualizar después del deploy

# ABI del contrato (versión simplificada - solo las funciones que usamos)
CONTRACT_ABI = json.loads('''[
    {
        "inputs": [{"internalType": "address","name": "_direccion","type": "address"},{"internalType": "uint8","name": "_rol","type": "uint8"}],
        "name": "registrarParticipante",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string","name": "_idLote","type": "string"},{"internalType": "address","name": "_logistica","type": "address"},{"internalType": "address","name": "_farmacia","type": "address"},{"internalType": "int256","name": "_tempMin","type": "int256"},{"internalType": "int256","name": "_tempMax","type": "int256"}],
        "name": "crearLote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string","name": "_idLote","type": "string"},{"internalType": "uint256","name": "_temperatura","type": "uint256"},{"internalType": "string","name": "_ubicacion","type": "string"}],
        "name": "registrarTemperatura",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string","name": "_idLote","type": "string"}],
        "name": "marcarComoEntregado",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string","name": "_idLote","type": "string"}],
        "name": "obtenerInfoLote",
        "outputs": [{"internalType": "string","name": "idLote","type": "string"},{"internalType": "uint256","name": "fechaCreacion","type": "uint256"},{"internalType": "uint8","name": "estado","type": "uint8"},{"internalType": "bool","name": "cadenaRota","type": "bool"},{"internalType": "int256","name": "tempMinima","type": "int256"},{"internalType": "int256","name": "tempMaxima","type": "int256"},{"internalType": "uint256","name": "cantidadRegistros","type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [{"indexed": true,"internalType": "string","name": "idLote","type": "string"},{"indexed": false,"internalType": "uint256","name": "temperatura","type": "uint256"},{"indexed": false,"internalType": "uint8","name": "registradoPor","type": "uint8"},{"indexed": false,"internalType": "uint256","name": "timestamp","type": "uint256"}],
        "name": "TemperaturaRegistrada",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [{"indexed": true,"internalType": "string","name": "idLote","type": "string"},{"indexed": false,"internalType": "uint256","name": "temperaturaRegistrada","type": "uint256"},{"indexed": false,"internalType": "int256","name": "tempMin","type": "int256"},{"indexed": false,"internalType": "int256","name": "tempMax","type": "int256"}],
        "name": "CadenaFrioRota",
        "type": "event"
    }
]''')

# Roles
ROL_LABORATORIO = 0
ROL_LOGISTICA = 1
ROL_FARMACIA = 2

# Estados de la cadena
ESTADO_LABORATORIO = "LABORATORIO"
ESTADO_LOGISTICA = "LOGISTICA"
ESTADO_FARMACIA = "FARMACIA"
ESTADO_COMPLETADO = "COMPLETADO"

class SensorSimulator:
    def __init__(self, w3, contract, account, rol, nombre, ubicacion_base):
        self.w3 = w3
        self.contract = contract
        self.account = account
        self.rol = rol
        self.nombre = nombre
        self.ubicacion_base = ubicacion_base
        self.activo = False
        
    def generar_temperatura(self):
        """Genera temperatura simulada con posibilidad de fallo (5% de probabilidad)"""
        # Temperatura base según fase del proceso
        if self.rol == ROL_LABORATORIO:
            base = -5.0  # Almacenamiento en laboratorio
            variacion = 2.0
        elif self.rol == ROL_LOGISTICA:
            base = -3.0  # Transporte refrigerado
            variacion = 3.0
        else:  # FARMACIA
            base = 4.0  # Refrigerador de farmacia
            variacion = 2.0
        
        # 5% de probabilidad de temperatura fuera de rango
        if random.random() < 0.05:
            temp = random.uniform(8, 15)  # Temperatura peligrosa
            print(f"⚠️  {self.nombre}: ¡ALERTA! Temperatura fuera de rango simulada")
        else:
            temp = base + random.uniform(-variacion, variacion)
        
        return round(temp, 1)
    
    def registrar_temperatura(self, id_lote):
        """Registra una temperatura en el smart contract"""
        try:
            temperatura = self.generar_temperatura()
            # Convertir a décimas (el contrato usa enteros)
            temp_decimas = int(temperatura * 10)
            
            ubicacion = f"{self.ubicacion_base} - Hora: {datetime.now().strftime('%H:%M:%S')}"
            
            # Construir transacción
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = self.contract.functions.registrarTemperatura(
                id_lote,
                temp_decimas,
                ubicacion
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Firmar y enviar
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Mostrar resultado
            emoji = "🌡️" if -8 <= temperatura <= 2 else "🔥"
            status = "✅" if receipt['status'] == 1 else "❌"
            print(f"{status} {emoji} {self.nombre}: {temperatura}°C registrada en {ubicacion}")
            print(f"   Gas usado: {receipt['gasUsed']} | TX: {tx_hash.hex()[:10]}...")
            
            return receipt['status'] == 1, temperatura
            
        except Exception as e:
            print(f"❌ Error en {self.nombre}: {str(e)}")
            return False, None

class CadenaFrioSimulator:
    def __init__(self):
        # Conectar a Anvil
        self.w3 = Web3(Web3.HTTPProvider(ANVIL_RPC))
        if not self.w3.is_connected():
            raise Exception("No se pudo conectar a Anvil. ¿Está corriendo?")
        
        print("✅ Conectado a Anvil")
        
        # Obtener cuentas de Anvil (las primeras 4)
        accounts = self.w3.eth.accounts
        self.owner_address = accounts[0]
        
        # Crear cuentas para los sensores (usando claves privadas de Anvil)
        # Nota: Estas son las claves por defecto de Anvil
        private_keys = [
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",  # Account 0 (Owner)
            "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",  # Account 1 (Lab)
            "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",  # Account 2 (Log)
            "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",  # Account 3 (Far)
        ]
        
        self.owner_account = Account.from_key(private_keys[0])
        self.lab_account = Account.from_key(private_keys[1])
        self.log_account = Account.from_key(private_keys[2])
        self.far_account = Account.from_key(private_keys[3])
        
        print(f"👤 Owner: {self.owner_address}")
        print(f"🔬 Laboratorio: {self.lab_account.address}")
        print(f"🚚 Logística: {self.log_account.address}")
        print(f"💊 Farmacia: {self.far_account.address}")
        
        self.contract = None
        self.estado_actual = ESTADO_LABORATORIO
        
    def deploy_contract(self, bytecode, abi):
        """Despliega el contrato en Anvil"""
        print("\n🚀 Desplegando contrato...")
        
        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        nonce = self.w3.eth.get_transaction_count(self.owner_address)
        tx = Contract.constructor().build_transaction({
            'from': self.owner_address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.owner_account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        self.contract = self.w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=abi
        )
        
        print(f"✅ Contrato desplegado en: {tx_receipt.contractAddress}")
        print(f"   Gas usado: {tx_receipt.gasUsed}")
        return tx_receipt.contractAddress
    
    def setup_participantes(self):
        """Registra los participantes en el contrato"""
        print("\n👥 Registrando participantes...")
        
        participantes = [
            (self.lab_account.address, ROL_LABORATORIO, "Laboratorio"),
            (self.log_account.address, ROL_LOGISTICA, "Logística"),
            (self.far_account.address, ROL_FARMACIA, "Farmacia")
        ]
        
        for address, rol, nombre in participantes:
            nonce = self.w3.eth.get_transaction_count(self.owner_address)
            tx = self.contract.functions.registrarParticipante(
                address, rol
            ).build_transaction({
                'from': self.owner_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.owner_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"✅ {nombre} registrado")
    
    def crear_lote(self, id_lote):
        """Crea un nuevo lote de vacunas"""
        print(f"\n📦 Creando lote {id_lote}...")
        
        # Rango de temperatura: -8°C a +2°C (en décimas: -80 a 20)
        temp_min = -80
        temp_max = 20
        
        nonce = self.w3.eth.get_transaction_count(self.lab_account.address)
        tx = self.contract.functions.crearLote(
            id_lote,
            self.log_account.address,
            self.far_account.address,
            temp_min,
            temp_max
        ).build_transaction({
            'from': self.lab_account.address,
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.lab_account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"✅ Lote {id_lote} creado (Rango: -8°C a +2°C)")
        print(f"   TX: {tx_hash.hex()}")
    
    def cambiar_estado(self, id_lote, nuevo_estado):
        """Cambia el estado de la cadena (simula transferencia)"""
        print(f"\n🔄 Cambiando estado: {self.estado_actual} → {nuevo_estado}")
        self.estado_actual = nuevo_estado
        
        if nuevo_estado == ESTADO_COMPLETADO:
            # Marcar como entregado
            nonce = self.w3.eth.get_transaction_count(self.far_account.address)
            tx = self.contract.functions.marcarComoEntregado(id_lote).build_transaction({
                'from': self.far_account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.far_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print("✅ Lote marcado como ENTREGADO")
    
    def simular_cadena(self, id_lote, registros_por_fase=10):
        """Simula toda la cadena de frío con los 3 sensores"""
        print("\n" + "="*70)
        print(f"🧪 INICIANDO SIMULACIÓN DE CADENA DE FRÍO - LOTE: {id_lote}")
        print("="*70)
        
        # Crear sensores
        sensores = {
            ESTADO_LABORATORIO: SensorSimulator(
                self.w3, self.contract, self.lab_account,
                ROL_LABORATORIO, "Sensor Lab", "Laboratorio Central - Cámara Fría"
            ),
            ESTADO_LOGISTICA: SensorSimulator(
                self.w3, self.contract, self.log_account,
                ROL_LOGISTICA, "Sensor Log", "Camión Refrigerado - En tránsito"
            ),
            ESTADO_FARMACIA: SensorSimulator(
                self.w3, self.contract, self.far_account,
                ROL_FARMACIA, "Sensor Far", "Farmacia - Refrigerador Principal"
            )
        }
        
        fases = [
            (ESTADO_LABORATORIO, registros_por_fase, "FASE 1: ALMACENAMIENTO EN LABORATORIO"),
            (ESTADO_LOGISTICA, registros_por_fase, "FASE 2: TRANSPORTE LOGÍSTICO"),
            (ESTADO_FARMACIA, registros_por_fase, "FASE 3: ALMACENAMIENTO EN FARMACIA"),
        ]
        
        for estado, num_registros, titulo in fases:
            print(f"\n{'='*70}")
            print(f"📍 {titulo}")
            print(f"{'='*70}")
            
            sensor = sensores[estado]
            
            for i in range(num_registros):
                print(f"\n[Registro {i+1}/{num_registros}]")
                success, temp = sensor.registrar_temperatura(id_lote)
                
                if not success:
                    print("⚠️  Reintentando en 5 segundos...")
                    time.sleep(5)
                    continue
                
                # Esperar 15 segundos antes del próximo registro
                if i < num_registros - 1:
                    print(f"⏳ Esperando 15 segundos para próximo registro...")
                    time.sleep(15)
            
            # Cambiar al siguiente estado
            if estado == ESTADO_LABORATORIO:
                print(f"\n🚚 Transferencia a Logística...")
                time.sleep(5)
                self.cambiar_estado(id_lote, ESTADO_LOGISTICA)
            elif estado == ESTADO_LOGISTICA:
                print(f"\n💊 Transferencia a Farmacia...")
                time.sleep(5)
                self.cambiar_estado(id_lote, ESTADO_FARMACIA)
            else:
                self.cambiar_estado(id_lote, ESTADO_COMPLETADO)
        
        # Resumen final
        print("\n" + "="*70)
        print("📊 RESUMEN FINAL")
        print("="*70)
        self.mostrar_resumen(id_lote)
    
    def mostrar_resumen(self, id_lote):
        """Muestra un resumen del lote"""
        try:
            info = self.contract.functions.obtenerInfoLote(id_lote).call()
            
            estados_txt = ["Activo", "Comprometido", "Entregado"]
            
            print(f"📦 Lote: {info[0]}")
            print(f"📅 Creado: {datetime.fromtimestamp(info[1]).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🏷️  Estado: {estados_txt[info[2]]}")
            print(f"❄️  Cadena de frío: {'❌ ROTA' if info[3] else '✅ INTACTA'}")
            print(f"🌡️  Rango permitido: {info[4]/10}°C a {info[5]/10}°C")
            print(f"📈 Total registros: {info[6]}")
            
        except Exception as e:
            print(f"❌ Error al obtener resumen: {str(e)}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         🧪 SIMULADOR DE CADENA DE FRÍO - BLOCKCHAIN 🧪        ║
    ║              Trazabilidad de Vacunas con IoT                  ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar simulador
    simulator = CadenaFrioSimulator()
    
    # Nota: Aquí necesitas el bytecode del contrato compilado
    # Para compilarlo usa: solc --bin --abi CadenaFrioVacunas.sol
    print("\n⚠️  IMPORTANTE: Necesitas desplegar el contrato primero")
    print("   Usa el script de deployment o actualiza CONTRACT_ADDRESS")
    
    # Si ya tienes el contrato desplegado, descomentar:
    # simulator.contract = simulator.w3.eth.contract(
    #     address=CONTRACT_ADDRESS,
    #     abi=CONTRACT_ABI
    # )
    
    # Descomentar para setup inicial:
    # simulator.setup_participantes()
    # simulator.crear_lote("VAC-2025-001")
    
    # Iniciar simulación
    # simulator.simular_cadena("VAC-2025-001", registros_por_fase=10)

if __name__ == "__main__":
    main()