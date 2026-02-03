"""
🎨 Web Monitor Dashboard - RPA Agent Real-Time Monitoring
==========================================================

Descrição:
    Interface web em tempo real para monitorar a execução de agentes RPA.
    Fornece visualização de tasks, workers, métricas e logs em tempo real.

Autor: MultiAgent Platform Team
Data: 02/02/2026
Versão: 1.0.0

Tecnologias:
    - FastAPI: Framework web assíncrono
    - WebSockets: Comunicação em tempo real
    - HTML/CSS/JS: Interface do usuário
    - Chart.js: Gráficos de métricas
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import uvicorn
from pathlib import Path


class DashboardManager:
    """
    Gerenciador do Dashboard de Monitoramento
    
    Responsabilidades:
        - Manter conexões WebSocket ativas
        - Broadcast de atualizações para todos os clientes
        - Agregação de métricas de múltiplos agentes
        - Histórico de eventos
    
    Atributos:
        active_connections (List[WebSocket]): Lista de conexões WebSocket ativas
        agent_states (Dict): Estado atual de cada agente
        task_history (List): Histórico de tarefas executadas
        metrics (Dict): Métricas agregadas do sistema
    """
    
    def __init__(self):
        """Inicializa o gerenciador do dashboard"""
        self.active_connections: List[WebSocket] = []
        self.agent_states: Dict[str, Any] = {}
        self.task_history: List[Dict] = []
        self.metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_workers": 0,
            "avg_execution_time": 0.0
        }
    
    async def connect(self, websocket: WebSocket):
        """
        Aceita nova conexão WebSocket
        
        Args:
            websocket (WebSocket): Conexão WebSocket do cliente
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        # Envia estado atual para novo cliente
        await self.send_current_state(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove conexão WebSocket
        
        Args:
            websocket (WebSocket): Conexão a ser removida
        """
        self.active_connections.remove(websocket)
    
    async def send_current_state(self, websocket: WebSocket):
        """
        Envia estado atual do sistema para cliente
        
        Args:
            websocket (WebSocket): Cliente que receberá o estado
        """
        state = {
            "type": "initial_state",
            "agents": self.agent_states,
            "metrics": self.metrics,
            "history": self.task_history[-50:]  # Últimas 50 tarefas
        }
        await websocket.send_json(state)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Envia mensagem para todos os clientes conectados
        
        Args:
            message (Dict): Mensagem a ser enviada
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove conexões que falharam
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    async def update_agent_state(self, agent_id: str, state: Dict[str, Any]):
        """
        Atualiza estado de um agente específico
        
        Args:
            agent_id (str): Identificador do agente
            state (Dict): Novo estado do agente
        """
        self.agent_states[agent_id] = {
            **state,
            "last_update": datetime.now().isoformat()
        }
        
        await self.broadcast({
            "type": "agent_update",
            "agent_id": agent_id,
            "state": self.agent_states[agent_id]
        })
    
    async def add_task_event(self, event: Dict[str, Any]):
        """
        Adiciona evento de tarefa ao histórico
        
        Args:
            event (Dict): Dados do evento
        """
        event["timestamp"] = datetime.now().isoformat()
        self.task_history.append(event)
        
        # Atualiza métricas
        if event.get("type") == "task_started":
            self.metrics["total_tasks"] += 1
        elif event.get("type") == "task_completed":
            self.metrics["completed_tasks"] += 1
        elif event.get("type") == "task_failed":
            self.metrics["failed_tasks"] += 1
        
        await self.broadcast({
            "type": "task_event",
            "event": event,
            "metrics": self.metrics
        })
    
    async def update_worker_count(self, count: int):
        """
        Atualiza contagem de workers ativos
        
        Args:
            count (int): Número de workers ativos
        """
        self.metrics["active_workers"] = count
        await self.broadcast({
            "type": "metrics_update",
            "metrics": self.metrics
        })


# Instância global do gerenciador
dashboard = DashboardManager()

# App FastAPI
app = FastAPI(title="RPA Agent Dashboard", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """
    Retorna página HTML do dashboard
    
    Returns:
        HTMLResponse: Página HTML do dashboard
    """
    html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 MultiAgent Dashboard | RPA Monitoring</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: rgba(22, 27, 34, 0.8);
            --neon-blue: #00d2ff;
            --neon-green: #39ff14;
            --neon-red: #ff3131;
            --neon-purple: #bc13fe;
            --text-color: #e6edf3;
            --border-color: rgba(48, 54, 61, 0.8);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(0, 210, 255, 0.05) 0%, transparent 50%),
                url("https://www.transparenttextures.com/patterns/carbon-fibre.png");
            color: var(--text-color);
            min-height: 100vh;
            overflow-x: hidden;
            padding: 10px 20px;
        }

        /* Fundo de Circuito */
        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: url('https://img.freepik.com/free-vector/digital-technology-circuit-board-background_23-2148404245.jpg?w=1380') center/cover no-repeat;
            opacity: 0.03;
            pointer-events: none;
            z-index: -1;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0 20px 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 20px;
        }

        .status-container {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            background-color: var(--neon-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--neon-green);
            animation: pulse 2s infinite;
        }

        .user-profile {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #30363d;
            border: 1px solid var(--neon-blue);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Main Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            grid-template-rows: auto 1fr;
            gap: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }

        /* Stat Cards */
        .stats-row {
            grid-column: 1 / span 2;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
        }

        .stat-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.3);
        }

        .stat-card::after {
            content: "";
            position: absolute;
            bottom: 0; left: 0; width: 100%; height: 2px;
        }

        .stat-card.blue::after { background: var(--neon-blue); box-shadow: 0 0 15px var(--neon-blue); }
        .stat-card.green::after { background: var(--neon-green); box-shadow: 0 0 15px var(--neon-green); }
        .stat-card.red::after { background: var(--neon-red); box-shadow: 0 0 15px var(--neon-red); }
        .stat-card.purple::after { background: var(--neon-purple); box-shadow: 0 0 15px var(--neon-purple); }

        .icon-box {
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
        }

        .blue .icon-box { border-color: var(--neon-blue); color: var(--neon-blue); }
        .green .icon-box { border-color: var(--neon-green); color: var(--neon-green); }
        .red .icon-box { border-color: var(--neon-red); color: var(--neon-red); }
        .purple .icon-box { border-color: var(--neon-purple); color: var(--neon-purple); }

        .stat-info { display: flex; flex-direction: column; flex-grow: 1; text-align: right; }
        .stat-label { font-size: 12px; opacity: 0.7; display: flex; align-items: center; justify-content: flex-end; gap: 5px; }
        .stat-value { font-size: 32px; font-weight: 700; margin-top: 5px; }

        /* Left Side Charts */
        .left-column { display: flex; flex-direction: column; gap: 20px; }

        .content-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 16px;
            font-weight: 600;
        }

        .chart-container { height: 250px; position: relative; }
        .placeholder-text {
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            opacity: 0.5;
            font-size: 14px;
        }

        /* Agents List */
        .agents-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 200px;
            justify-content: center;
            align-items: center;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(0, 210, 255, 0.1);
            border-top-color: var(--neon-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        /* History Table */
        .history-card { height: 100%; }
        .table-header {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            padding: 10px;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
            opacity: 0.8;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 5px 5px 0 0;
        }

        .history-list {
            margin-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .history-list::-webkit-scrollbar { width: 4px; }
        .history-list::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 10px; }

        .history-item {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            padding: 12px 10px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 6px;
            font-size: 13px;
            align-items: center;
            transition: background 0.2s;
        }

        .history-item:hover { background: rgba(255, 255, 255, 0.06); }
        .status-badge {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            text-align: center;
            width: fit-content;
        }

        .status-success { background: rgba(57, 255, 20, 0.1); color: var(--neon-green); border: 1px solid var(--neon-green); }
        .status-failed { background: rgba(255, 49, 49, 0.1); color: var(--neon-red); border: 1px solid var(--neon-red); }
        .status-pending { background: rgba(0, 210, 255, 0.1); color: var(--neon-blue); border: 1px solid var(--neon-blue); }

        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; filter: brightness(1.2); } 50% { opacity: 0.6; filter: brightness(0.8); } }

        @media (max-width: 1000px) {
            .dashboard-grid { grid-template-columns: 1fr; }
            .stats-row { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <header>
        <div class="status-container">
            <div class="status-dot"></div>
            <span>Conectado</span>
        </div>
        <div class="user-profile">
            <i data-lucide="user" style="width: 18px; color: var(--neon-blue)"></i>
        </div>
    </header>

    <div class="dashboard-grid">
        <!-- Stat Cards -->
        <div class="stats-row">
            <div class="stat-card blue">
                <div class="icon-box"><i data-lucide="layers"></i></div>
                <div class="stat-info">
                    <div class="stat-label"><i data-lucide="layers" style="width:12px"></i> Total de Tarefas</div>
                    <div class="stat-value" id="total-tasks">0</div>
                </div>
            </div>
            <div class="stat-card green">
                <div class="icon-box"><i data-lucide="check-square"></i></div>
                <div class="stat-info">
                    <div class="stat-label"><i data-lucide="check-circle" style="width:12px"></i> Completadas</div>
                    <div class="stat-value" id="completed-tasks">0</div>
                </div>
            </div>
            <div class="stat-card red">
                <div class="icon-box"><i data-lucide="x-circle"></i></div>
                <div class="stat-info">
                    <div class="stat-label"><i data-lucide="alert-circle" style="width:12px"></i> Falhadas</div>
                    <div class="stat-value" id="failed-tasks">0</div>
                </div>
            </div>
            <div class="stat-card purple">
                <div class="icon-box"><i data-lucide="settings"></i></div>
                <div class="stat-info">
                    <div class="stat-label"><i data-lucide="cpu" style="width:12px"></i> Workers Ativos</div>
                    <div class="stat-value" id="active-workers">0</div>
                </div>
            </div>
        </div>

        <!-- Left Column -->
        <div class="left-column">
            <div class="content-card">
                <div class="card-header">
                    <i data-lucide="bar-chart-2" style="color: var(--neon-blue)"></i>
                    Performance em Tempo Real
                </div>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                    <div id="chart-placeholder" class="placeholder-text">Aguardando dados...</div>
                </div>
            </div>

            <div class="content-card">
                <div class="card-header">
                    <i data-lucide="wrench" style="color: var(--neon-blue)"></i>
                    Agentes Ativos
                </div>
                <div class="agents-list" id="agents-info">
                    <div class="spinner"></div>
                    <p style="margin-top: 15px; opacity: 0.7; font-size: 14px;">Carregando lista de agentes...</p>
                </div>
            </div>
        </div>

        <!-- Right Column (History) -->
        <div class="content-card history-card">
            <div class="card-header">
                <i data-lucide="clipboard-list" style="color: var(--neon-blue)"></i>
                Histórico de Tarefas (Tempo Real)
            </div>
            <div class="table-header">
                <span>Nome da Tarefa</span>
                <span>Status</span>
                <span>Timestamp</span>
            </div>
            <div class="history-list" id="tasks-history">
                <div class="placeholder-text" style="display: block; position: relative; padding: 100px 0; text-align: center;">
                    Aguardando tarefas...
                </div>
            </div>
        </div>
    </div>

    <script>
        // Inicializar ícones Lucide
        lucide.createIcons();

        // WebSocket Connection
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
        
        let performanceChart;
        const historyList = document.getElementById('tasks-history');

        // Configuração do Gráfico
        const ctx = document.getElementById('performanceChart').getContext('2d');
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Completas',
                    data: [],
                    borderColor: '#39ff14',
                    backgroundColor: 'rgba(57, 255, 20, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Falhas',
                    data: [],
                    borderColor: '#ff3131',
                    backgroundColor: 'rgba(255, 49, 49, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { 
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: 'rgba(255,255,255,0.5)' }
                    }
                }
            }
        });

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'initial_state' || data.type === 'metrics_update' || data.type === 'task_event') {
                const metrics = data.metrics || (data.type === 'initial_state' ? data.metrics : null);
                if (metrics) {
                    updateCounter('total-tasks', metrics.total_tasks);
                    updateCounter('completed-tasks', metrics.completed_tasks);
                    updateCounter('failed-tasks', metrics.failed_tasks);
                    updateCounter('active-workers', metrics.active_workers);
                    
                    if (data.type === 'task_event') {
                        updateChart(metrics);
                        addTaskToHistory(data.event);
                    }
                }
            }
        };

        function updateCounter(id, value) {
            const el = document.getElementById(id);
            if (el.textContent != value) {
                el.textContent = value;
                el.classList.add('pulse-text');
                setTimeout(() => el.classList.remove('pulse-text'), 500);
            }
        }

        function updateChart(metrics) {
            const placeholder = document.getElementById('chart-placeholder');
            if (placeholder) placeholder.style.display = 'none';

            const now = new Date().toLocaleTimeString();
            performanceChart.data.labels.push(now);
            performanceChart.data.datasets[0].data.push(metrics.completed_tasks);
            performanceChart.data.datasets[1].data.push(metrics.failed_tasks);
            
            if (performanceChart.data.labels.length > 30) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
                performanceChart.data.datasets[1].data.shift();
            }
            performanceChart.update('none');
        }

        function addTaskToHistory(event) {
            // Remover placeholder no primeiro evento
            if (historyList.querySelector('.placeholder-text')) {
                historyList.innerHTML = '';
            }

            const item = document.createElement('div');
            item.className = 'history-item';
            
            const statusClass = event.status === 'success' ? 'status-success' : 
                              event.status === 'failed' ? 'status-failed' : 'status-pending';
            
            const taskName = event.url ? (new URL(event.url).hostname) : 'RPA Task';
            const timestamp = new Date().toLocaleTimeString();

            item.innerHTML = `
                <span style="font-weight: 500;">${taskName}</span>
                <span class="status-badge ${statusClass}">${event.status || 'Pending'}</span>
                <span style="opacity: 0.6;">${timestamp}</span>
            `;

            historyList.insertBefore(item, historyList.firstChild);
            
            if (historyList.children.length > 50) {
                historyList.removeChild(historyList.lastChild);
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para comunicação em tempo real
    
    Args:
        websocket (WebSocket): Conexão WebSocket
        
    Funcionalidade:
        - Aceita conexão
        - Mantém conexão ativa
        - Envia atualizações em tempo real
        - Remove conexão ao desconectar
    """
    await dashboard.connect(websocket)
    try:
        while True:
            # Mantém conexão viva
            data = await websocket.receive_text()
            # Processa comandos do cliente se necessário
    except WebSocketDisconnect:
        dashboard.disconnect(websocket)


@app.get("/api/metrics")
async def get_metrics():
    """
    API endpoint para obter métricas atuais
    
    Returns:
        Dict: Métricas do sistema
    """
    return dashboard.metrics


@app.get("/api/agents")
async def get_agents():
    """
    API endpoint para obter estado dos agentes
    
    Returns:
        Dict: Estado de todos os agentes
    """
    return dashboard.agent_states


def start_dashboard(host: str = "127.0.0.1", port: int = 8000):
    """
    Inicia o servidor do dashboard
    
    Args:
        host (str): Host para bind do servidor
        port (int): Porta para bind do servidor
        
    Uso:
        >>> start_dashboard()
        >>> # Acesse http://localhost:8000
    """
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           🎨 RPA AGENT DASHBOARD STARTED 🎨             ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    📊 Dashboard URL: http://{host}:{port}
    🔌 WebSocket URL: ws://{host}:{port}/ws
    
    Pressione CTRL+C para parar o servidor
    """)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_dashboard()
