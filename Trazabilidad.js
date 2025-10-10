import React, { useState } from 'react';
import { Activity, Package, Thermometer, AlertTriangle, CheckCircle, Users, History } from 'lucide-react';

export default function ColdChainSimulator() {
  const [lotes, setLotes] = useState([]);
  const [selectedLote, setSelectedLote] = useState(null);
  const [participantes, setParticipantes] = useState({
    laboratorio: null,
    logistica: null,
    farmacia: null
  });
  
  const [newLote, setNewLote] = useState({
    id: '',
    tempMin: -8,
    tempMax: 2
  });
  
  const [newTemp, setNewTemp] = useState({
    temperatura: 0,
    ubicacion: '',
    registrador: 'laboratorio'
  });

  // Registrar participantes (simulación)
  const registrarParticipantes = () => {
    setParticipantes({
      laboratorio: '0xLab' + Math.random().toString(36).substr(2, 6),
      logistica: '0xLog' + Math.random().toString(36).substr(2, 6),
      farmacia: '0xFar' + Math.random().toString(36).substr(2, 6)
    });
  };

  // Crear lote
  const crearLote = () => {
    if (!newLote.id || !participantes.laboratorio) return;
    
    const lote = {
      id: newLote.id,
      fechaCreacion: new Date(),
      estado: 'Activo',
      tempMinima: parseFloat(newLote.tempMin),
      tempMaxima: parseFloat(newLote.tempMax),
      laboratorio: participantes.laboratorio,
      logistica: participantes.logistica,
      farmacia: participantes.farmacia,
      historial: [],
      cadenaRota: false
    };
    
    setLotes([...lotes, lote]);
    setNewLote({ id: '', tempMin: -8, tempMax: 2 });
  };

  // Registrar temperatura
  const registrarTemperatura = () => {
    if (!selectedLote) return;
    
    const temp = parseFloat(newTemp.temperatura);
    const registro = {
      temperatura: temp,
      timestamp: new Date(),
      registradoPor: newTemp.registrador,
      ubicacion: newTemp.ubicacion
    };
    
    const lotesActualizados = lotes.map(l => {
      if (l.id === selectedLote.id) {
        const cadenaRota = temp < l.tempMinima || temp > l.tempMaxima;
        return {
          ...l,
          historial: [...l.historial, registro],
          cadenaRota: cadenaRota || l.cadenaRota,
          estado: cadenaRota ? 'Comprometido' : l.estado
        };
      }
      return l;
    });
    
    setLotes(lotesActualizados);
    setSelectedLote(lotesActualizados.find(l => l.id === selectedLote.id));
    setNewTemp({ temperatura: 0, ubicacion: '', registrador: 'laboratorio' });
  };

  // Marcar como entregado
  const marcarEntregado = () => {
    if (!selectedLote) return;
    
    const lotesActualizados = lotes.map(l => {
      if (l.id === selectedLote.id) {
        return { ...l, estado: 'Entregado' };
      }
      return l;
    });
    
    setLotes(lotesActualizados);
    setSelectedLote(lotesActualizados.find(l => l.id === selectedLote.id));
  };

  const getEstadoColor = (estado) => {
    switch(estado) {
      case 'Activo': return 'bg-blue-100 text-blue-800';
      case 'Comprometido': return 'bg-red-100 text-red-800';
      case 'Entregado': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRolLabel = (rol) => {
    switch(rol) {
      case 'laboratorio': return 'Laboratorio';
      case 'logistica': return 'Logística';
      case 'farmacia': return 'Farmacia';
      default: return rol;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Activity className="w-10 h-10 text-indigo-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Cadena de Frío - Trazabilidad de Vacunas</h1>
              <p className="text-gray-600">Sistema blockchain para monitoreo de temperatura</p>
            </div>
          </div>

          {/* Registro de Participantes */}
          {!participantes.laboratorio && (
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <Users className="w-6 h-6 text-yellow-600" />
                <h2 className="text-xl font-semibold text-gray-800">Paso 1: Registrar Participantes</h2>
              </div>
              <p className="text-gray-600 mb-4">Primero debes registrar las direcciones de los 3 actores</p>
              <button
                onClick={registrarParticipantes}
                className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 font-medium"
              >
                Generar Direcciones de Prueba
              </button>
            </div>
          )}

          {/* Participantes Registrados */}
          {participantes.laboratorio && (
            <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-800">Participantes Registrados</h2>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-lg border border-green-200">
                  <div className="font-semibold text-gray-700">🔬 Laboratorio</div>
                  <div className="text-sm text-gray-600 font-mono mt-1">{participantes.laboratorio}</div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-green-200">
                  <div className="font-semibold text-gray-700">🚚 Logística</div>
                  <div className="text-sm text-gray-600 font-mono mt-1">{participantes.logistica}</div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-green-200">
                  <div className="font-semibold text-gray-700">💊 Farmacia</div>
                  <div className="text-sm text-gray-600 font-mono mt-1">{participantes.farmacia}</div>
                </div>
              </div>
            </div>
          )}

          {/* Crear Lote */}
          {participantes.laboratorio && (
            <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <Package className="w-6 h-6 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-800">Crear Nuevo Lote</h2>
              </div>
              <div className="grid md:grid-cols-3 gap-4 mb-4">
                <input
                  type="text"
                  placeholder="ID del Lote (ej: VAC-2025-001)"
                  value={newLote.id}
                  onChange={(e) => setNewLote({...newLote, id: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <input
                  type="number"
                  placeholder="Temp. Mínima (°C)"
                  value={newLote.tempMin}
                  onChange={(e) => setNewLote({...newLote, tempMin: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <input
                  type="number"
                  placeholder="Temp. Máxima (°C)"
                  value={newLote.tempMax}
                  onChange={(e) => setNewLote({...newLote, tempMax: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={crearLote}
                disabled={!newLote.id}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium disabled:bg-gray-400"
              >
                Crear Lote
              </button>
            </div>
          )}
        </div>

        {/* Lista de Lotes */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Lotes Registrados</h2>
            {lotes.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No hay lotes creados aún</p>
            ) : (
              <div className="space-y-3">
                {lotes.map((lote) => (
                  <div
                    key={lote.id}
                    onClick={() => setSelectedLote(lote)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedLote?.id === lote.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-bold text-gray-800">{lote.id}</div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getEstadoColor(lote.estado)}`}>
                        {lote.estado}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      <div>Rango: {lote.tempMinima}°C a {lote.tempMaxima}°C</div>
                      <div>Registros: {lote.historial.length}</div>
                      {lote.cadenaRota && (
                        <div className="flex items-center gap-1 text-red-600 font-semibold mt-1">
                          <AlertTriangle className="w-4 h-4" />
                          Cadena de frío comprometida
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Detalles del Lote Seleccionado */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            {!selectedLote ? (
              <div className="text-center text-gray-500 py-8">
                Selecciona un lote para ver detalles
              </div>
            ) : (
              <>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Detalles: {selectedLote.id}</h2>
                
                {/* Registrar Temperatura */}
                {selectedLote.estado === 'Activo' && (
                  <div className="bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 mb-6">
                    <div className="flex items-center gap-2 mb-3">
                      <Thermometer className="w-5 h-5 text-indigo-600" />
                      <h3 className="font-semibold text-gray-800">Registrar Temperatura</h3>
                    </div>
                    <div className="space-y-3">
                      <input
                        type="number"
                        step="0.1"
                        placeholder="Temperatura (°C)"
                        value={newTemp.temperatura}
                        onChange={(e) => setNewTemp({...newTemp, temperatura: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      />
                      <input
                        type="text"
                        placeholder="Ubicación (opcional)"
                        value={newTemp.ubicacion}
                        onChange={(e) => setNewTemp({...newTemp, ubicacion: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      />
                      <select
                        value={newTemp.registrador}
                        onChange={(e) => setNewTemp({...newTemp, registrador: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="laboratorio">Laboratorio</option>
                        <option value="logistica">Logística</option>
                        <option value="farmacia">Farmacia</option>
                      </select>
                      <button
                        onClick={registrarTemperatura}
                        className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium"
                      >
                        Registrar
                      </button>
                    </div>
                  </div>
                )}

                {/* Marcar como Entregado */}
                {selectedLote.estado !== 'Entregado' && (
                  <button
                    onClick={marcarEntregado}
                    className="w-full bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 font-medium mb-6"
                  >
                    Marcar como Entregado
                  </button>
                )}

                {/* Historial */}
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <History className="w-5 h-5 text-gray-600" />
                    <h3 className="font-semibold text-gray-800">Historial de Temperaturas</h3>
                  </div>
                  {selectedLote.historial.length === 0 ? (
                    <p className="text-gray-500 text-sm">No hay registros aún</p>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {[...selectedLote.historial].reverse().map((reg, idx) => {
                        const fueraDeRango = reg.temperatura < selectedLote.tempMinima || 
                                           reg.temperatura > selectedLote.tempMaxima;
                        return (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg ${fueraDeRango ? 'bg-red-50 border border-red-200' : 'bg-white border border-gray-200'}`}
                          >
                            <div className="flex justify-between items-start">
                              <div>
                                <div className={`text-2xl font-bold ${fueraDeRango ? 'text-red-600' : 'text-gray-800'}`}>
                                  {reg.temperatura}°C
                                  {fueraDeRango && <AlertTriangle className="inline w-5 h-5 ml-1" />}
                                </div>
                                <div className="text-sm text-gray-600">
                                  {getRolLabel(reg.registradoPor)} • {reg.ubicacion || 'Sin ubicación'}
                                </div>
                              </div>
                              <div className="text-xs text-gray-500">
                                {reg.timestamp.toLocaleString()}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
