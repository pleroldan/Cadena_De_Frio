// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title CadenaFrioVacunas
 * @notice Contrato para rastrear la cadena de frío de lotes de vacunas
 * @dev Permite a 3 actores (Laboratorio, Logística, Farmacia) registrar temperaturas
 */
contract CadenaFrioVacunas {
    
    // --- Enums y Estructuras ---
    
    enum Rol { Laboratorio, Logistica, Farmacia }
    enum EstadoLote { Activo, Comprometido, Entregado }
    
    struct RegistroTemperatura {
        uint256 temperatura;      // Temperatura en décimas de grado (ej: 25 = 2.5°C)
        uint256 timestamp;        // Momento del registro
        Rol registradoPor;        // Quién registró
        string ubicacion;         // Ubicación opcional
    }
    
    struct Lote {
        string idLote;
        uint256 fechaCreacion;
        EstadoLote estado;
        address laboratorio;
        address logistica;
        address farmacia;
        int256 tempMinima;        // Temperatura mínima permitida (en décimas)
        int256 tempMaxima;        // Temperatura máxima permitida (en décimas)
        RegistroTemperatura[] historial;
        bool cadenaRota;          // Si se rompió la cadena de frío
    }
    
    // --- Variables de Estado ---
    
    address public owner;
    mapping(string => Lote) public lotes;
    mapping(address => Rol) public participantes;
    mapping(address => bool) public participantesRegistrados;
    string[] public listadoLotes;
    
    // --- Eventos ---
    
    event ParticipanteRegistrado(address indexed participante, Rol rol);
    event LoteCreado(string indexed idLote, address indexed laboratorio, int256 tempMin, int256 tempMax);
    event TemperaturaRegistrada(string indexed idLote, uint256 temperatura, Rol registradoPor, uint256 timestamp);
    event CadenaFrioRota(string indexed idLote, uint256 temperaturaRegistrada, int256 tempMin, int256 tempMax);
    event LoteEntregado(string indexed idLote, address indexed farmacia);
    
    // --- Modificadores ---
    
    modifier soloOwner() {
        require(msg.sender == owner, "Solo el owner puede ejecutar esta funcion");
        _;
    }
    
    modifier soloParticipante() {
        require(participantesRegistrados[msg.sender], "No eres un participante registrado");
        _;
    }
    
    modifier loteExiste(string memory _idLote) {
        require(bytes(lotes[_idLote].idLote).length > 0, "El lote no existe");
        _;
    }
    
    // --- Constructor ---
    
    constructor() {
        owner = msg.sender;
    }
    
    // --- Funciones de Administración ---
    
    /**
     * @notice Registra un nuevo participante en el sistema
     * @param _direccion Dirección del participante
     * @param _rol Rol del participante (0=Lab, 1=Logística, 2=Farmacia)
     */
    function registrarParticipante(address _direccion, Rol _rol) public soloOwner {
        require(!participantesRegistrados[_direccion], "Participante ya registrado");
        participantes[_direccion] = _rol;
        participantesRegistrados[_direccion] = true;
        emit ParticipanteRegistrado(_direccion, _rol);
    }
    
    /**
     * @notice Crea un nuevo lote de vacunas
     * @param _idLote Identificador único del lote
     * @param _logistica Dirección del proveedor logístico
     * @param _farmacia Dirección de la farmacia destino
     * @param _tempMin Temperatura mínima permitida (en décimas de °C)
     * @param _tempMax Temperatura máxima permitida (en décimas de °C)
     */
    function crearLote(
        string memory _idLote,
        address _logistica,
        address _farmacia,
        int256 _tempMin,
        int256 _tempMax
    ) public soloParticipante {
        require(participantes[msg.sender] == Rol.Laboratorio, "Solo el laboratorio puede crear lotes");
        require(bytes(lotes[_idLote].idLote).length == 0, "El lote ya existe");
        require(participantesRegistrados[_logistica], "Logistica no registrada");
        require(participantesRegistrados[_farmacia], "Farmacia no registrada");
        require(_tempMin < _tempMax, "Rango de temperatura invalido");
        
        Lote storage nuevoLote = lotes[_idLote];
        nuevoLote.idLote = _idLote;
        nuevoLote.fechaCreacion = block.timestamp;
        nuevoLote.estado = EstadoLote.Activo;
        nuevoLote.laboratorio = msg.sender;
        nuevoLote.logistica = _logistica;
        nuevoLote.farmacia = _farmacia;
        nuevoLote.tempMinima = _tempMin;
        nuevoLote.tempMaxima = _tempMax;
        nuevoLote.cadenaRota = false;
        
        listadoLotes.push(_idLote);
        
        emit LoteCreado(_idLote, msg.sender, _tempMin, _tempMax);
    }
    
    // --- Funciones de Registro de Temperatura ---
    
    /**
     * @notice Registra una nueva temperatura para un lote
     * @param _idLote ID del lote
     * @param _temperatura Temperatura en décimas de grado (ej: 25 = 2.5°C)
     * @param _ubicacion Ubicación donde se tomó la medición
     */
    function registrarTemperatura(
        string memory _idLote,
        uint256 _temperatura,
        string memory _ubicacion
    ) public soloParticipante loteExiste(_idLote) {
        Lote storage lote = lotes[_idLote];
        require(lote.estado == EstadoLote.Activo, "El lote no esta activo");
        
        // Verificar que el participante esté autorizado para este lote
        require(
            msg.sender == lote.laboratorio || 
            msg.sender == lote.logistica || 
            msg.sender == lote.farmacia,
            "No estas autorizado para este lote"
        );
        
        // Crear registro
        RegistroTemperatura memory nuevoRegistro = RegistroTemperatura({
            temperatura: _temperatura,
            timestamp: block.timestamp,
            registradoPor: participantes[msg.sender],
            ubicacion: _ubicacion
        });
        
        lote.historial.push(nuevoRegistro);
        
        // Verificar si se rompió la cadena de frío
        int256 tempInt = int256(_temperatura);
        if (tempInt < lote.tempMinima || tempInt > lote.tempMaxima) {
            lote.cadenaRota = true;
            lote.estado = EstadoLote.Comprometido;
            emit CadenaFrioRota(_idLote, _temperatura, lote.tempMinima, lote.tempMaxima);
        }
        
        emit TemperaturaRegistrada(_idLote, _temperatura, participantes[msg.sender], block.timestamp);
    }
    
    /**
     * @notice Marca un lote como entregado
     * @param _idLote ID del lote
     */
    function marcarComoEntregado(string memory _idLote) public soloParticipante loteExiste(_idLote) {
        Lote storage lote = lotes[_idLote];
        require(msg.sender == lote.farmacia, "Solo la farmacia puede marcar como entregado");
        require(lote.estado != EstadoLote.Entregado, "El lote ya fue entregado");
        
        lote.estado = EstadoLote.Entregado;
        emit LoteEntregado(_idLote, msg.sender);
    }
    
    // --- Funciones de Consulta ---
    
    /**
     * @notice Obtiene el historial completo de temperaturas de un lote
     * @param _idLote ID del lote
     * @return Array de registros de temperatura
     */
    function obtenerHistorial(string memory _idLote) 
        public 
        view 
        loteExiste(_idLote) 
        returns (RegistroTemperatura[] memory) 
    {
        return lotes[_idLote].historial;
    }
    
    /**
     * @notice Obtiene información básica de un lote
     * @param _idLote ID del lote
     */
    function obtenerInfoLote(string memory _idLote) 
        public 
        view 
        loteExiste(_idLote) 
        returns (
            string memory idLote,
            uint256 fechaCreacion,
            EstadoLote estado,
            bool cadenaRota,
            int256 tempMinima,
            int256 tempMaxima,
            uint256 cantidadRegistros
        ) 
    {
        Lote storage lote = lotes[_idLote];
        return (
            lote.idLote,
            lote.fechaCreacion,
            lote.estado,
            lote.cadenaRota,
            lote.tempMinima,
            lote.tempMaxima,
            lote.historial.length
        );
    }
    
    /**
     * @notice Obtiene la última temperatura registrada de un lote
     * @param _idLote ID del lote
     */
    function obtenerUltimaTemperatura(string memory _idLote) 
        public 
        view 
        loteExiste(_idLote) 
        returns (uint256 temperatura, uint256 timestamp, Rol registradoPor) 
    {
        Lote storage lote = lotes[_idLote];
        require(lote.historial.length > 0, "No hay registros de temperatura");
        
        RegistroTemperatura memory ultimo = lote.historial[lote.historial.length - 1];
        return (ultimo.temperatura, ultimo.timestamp, ultimo.registradoPor);
    }
    
    /**
     * @notice Obtiene todos los IDs de lotes creados
     */
    function obtenerTodosLosLotes() public view returns (string[] memory) {
        return listadoLotes;
    }
    
    /**
     * @notice Verifica si la cadena de frío está intacta
     * @param _idLote ID del lote
     */
    function verificarCadenaFrio(string memory _idLote) 
        public 
        view 
        loteExiste(_idLote) 
        returns (bool) 
    {
        return !lotes[_idLote].cadenaRota;
    }
}