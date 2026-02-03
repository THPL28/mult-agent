# Guia de Desenvolvimento

## Configuração do Ambiente

### 1. Clone e Setup

```bash
git clone https://github.com/seu-usuario/mult-agent.git
cd mult-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements_rpa.txt
playwright install chromium
```

### 2. Variáveis de Ambiente

Crie `.env` na raiz:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LOG_LEVEL=INFO
```

## Padrão de Código

### Docstrings (Google Style)

```python
def funcao(param1: str, param2: int) -> Dict[str, Any]:
    """
    Descrição breve da função.
    
    Descrição detalhada se necessário.
    
    Args:
        param1: Descrição do parâmetro 1
        param2: Descrição do parâmetro 2
        
    Returns:
        Dict contendo os resultados
        
    Raises:
        ValueError: Se param1 estiver vazio
        
    Example:
        >>> resultado = funcao("teste", 42)
        >>> print(resultado)
        {'status': 'ok'}
    """
    pass
```

### Type Hints

Sempre usar type hints:

```python
from typing import List, Dict, Optional, Any

def processar(dados: List[str]) -> Optional[Dict[str, Any]]:
    pass
```

### Logging

Usar loguru:

```python
from loguru import logger

logger.info("Mensagem informativa")
logger.warning("Aviso")
logger.error("Erro")
logger.success("Sucesso")
```

## Criando Novo Agente

1. Crie pasta em `app/agents/nome_agente/`
2. Crie `__init__.py` e `agent.py`
3. Siga o template:

```python
"""
Nome do Agente - Descrição
"""

from typing import Dict, Any
from loguru import logger

class NomeAgent:
    """Docstring da classe"""
    
    def __init__(self):
        """Inicialização"""
        logger.info("Agente inicializado")
    
    async def execute(self) -> Dict[str, Any]:
        """Método principal"""
        pass

agent = NomeAgent()
```

## Testes

```bash
# Teste rápido
python test_web_scraper.py

# Pytest
pytest tests/ -v
```

## Git Workflow

1. `git checkout -b feature/nome`
2. Desenvolva
3. `git commit -m "feat: descrição"`
4. `git push origin feature/nome`
5. Abra PR

### Commits Convencionais

- `feat:` nova feature
- `fix:` correção de bug
- `docs:` documentação
- `refactor:` refatoração
- `test:` testes
