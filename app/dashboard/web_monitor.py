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
    <title>🤖 RPA Agent Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            background: #10b981;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .agents-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        }
        
        .agent-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .agent-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .agent-status {
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .status-running {
            background: #10b981;
        }
        
        .status-idle {
            background: #6b7280;
        }
        
        .status-error {
            background: #ef4444;
        }
        
        .tasks-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .task-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #10b981;
        }
        
        .task-item.failed {
            border-left-color: #ef4444;
        }
        
        .task-url {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .task-time {
            font-size: 0.85em;
            opacity: 0.7;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 2s infinite;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 RPA Agent Dashboard</h1>
            <p class="status-badge" id="connection-status">Conectando...</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total de Tarefas</div>
                <div class="metric-value" id="total-tasks">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">✅ Completadas</div>
                <div class="metric-value" id="completed-tasks">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">❌ Falhadas</div>
                <div class="metric-value" id="failed-tasks">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">⚙️ Workers Ativos</div>
                <div class="metric-value" id="active-workers">0</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 class="section-title">📊 Performance em Tempo Real</h2>
            <canvas id="performanceChart" width="400" height="100"></canvas>
        </div>
        
        <div class="agents-section">
            <h2 class="section-title">🔧 Agentes Ativos</h2>
            <div id="agents-list">
                <div class="agent-item loading">
                    <span class="agent-name">Carregando agentes...</span>
                </div>
            </div>
        </div>
        
        <div class="tasks-section">
            <h2 class="section-title">📋 Histórico de Tarefas (Tempo Real)</h2>
            <div id="tasks-list">
                <div class="task-item">
                    <div class="task-url">Aguardando tarefas...</div>
                    <div class="task-time">Sistema inicializado</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const tasksData = [];
        let performanceChart;
        
        // Initialize chart
        const ctx = document.getElementById('performanceChart').getContext('2d');
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Tarefas Completadas',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Tarefas Falhadas',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
        
        ws.onopen = () => {
            document.getElementById('connection-status').textContent = '🟢 Conectado';
            document.getElementById('connection-status').style.background = '#10b981';
        };
        
        ws.onclose = () => {
            document.getElementById('connection-status').textContent = '🔴 Desconectado';
            document.getElementById('connection-status').style.background = '#ef4444';
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'initial_state' || data.type === 'metrics_update') {
                updateMetrics(data.metrics);
            }
            
            if (data.type === 'agent_update') {
                updateAgents(data);
            }
            
            if (data.type === 'task_event') {
                addTaskToList(data.event);
                updateMetrics(data.metrics);
                updateChart(data.metrics);
            }
        };
        
        function updateMetrics(metrics) {
            document.getElementById('total-tasks').textContent = metrics.total_tasks;
            document.getElementById('completed-tasks').textContent = metrics.completed_tasks;
            document.getElementById('failed-tasks').textContent = metrics.failed_tasks;
            document.getElementById('active-workers').textContent = metrics.active_workers;
        }
        
        function updateChart(metrics) {
            const now = new Date().toLocaleTimeString();
            performanceChart.data.labels.push(now);
            performanceChart.data.datasets[0].data.push(metrics.completed_tasks);
            performanceChart.data.datasets[1].data.push(metrics.failed_tasks);
            
            if (performanceChart.data.labels.length > 20) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
                performanceChart.data.datasets[1].data.shift();
            }
            
            performanceChart.update();
        }
        
        function updateAgents(data) {
            // Implementar atualização de agentes
        }
        
        function addTaskToList(event) {
            const tasksList = document.getElementById('tasks-list');
            const taskItem = document.createElement('div');
            taskItem.className = `task-item ${event.status === 'failed' ? 'failed' : ''}`;
            
            const icon = event.type === 'task_completed' ? '✅' : 
                        event.type === 'task_failed' ? '❌' : '⏳';
            
            taskItem.innerHTML = `
                <div class="task-url">${icon} ${event.url || 'Task'}</div>
                <div class="task-time">${event.worker || 'Worker'} - ${new Date().toLocaleTimeString()}</div>
            `;
            
            tasksList.insertBefore(taskItem, tasksList.firstChild);
            
            // Limite de 50 itens
            while (tasksList.children.length > 50) {
                tasksList.removeChild(tasksList.lastChild);
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
