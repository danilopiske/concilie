# AGENTCONCILIE.md — Guia IA Completo para Financial  e Stack Moderno

---

## 1. Overview: Legado e Futuro

O **Financial  v2.0** é uma solução robusta de conciliação financeira (MySQL/SQLite), com pipeline de importação, análise, agregação, cálculo e reporting, preparada para ambientes de alta escala e portabilidade. Este documento unifica:
- Descrição funcional
- Fluxos técnicos
- Práticas de desenvolvimento e testes
- Problemas históricos e lições aprendidas
- Regras para agentes IA e contribuintes
- Plano e padrões para migração ao stack web moderno (Next.js + FastAPI)

>  **Meta**: Este markdown é a base viva de inteligência coletiva do projeto e da automação IA — deve ser retroalimentado a cada ciclo de evolução.

---

## 2. Arquitetura Atual — Legado Python
### **Diretórios & Componentes**
- `main.py`: Painel/tela principal, serve UI Panel + integra processamento.
- `modules/`: Views e controle UI (importação, gestão, analista, cálculos, gráficos, relatórios)
- `proc/`: ETL, normalização, bulk insert, classificação, lógica de usuários
- `conf/`: Autenticação, helpers (abstrações SQL camada dual MySQL/SQLite), settings globais
- `relatorios/`: Templates de relatórios
- `dev_tools/`: Scripts CLI para migração, debug, limpeza, análise

### **Banco de Dados**
- MySQL: produção/multiusuário; SQLite: client-side/distribuição
- Tabelas de vendas, recebíveis, análises, controles, logs, clientes, ECs, taxas, users, contextos, de-para
- DECIMAL(18,2) obrigatório para monetários; bulk insert sempre com dtype
- Migração/compatibilidade SQL dual via helpers

---

## 3. Fluxograma e Pipelines Técnicos (Importação→Cálculo→Reporting)

### **Fluxo Principal**
1. **Upload/importação**: Arquivos (.csv/.xls/.xlsx)→detect/cabeçalho→de-para mapeamento→normalização
2. **Classificação:** Filtros inteligentes (termos, status), separação processados/filtrados/diversos
3. **Gravação:** Bulk insert otimizado, dtype/DECIMAL em to_sql; processamentoID único e trackeável
4. **Cálculo:** Multi-layer (taxa específica→taxa genérica→fallback/min/log), agregações, relatórios
5. **Visual e Output:** UI Panel, gráficos Plotly, exportações PDF e dashboards
6. **Validação/Testes:** Automação post-install, checklist multi-modo, troubleshooting guiado e detalhado

### **Checklists Críticos**
- .round(2) aplicado em ETL/insere/antes de gravação
- dtype explícito em Pandas→to_sql
- Validação de consistência pós-importação (valores, log de erros)

---

## 4. Regras Absolutas para Todo Novo Código/Manutenção (AGENTE IA)
### **Sempre Fazer**
- Compatibilidade MySQL+SQLite sempre via helpers/adapters (ex.: _concat_sql, _date_format_sql, etc.)
- Usar DECIMAL(18,2) nas colunas monetárias, nunca DOUBLE/FLOAT/não tipado
- Atualizar sempre este markdown em qualquer refino estrutural/técnico
- Docstring obrigatória em toda função não-trivial
- Teste (manual e, se possível, automatizado) multi-banco
- Movimentar scripts utilitários/experimentos para dev_tools/ ou /scripts

### **Nunca Fazer**
- Assumir SQL puro de apenas um banco
- Cometer DOUBLE/FLOAT para dinheiro (leva a bugs graves!)
- Deixar documentação espalhada ou desatualizada
- Bulk insert sem especificar dtype
- **MOCKAR DADOS - TUDO deve vir do banco de dados (hooks, componentes, testes unitários devem usar API real ou dados de teste no DB)**

### **Armadilhas comuns a evitar**
- Deixar sem .round(2) após conversões monetárias
- Usar placeholders errados (ex.: %s sem adaptar para :param no SQLite)
- Falhar em inicializar variáveis antes de uso em queries dinâmicas
- **Criar hooks/componentes com dados mockados (setTimeout com arrays hardcoded)**
- **Usar dados diferentes entre componentes (sempre mesma fonte: API/DB)**

### **Checklist Padrão de Nova Feature**
- [ ] Dual-path testada (MySQL/SQLite)
- [ ] Docstring/PT-BR
- [ ] decimal/dtype nos inserts
- [ ] Teste manual funcional/ETL completo
- [ ] Documentação / este arquivo atualizado
- [ ] UI cobre cenário (Next.js + Design System)
- [ ] Componentes do Design System utilizados
- [ ] Estados UI previstos (loading, error, disabled, success)
- [ ] Tokens semânticos aplicados (não hard-coded)
- [ ] Acessibilidade validada (labels, aria, keyboard)

---

## 5. Testes, Validação e Troubleshooting ("GUIA_VALIDACAO_TESTES.md" Unificado)

- Modos de execução/teste: SQLite (single user) e MySQL (multiuser)
- Scripts validados em ambientes puros, VM, Sandbox
- Instalação (Poetry), smoke-test (`test_installation.bat`), pós-importação, alternância bancos
- Checklist básico: imports, versões, painel ativo, acesso admin, funções críticas (import, cálculo, relatório)
- Troubleshooting: erros comuns, python/poetry ausente, porta em uso, falha de bulk insert, bugs de arredondamento
- Scripts automação: garantindo setup verde antes de subir/dar manutenção

---

## 6. Diagnóstico Técnico e Lições de Projeto (Análise Crítica)
- Códigos SQL duplicados para MySQL e SQLite devem ser eliminados via abstração
- Atenção a tipos: DECIMAL sempre para dinheiro, VARCHAR para campos indexáveis
- Consistência de queries: usar sempre helpers, nunca string SQL "pura" para funcionalidades
- Todos os pontos fortes, riscos e métricas históricas em documentação (ver analisedeprojeto_completa.md)
- Logs e controles: logging de bugs críticos, automação de checagens e recálculo
- **LIÇÃO CRÍTICA (Jan/2026)**: Hook `useECs` estava mockado com `['1234567890', '0987654321', '1111111111']` via setTimeout, causando inconsistência entre página principal e modal. SOLUÇÃO: Sempre usar API real `/clientes/{id}/ecs`. REGRA: NUNCA mockar dados em hooks/componentes - apenas em testes isolados se absolutamente necessário.

---

## 7. AGENTE IA: Premissas e Diretrizes Herméticas
- Todas novas funções para banco/ETL/cálculo devem prever via helper SQL adapter
- Qualquer bug, aprendizado, workaround post-mortem → atualizar este markdown
- Lista viva de boas práticas, erros históricos e workflows:
    - .round(2) sempre!
    - dtype DECIMAL obrigatório
    - placeholders SQL adaptativos
    - separação clara de UI, core, banco e settings
    - **FRONTEND: Seguir obrigatoriamente UI Design System (seção 10)**
    - **COMPONENTES: Reutilizar existentes, nunca criar do zero sem justificativa**
    - **ESTADOS: Prever loading, error, disabled, success em toda UI**
- Sempre sugerir *docstring clara*, *exemplo de uso* e atualizar README/agent.
- **UI/UX**: Consultar `.github/agents/ui-design-system-nextjs.md` ANTES de criar qualquer componente Next.js

---

## 8. **Stack Moderno: Next.js + TypeScript + FastAPI + Poetry + pnpm**

### **8.0. Alternância de Banco de Dados (SQLite ↔ MySQL)**

O sistema moderno suporta alternância fácil entre SQLite (single-user) e MySQL (multi-user):

#### **Arquivos de Configuração**
```
apps/api/
├─ .env                # Arquivo ativo (gerado pelos scripts)
├─ .env.sqlite         # Template para SQLite
├─ .env.mysql          # Template para MySQL
└─ .env.example        # Exemplo geral
```

#### **Scripts de Alternância**

**1. Configurar Banco (Primeiro uso):**
```powershell
# Execute no diretório raiz:
"Configurar Stack Moderno.bat"
```
Menu interativo:
- [1] SQLite - Copia `.env.sqlite` → `.env`
- [2] MySQL - Copia `.env.mysql` → `.env` + solicita configuração de senha
- [3] Cancelar

**2. Iniciar Sistema (Após configurar):**
```powershell
# Para SQLite:
"Iniciar Stack Moderno - SQLite.bat"

# Para MySQL:
"Iniciar Stack Moderno - MySQL.bat"
```

Ambos scripts:
- ✅ Verificam dependências (Poetry, pnpm)
- ✅ Verificam configuração do .env
- ✅ Verificam serviço MySQL (apenas modo MySQL)
- ✅ Abrem 2 terminais automaticamente (Backend + Frontend)

#### **Estrutura do .env**

**`.env.sqlite` (Template SQLite):**
```env
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=../../data/concilie.db
MYSQL_SERVER=localhost       # Não usado
MYSQL_PORT=3306              # Não usado
MYSQL_USER=root              # Não usado
MYSQL_PASSWORD=              # Não usado
MYSQL_DB=bd_conciliacao      # Não usado
```

**`.env.mysql` (Template MySQL):**
```env
DATABASE_TYPE=mysql
SQLITE_DB_PATH=../../data/concilie.db  # Não usado
MYSQL_SERVER=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=              # ← CONFIGURE AQUI
MYSQL_DB=bd_conciliacao
```

**IMPORTANTE:**
- Variável `DATABASE_TYPE` controla qual banco é usado
- Backend lê `.env` e conecta ao banco apropriado via `conf/funcoesbd.py`
- Após alternar, **sempre reinicie o backend**

#### **Fluxo de Uso**

**Primeira vez (Setup):**
1. Execute `Configurar Stack Moderno.bat`
2. Escolha SQLite ou MySQL
3. Se MySQL, configure senha no `.env` quando solicitado
4. Pronto! Arquivo `.env` criado

**Alternar banco (depois):**
1. Feche backend (Ctrl+C no terminal)
2. Execute `Configurar Stack Moderno.bat` novamente
3. Escolha novo banco
4. Execute `Iniciar Stack Moderno - [SQLite/MySQL].bat`

**Verificar qual banco está ativo:**
```powershell
type apps\api\.env | findstr DATABASE_TYPE
# Saída: DATABASE_TYPE=sqlite ou DATABASE_TYPE=mysql
```

#### **Troubleshooting**

**Erro: "MySQL not running"**
```powershell
# Iniciar serviço MySQL:
net start MySQL80

# Ou via MySQL Workbench
```

**Erro: "Access denied for user 'root'"**
- Edite `apps\api\.env`
- Corrija `MYSQL_PASSWORD=sua_senha_correta`
- Reinicie backend

**Backend conectando no banco errado:**
- Verifique `DATABASE_TYPE` em `apps\api\.env`
- Execute `Configurar Stack Moderno.bat` para recriar `.env`

---

### **8.1. Gerenciamento de Dependências**

#### **Poetry (Backend Python)**
```bash
# Instalação
curl -sSL https://install.python-poetry.org | python3 -

# Inicializar projeto
poetry init

# Adicionar dependências
poetry add fastapi uvicorn sqlalchemy pandas pydantic-settings
poetry add --group dev pytest black ruff mypy

# Instalar dependências
poetry install

# Executar comandos
poetry run python main.py
poetry run pytest
```

**pyproject.toml exemplo:**
```toml
[tool.poetry]
name = "financial--api"
version = "2.0.0"
description = "API FastAPI para Financial "
authors = ["Seu Nome <email@exemplo.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
pandas = "^2.2.0"
pydantic = "^2.6.0"
pydantic-settings = "^2.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
black = "^24.1.0"
ruff = "^0.2.0"
mypy = "^1.8.0"

[tool.poetry.scripts]
dev = "uvicorn app.main:app --reload"
start = "uvicorn app.main:app --host 0.0.0.0 --port 8000"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### **pnpm (Frontend Node.js)**
```bash
# Instalação
npm install -g pnpm

# Inicializar projeto
pnpm init

# Adicionar dependências
pnpm add next react react-dom
pnpm add -D typescript @types/react @types/node eslint prettier

# Instalar dependências
pnpm install

# Scripts
pnpm dev
pnpm build
pnpm start
```

**package.json exemplo:**
```json
{
  "name": "financial--web",
  "version": "2.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "@types/node": "^20.11.16",
    "@types/react": "^18.2.52",
    "@types/react-dom": "^18.2.18",
    "typescript": "^5.3.3",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.1.0",
    "prettier": "^3.2.4"
  }
}
```

---

### **8.2. Backend FastAPI Modularizado**

**Estrutura de Diretórios:**
```
apps/api/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                 # Entry point FastAPI
│  ├─ config/
│  │  ├─ __init__.py
│  │  ├─ settings.py          # Configurações com pydantic-settings
│  │  └─ database.py          # Conexão DB
│  ├─ models/                 # SQLAlchemy models
│  │  ├─ __init__.py
│  │  ├─ vendas.py
│  │  ├─ recebiveis.py
│  │  └─ usuarios.py
│  ├─ schemas/                # Pydantic schemas (DTOs)
│  │  ├─ __init__.py
│  │  ├─ vendas.py
│  │  ├─ recebiveis.py
│  │  └─ auth.py
│  ├─ api/                    # Rotas/endpoints
│  │  ├─ __init__.py
│  │  ├─ deps.py              # Dependências compartilhadas
│  │  └─ v1/
│  │     ├─ __init__.py
│  │     ├─ api.py            # Router principal v1
│  │     └─ endpoints/
│  │        ├─ vendas.py
│  │        ├─ recebiveis.py
│  │        ├─ calculos.py
│  │        └─ auth.py
│  ├─ services/               # Lógica de negócio
│  │  ├─ __init__.py
│  │  ├─ vendas_service.py
│  │  ├─ calculos_service.py
│  │  └─ etl_service.py
│  ├─ repositories/           # Acesso a dados (Repository pattern)
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  ├─ vendas_repository.py
│  │  └─ recebiveis_repository.py
│  └─ utils/
│     ├─ __init__.py
│     ├─ sql_adapters.py      # Adaptadores MySQL/SQLite
│     ├─ validators.py
│     └─ formatters.py
├─ tests/
│  ├─ __init__.py
│  ├─ conftest.py
│  ├─ test_vendas.py
│  └─ test_calculos.py
├─ alembic/                   # Migrações DB
├─ pyproject.toml
├─ poetry.lock
└─ README.md
```

**app/main.py:**
```python
"""
Entry point da aplicação FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

**app/config/settings.py:**
```python
"""
Configurações da aplicação usando Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Financial  API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DB_TYPE: str = "mysql"  # mysql ou sqlite
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**app/api/v1/endpoints/vendas.py:**
```python
"""
Endpoints de vendas
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.vendas import VendaCreate, VendaResponse
from app.services.vendas_service import VendasService

router = APIRouter()

@router.post("/", response_model=VendaResponse, status_code=201)
async def criar_venda(
    venda: VendaCreate,
    db: Session = Depends(get_db)
):
    """
    Criar nova venda
    """
    service = VendasService(db)
    return await service.criar_venda(venda)

@router.get("/{venda_id}", response_model=VendaResponse)
async def obter_venda(
    venda_id: int,
    db: Session = Depends(get_db)
):
    """
    Obter venda por ID
    """
    service = VendasService(db)
    venda = await service.obter_venda(venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda
```

**app/services/vendas_service.py:**
```python
"""
Serviço de vendas - lógica de negócio
"""
from sqlalchemy.orm import Session
from app.repositories.vendas_repository import VendasRepository
from app.schemas.vendas import VendaCreate
from decimal import Decimal

class VendasService:
    def __init__(self, db: Session):
        self.repository = VendasRepository(db)
    
    async def criar_venda(self, venda: VendaCreate):
        """
        Criar venda com validações e normalizações
        """
        # Normalizar valor (sempre DECIMAL com .round(2))
        venda.valor = Decimal(str(venda.valor)).quantize(Decimal('0.01'))
        
        # Validar dados
        if venda.valor <= 0:
            raise ValueError("Valor deve ser positivo")
        
        # Criar no repositório
        return await self.repository.create(venda)
```

**app/repositories/base.py:**
```python
"""
Repository base com operações CRUD genéricas
"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[ModelType]:
        """Buscar por ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Listar todos com paginação"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    async def create(self, obj_in: dict) -> ModelType:
        """Criar novo registro"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """Atualizar registro"""
        db_obj = await self.get(id)
        if db_obj:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> bool:
        """Deletar registro"""
        db_obj = await self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
```

**app/repositories/vendas_repository.py:**
```python
"""
Repository de vendas
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.vendas import Venda

class VendasRepository(BaseRepository[Venda]):
    def __init__(self, db: Session):
        super().__init__(Venda, db)
    
    async def get_by_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime
    ) -> List[Venda]:
        """Buscar vendas por período"""
        return self.db.query(Venda).filter(
            and_(
                Venda.data >= data_inicio,
                Venda.data <= data_fim
            )
        ).all()
    
    async def get_by_status(self, status: str) -> List[Venda]:
        """Buscar vendas por status"""
        return self.db.query(Venda).filter(Venda.status == status).all()
    
    async def calcular_total_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime
    ) -> float:
        """Calcular total de vendas no período"""
        from sqlalchemy import func
        result = self.db.query(
            func.sum(Venda.valor_venda)
        ).filter(
            and_(
                Venda.data >= data_inicio,
                Venda.data <= data_fim
            )
        ).scalar()
        return float(result) if result else 0.0
```

**app/models/vendas.py:**
```python
"""
Model SQLAlchemy de vendas
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class Venda(Base):
    __tablename__ = "vendas_processadas"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(DateTime, nullable=False, index=True)
    valor_venda = Column(DECIMAL(18, 2), nullable=False)
    valor_liquido = Column(DECIMAL(18, 2))
    status = Column(String(50), index=True)
    tipo_transacao = Column(String(100))
    bandeira = Column(String(50))
    autorizacao = Column(String(100))
    nsu = Column(String(100), unique=True)
    
    # Relacionamentos
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    cliente = relationship("Cliente", back_populates="vendas")
    
    processamento_id = Column(Integer, ForeignKey("processamentos.id"))
    processamento = relationship("Processamento", back_populates="vendas")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Venda(id={self.id}, data={self.data}, valor={self.valor_venda})>"
```

**app/models/base.py:**
```python
"""
Base model para SQLAlchemy
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**app/schemas/vendas.py:**
```python
"""
Pydantic schemas para vendas
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional

class VendaBase(BaseModel):
    """Schema base de venda"""
    data: datetime
    valor_venda: Decimal = Field(..., decimal_places=2)
    tipo_transacao: Optional[str] = None
    bandeira: Optional[str] = None
    status: str = "processado"

class VendaCreate(VendaBase):
    """Schema para criação de venda"""
    cliente_id: int
    
    @validator('valor_venda')
    def validar_valor(cls, v):
        """Garantir valor positivo e arredondado"""
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return Decimal(str(v)).quantize(Decimal('0.01'))

class VendaUpdate(BaseModel):
    """Schema para atualização de venda"""
    valor_venda: Optional[Decimal] = None
    status: Optional[str] = None
    valor_liquido: Optional[Decimal] = None
    
    @validator('valor_venda', 'valor_liquido')
    def validar_valores(cls, v):
        """Arredondar valores decimais"""
        if v is not None:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v

class VendaResponse(VendaBase):
    """Schema de resposta de venda"""
    id: int
    valor_liquido: Optional[Decimal] = None
    nsu: Optional[str] = None
    autorizacao: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Para compatibilidade com SQLAlchemy
```

**app/config/database.py:**
```python
"""
Configuração de conexão com banco de dados
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
from app.models.base import Base
from typing import Generator

# Criar engine com configurações apropriadas
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DB_ECHO if hasattr(settings, 'DB_ECHO') else False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Criar todas as tabelas
    """
    Base.metadata.create_all(bind=engine)
```

**app/api/deps.py:**
```python
"""
Dependências compartilhadas para endpoints
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.config.database import get_db
from app.config.settings import settings
from app.models.usuarios import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:
    """
    Obter usuário autenticado do token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Verificar se usuário está ativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user
```

**app/api/v1/api.py:**
```python
"""
Router principal da API v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import vendas, recebiveis, calculos, auth

api_router = APIRouter()

# Incluir todos os routers
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["autenticação"]
)
api_router.include_router(
    vendas.router, 
    prefix="/vendas", 
    tags=["vendas"]
)
api_router.include_router(
    recebiveis.router, 
    prefix="/recebiveis", 
    tags=["recebíveis"]
)
api_router.include_router(
    calculos.router, 
    prefix="/calculos", 
    tags=["cálculos"]
)
```

**app/utils/sql_adapters.py:**
```python
"""
Adaptadores SQL para compatibilidade MySQL/SQLite
"""
from sqlalchemy import engine

def _is_sqlite(eng) -> bool:
    """Verificar se é SQLite"""
    return 'sqlite' in str(eng.url)

def _is_mysql(eng) -> bool:
    """Verificar se é MySQL"""
    return 'mysql' in str(eng.url)

def _concat_sql(eng, *args) -> str:
    """
    Concatenação de strings SQL compatível
    """
    if _is_sqlite(eng):
        return ' || '.join(args)
    return f"CONCAT({', '.join(args)})"

def _date_format_sql(eng, date_column: str, format_str: str) -> str:
    """
    Formatação de data SQL compatível
    """
    if _is_sqlite(eng):
        # SQLite usa strftime
        return f"strftime('{format_str}', {date_column})"
    # MySQL usa DATE_FORMAT
    return f"DATE_FORMAT({date_column}, '{format_str}')"

def _substring_sql(eng, column: str, start: int, length: int) -> str:
    """
    Substring SQL compatível
    """
    if _is_sqlite(eng):
        return f"SUBSTR({column}, {start}, {length})"
    return f"SUBSTRING({column}, {start}, {length})"

def _current_timestamp_sql(eng) -> str:
    """
    Timestamp atual SQL compatível
    """
    if _is_sqlite(eng):
        return "CURRENT_TIMESTAMP"
    return "NOW()"

def get_placeholder(eng, index: int = 1) -> str:
    """
    Retornar placeholder correto para o banco
    MySQL: %s
    SQLite: ?
    """
    if _is_sqlite(eng):
        return "?"
    return "%s"
```

---

### **8.3. Frontend Next.js + TypeScript Modularizado**

**Estrutura de Diretórios:**
```
apps/web/
├─ app/                       # App Router (Next.js 13+)
│  ├─ layout.tsx
│  ├─ page.tsx
│  ├─ (auth)/
│  │  ├─ login/
│  │  │  └─ page.tsx
│  │  └─ layout.tsx
│  ├─ (dashboard)/
│  │  ├─ vendas/
│  │  │  ├─ page.tsx
│  │  │  └─ [id]/
│  │  │     └─ page.tsx
│  │  ├─ recebiveis/
│  │  │  └─ page.tsx
│  │  ├─ calculos/
│  │  │  └─ page.tsx
│  │  └─ layout.tsx
│  └─ api/                    # API Routes (opcional)
│     └─ health/
│        └─ route.ts
├─ components/
│  ├─ ui/                     # Componentes base
│  │  ├─ Button.tsx
│  │  ├─ Input.tsx
│  │  ├─ Table.tsx
│  │  └─ Card.tsx
│  ├─ layout/                 # Layout components
│  │  ├─ Header.tsx
│  │  ├─ Sidebar.tsx
│  │  └─ Footer.tsx
│  ├─ vendas/                 # Componentes de vendas
│  │  ├─ VendasTable.tsx
│  │  ├─ VendaForm.tsx
│  │  └─ VendaCard.tsx
│  └─ shared/                 # Componentes compartilhados
│     ├─ Loading.tsx
│     └─ ErrorBoundary.tsx
├─ lib/
│  ├─ api/                    # Cliente API
│  │  ├─ client.ts
│  │  ├─ vendas.ts
│  │  ├─ recebiveis.ts
│  │  └─ auth.ts
│  ├─ hooks/                  # Custom hooks
│  │  ├─ useVendas.ts
│  │  ├─ useAuth.ts
│  │  └─ useDebounce.ts
│  ├─ utils/
│  │  ├─ formatters.ts
│  │  ├─ validators.ts
│  │  └─ constants.ts
│  └─ types/                  # TypeScript types
│     ├─ vendas.ts
│     ├─ recebiveis.ts
│     └─ api.ts
├─ public/
├─ styles/
│  └─ globals.css
├─ package.json
├─ tsconfig.json
├─ next.config.js
└─ .env.local
```

**lib/api/client.ts:**
```typescript
/**
 * Cliente API base
 */
import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirecionar para login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**lib/api/vendas.ts:**
```typescript
/**
 * API de vendas
 */
import { apiClient } from './client';
import { Venda, VendaCreate } from '@/lib/types/vendas';

export const vendasApi = {
  async listar(): Promise<Venda[]> {
    const { data } = await apiClient.get<Venda[]>('/vendas');
    return data;
  },

  async obter(id: number): Promise<Venda> {
    const { data } = await apiClient.get<Venda>(`/vendas/${id}`);
    return data;
  },

  async criar(venda: VendaCreate): Promise<Venda> {
    const { data } = await apiClient.post<Venda>('/vendas', venda);
    return data;
  },

  async atualizar(id: number, venda: Partial<Venda>): Promise<Venda> {
    const { data } = await apiClient.put<Venda>(`/vendas/${id}`, venda);
    return data;
  },

  async deletar(id: number): Promise<void> {
    await apiClient.delete(`/vendas/${id}`);
  },
};
```

**lib/hooks/useVendas.ts:**
```typescript
/**
 * Hook para gerenciar vendas
 */
import { useState, useEffect } from 'react';
import { vendasApi } from '@/lib/api/vendas';
import { Venda } from '@/lib/types/vendas';

export function useVendas() {
  const [vendas, setVendas] = useState<Venda[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVendas = async () => {
    try {
      setLoading(true);
      const data = await vendasApi.listar();
      setVendas(data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar vendas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendas();
  }, []);

  return { vendas, loading, error, refetch: fetchVendas };
}
```

**components/vendas/VendasTable.tsx:**
```typescript
/**
 * Tabela de vendas
 */
'use client';

import { useVendas } from '@/lib/hooks/useVendas';
import { formatCurrency, formatDate } from '@/lib/utils/formatters';

export function VendasTable() {
  const { vendas, loading, error } = useVendas();

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;

  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>ID</th>
          <th>Data</th>
          <th>Valor</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {vendas.map((venda) => (
          <tr key={venda.id}>
            <td>{venda.id}</td>
            <td>{formatDate(venda.data)}</td>
            <td>{formatCurrency(venda.valor)}</td>
            <td>{venda.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### **8.4. Monorepo: Integração Completa**

**Estrutura Monorepo:**
```
financial-/
├─ apps/
│  ├─ web/                    # Next.js + TypeScript
│  │  ├─ package.json
│  │  └─ ...
│  └─ api/                    # FastAPI + Poetry
│     ├─ pyproject.toml
│     └─ ...
├─ packages/
│  ├─ shared-types/           # Types compartilhados
│  │  ├─ package.json
│  │  └─ index.ts
│  ├─ ui/                     # Component library
│  │  ├─ package.json
│  │  └─ components/
│  └─ config/                 # Configs compartilhadas
│     ├─ eslint-config/
│     └─ tsconfig/
├─ .github/
│  └─ workflows/
│     ├─ ci-web.yml
│     └─ ci-api.yml
├─ package.json               # Root package.json (pnpm workspace)
├─ pnpm-workspace.yaml
├─ turbo.json
└─ README.md
```

**pnpm-workspace.yaml:**
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**turbo.json:**
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "test": {
      "dependsOn": ["^build"]
    }
  }
}
```

**Root package.json:**
```json
{
  "name": "financial--monorepo",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "lint": "turbo run lint",
    "test": "turbo run test",
    "web:dev": "pnpm --filter web dev",
    "api:dev": "cd apps/api && poetry run dev"
  },
  "devDependencies": {
    "turbo": "^1.11.0",
    "prettier": "^3.2.4"
  },
  "packageManager": "pnpm@8.15.0"
}
```

---

### **8.5. Referências e Recursos**

#### **Documentação Oficial**
- [Poetry Documentation](https://python-poetry.org/docs/)
- [pnpm Documentation](https://pnpm.io/)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TurboRepo Documentation](https://turbo.build/repo/docs)

#### **Templates e Boilerplates**
- [Next.js FastAPI Template](https://nextfastapi.com/)
- [FastAPI Full Stack Template](https://github.com/tiangolo/full-stack-fastapi-template)
- [Next.js Boilerplate](https://github.com/vercel/next.js/tree/canary/examples)

#### **Ferramentas de Desenvolvimento**
- [openapi-typescript-codegen](https://github.com/ferdikoomen/openapi-typescript-codegen) - Gerar tipos TS do OpenAPI
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM Python
- [Alembic](https://alembic.sqlalchemy.org/) - Migrações de banco
- [Pytest](https://docs.pytest.org/) - Testes Python
- [Vitest](https://vitest.dev/) - Testes JavaScript/TypeScript

---

### **8.6. Melhores Práticas para o Agente IA**

#### **Backend (FastAPI + Poetry)**
- ✅ Sempre usar type hints em todas as funções
- ✅ Pydantic para validação de dados (schemas)
- ✅ Repository pattern para acesso a dados
- ✅ Service layer para lógica de negócio
- ✅ Async/await para operações I/O
- ✅ Testes com pytest e coverage > 80%
- ✅ DECIMAL(18,2) para valores monetários
- ✅ Docstrings em todas funções públicas

#### **Frontend (Next.js + TypeScript)**
- ✅ Componentes funcionais com TypeScript
- ✅ Custom hooks para lógica reutilizável
- ✅ Separação de concerns (UI/logic/data)
- ✅ Error boundaries para tratamento de erros
- ✅ Loading states em todas operações async
- ✅ Validação de formulários com Zod ou Yup
- ✅ Formatação consistente (Prettier + ESLint)
- ✅ Types gerados automaticamente do backend
- ❌ **NUNCA MOCKAR DADOS - Sempre usar API real (apiClient) mesmo em desenvolvimento**
- ✅ **SEGUIR OBRIGATORIAMENTE: [UI Design System](./ui-design-system-nextjs.md)**

#### **UI/UX (Design System Corporativo)**
**Referência Principal:** `.github/agents/ui-design-system-nextjs.md`

**Regras Absolutas:**
- ❌ NUNCA criar estilos inline
- ❌ NUNCA criar novos padrões visuais sem documentar
- ✅ SEMPRE reutilizar componentes existentes
- ✅ SEMPRE prever estados (loading, error, disabled, success)
- ✅ CLAREZA > estética (sistema fiscal/corporativo)

**Componentes Obrigatórios:**
1. **Button**
   - Variantes: `primary`, `secondary`, `success`, `text`, `icon`, `small`
   - Estados: default, hover, disabled, loading
   - Regra: Apenas 1 botão primary por tela
   - Loading state desabilita clique automaticamente

2. **InputText**
   - Variantes: `text`, `email`, `password`, `cnpj_raiz`, `textarea`
   - Estados: default, focus, disabled, error
   - Label obrigatório, placeholder instrutivo

3. **FileUpload**
   - Estados: empty, selected, loading, error
   - Mostrar tipos aceitos e nome do arquivo
   - Nunca processar automaticamente

4. **Table**
   - Variantes: `simple`, `info`
   - Sempre com headers claros
   - Suporte a ordenação e paginação

5. **Card**
   - Variantes: `default`, `success`, `disabled`
   - Usar para agrupamento lógico de dados

6. **Alert**
   - Variantes: `info`, `success`, `error`
   - Mensagens de erro devem orientar ação corretiva

7. **Stepper**
   - Uso obrigatório em fluxos longos e processamento fiscal
   - Estados: pending, active, completed, error

**Tokens Semânticos (NÃO usar cores diretas):**
```typescript
// Cores
color.primary      // Ações principais
color.secondary    // Ações alternativas
color.success      // Sucesso/confirmação
color.error        // Erro/alerta
color.info         // Informação
color.disabled     // Desabilitado

// Espaçamento
spacing.xs | sm | md | lg | xl

// Radius
radius.sm | md

// Fontes
font.body | label | title
```

**Padrões de Telas:**

*Formulário Padrão:*
```typescript
<Page>
  <Title>Nome da Funcionalidade</Title>
  <Form>
    <InputText label="Campo" />
    <Alert variant="info">Instrução clara</Alert>
    <ButtonGroup>
      <Button variant="secondary">Cancelar</Button>
      <Button variant="primary" loading={isLoading}>Confirmar</Button>
    </ButtonGroup>
  </Form>
</Page>
```

*Processamento/Importação:*
```typescript
<Page>
  <Stepper steps={['Upload', 'Validação', 'Processamento', 'Resultado']} current={step} />
  <Card>
    <FileUpload disabled={isProcessing} />
    <Alert variant={alertType}>{message}</Alert>
  </Card>
  <Button variant="primary" disabled={!canProcess}>Processar</Button>
</Page>
```

*Resultado/Listagem:*
```typescript
<Page>
  <Card variant="success">
    <Stats />
  </Card>
  <Table data={results} />
  <Button variant="text" icon="download">Exportar</Button>
</Page>
```

**Acessibilidade (A11y):**
- Focus visível em todos elementos interativos
- Labels sempre associados a inputs
- `aria-label` em ícones e botões sem texto
- Não depender apenas de cor para comunicar estado
- Suporte a navegação por teclado

**Workflow para Agents (CRÍTICO):**
1. **Antes de criar JSX:** Mapear componentes do Design System
2. **Escolher variante + estado:** Baseado no contexto (formulário, tabela, etc.)
3. **Usar tokens semânticos:** Nunca cores/espaços hard-coded
4. **Documentar novo componente:** Se não existir, documentar ANTES de criar
5. **Validar estados:** Loading, error, disabled, success

**Checklist UI (Nova Feature):**
- [ ] Componentes do Design System utilizados?
- [ ] Tokens semânticos aplicados (não hard-coded)?
- [ ] Estados previstos (loading, error, disabled)?
- [ ] Labels e aria-labels presentes?
- [ ] Padrão de tela documentado seguido?
- [ ] Apenas 1 botão primary na tela?
- [ ] Mensagens de erro são acionáveis?

**Erro Comum a Evitar:**
```typescript
// ❌ ERRADO
<button style={{backgroundColor: '#007bff', padding: '10px'}}>
  Salvar
</button>

// ✅ CORRETO
<Button variant="primary" loading={isSaving}>
  Salvar
</Button>
```

#### **Integração**
- ✅ OpenAPI spec sempre atualizado
- ✅ CI/CD para ambos apps (web + api)
- ✅ Versionamento semântico
- ✅ Changelog mantido atualizado
- ✅ Environment variables com .env
- ✅ Docker compose para desenvolvimento local
- ✅ Documentação técnica atualizada
---

## 9. Apêndices: Snippets, Troubleshootings, Workflows, Casos de Uso

### **Exemplo Adaptador SQL Universal**
```python
def _concat_sql(engine, *args):
    if _is_sqlite(engine):
        return ' || '.join(args)
    return f"CONCAT({', '.join(args)})"
```

### **Bulk Insert Pandas to_sql (corrigir bug monetário)**
```python
from sqlalchemy.types import DECIMAL
df.to_sql(
    'vendas_processadas',
    con=engine,
    dtype={'Valor_da_venda': DECIMAL(18,2), ...},
    method='multi',
    if_exists='append',
    index=False
)
```

### **Checklist Pós-Deploy/Importação**
- [ ] Teste SQLite e MySQL ok?
- [ ] Tipagem dos dados monetários? Não há DOUBLE?
- [ ] Scripts & docs ok e versionados?
- [ ] Teste manual função crítica/processamento?
- [ ] AI/engine atualizado/escrito no agent.md?
- [ ] UI seguindo Design System? (componentes, tokens, estados)
- [ ] Acessibilidade validada? (labels, aria, keyboard, focus)

---

## 10. UI Design System - Regras para Desenvolvimento Frontend

### **10.1. Documento de Referência**
**Localização:** `.github/agents/ui-design-system-nextjs.md`

Este documento é a **fonte única de verdade** para toda interface Next.js. Deve ser consultado antes de criar qualquer componente ou tela.

### **10.2. Princípios Fundamentais**

**Contexto Técnico:**
- Framework: Next.js (App Router)
- Linguagem: TypeScript
- Paradigma: Componentes reutilizáveis
- Domínio: Sistema corporativo/fiscal/financeiro

**Filosofia:**
- **CLAREZA > ESTÉTICA**: Sistema fiscal exige informação clara, não design "bonito"
- **PREVISIBILIDADE**: Mesma ação, mesmo componente, mesmo resultado
- **CONSISTÊNCIA**: Padrões visuais fixos em todo o sistema

### **10.3. Regras Globais (Invioláveis)**

```typescript
// ❌ PROIBIDO
const MyComponent = () => (
  <div style={{color: '#FF0000', padding: '20px'}}>
    <button onClick={handleClick}>Click</button>
  </div>
);

// ✅ OBRIGATÓRIO
const MyComponent = () => {
  const [loading, setLoading] = useState(false);
  
  return (
    <Card>
      <Button 
        variant="primary" 
        loading={loading}
        onClick={handleClick}
      >
        Processar
      </Button>
    </Card>
  );
};
```

**Nunca:**
- Criar estilos inline
- Criar novos padrões visuais sem documentar
- Ignorar estados (loading, error, disabled)
- Usar cores/espaçamentos hard-coded

**Sempre:**
- Reutilizar componentes existentes
- Prever todos os estados possíveis
- Usar tokens semânticos
- Validar acessibilidade

### **10.4. Biblioteca de Componentes**

#### **Button - Botões de Ação**
```typescript
<Button 
  variant="primary"     // primary | secondary | success | text | icon | small
  loading={isLoading}   // Desabilita automaticamente
  disabled={!canSave}
  onClick={handleSave}
>
  Salvar
</Button>
```

**Regras:**
- Apenas **1 botão primary** por tela (ação principal)
- Loading state desabilita clique
- Texto deve ser verbo de ação (Salvar, Processar, Exportar)

---

#### **InputText - Campos de Entrada**
```typescript
<InputText
  label="CNPJ"              // Obrigatório
  variant="cnpj_raiz"       // text | email | password | cnpj_raiz | textarea
  value={cnpj}
  onChange={setCnpj}
  error={errors.cnpj}       // Mostra mensagem de erro
  disabled={isProcessing}
  placeholder="00.000.000/0001-00"
/>
```

**Regras:**
- Label sempre presente
- Placeholder instrutivo (exemplo de formato)
- Mensagem de erro acionável

---

#### **FileUpload - Upload de Arquivos**
```typescript
<FileUpload
  accept=".csv,.xlsx"
  onFileSelect={handleFile}
  loading={isUploading}
  error={uploadError}
  selectedFile={file}
/>
```

**Regras:**
- Mostrar tipos aceitos visualmente
- Mostrar nome do arquivo selecionado
- NUNCA processar automaticamente (sempre aguardar confirmação)

---

#### **Table - Tabelas de Dados**
```typescript
<Table
  variant="simple"        // simple | info
  columns={[
    { key: 'id', label: 'ID', sortable: true },
    { key: 'valor', label: 'Valor', format: 'currency' }
  ]}
  data={vendas}
  onSort={handleSort}
  pagination={pagination}
/>
```

**Regras:**
- Headers sempre claros
- Suporte a ordenação e paginação
- Formatação automática (currency, date, etc.)

---

#### **Card - Agrupamento de Conteúdo**
```typescript
<Card variant="success">   // default | success | disabled
  <h3>Processamento Concluído</h3>
  <Stats data={result} />
</Card>
```

---

#### **Alert - Mensagens ao Usuário**
```typescript
<Alert variant="error">    // info | success | error
  Erro ao processar arquivo. Verifique o formato e tente novamente.
</Alert>
```

**Regras:**
- Mensagens de erro devem orientar ação corretiva
- Nunca apenas "Erro ocorreu" - explicar O QUE fazer

---

#### **Stepper - Fluxos Multi-Etapas**
```typescript
<Stepper
  steps={['Upload', 'Validação', 'Processamento', 'Resultado']}
  currentStep={step}
  stepStatus={status}      // pending | active | completed | error
/>
```

**Uso obrigatório em:**
- Importação de arquivos
- Processamento fiscal
- Cálculos multi-etapa

---

### **10.5. Tokens Semânticos (Design Tokens)**

**NUNCA usar valores diretos:**
```typescript
// ❌ ERRADO
<div style={{color: '#007bff', marginTop: '20px'}}>

// ✅ CORRETO
<div className={styles.primaryText} style={{marginTop: spacing.md}}>
```

**Cores:**
```typescript
color.primary      // Ações principais (#007bff)
color.secondary    // Ações alternativas
color.success      // Verde de sucesso
color.error        // Vermelho de erro
color.info         // Azul informativo
color.disabled     // Cinza desabilitado
```

**Espaçamento:**
```typescript
spacing.xs   // 4px
spacing.sm   // 8px
spacing.md   // 16px
spacing.lg   // 24px
spacing.xl   // 32px
```

**Radius (Bordas):**
```typescript
radius.sm    // 4px
radius.md    // 8px
```

**Tipografia:**
```typescript
font.body    // Texto padrão
font.label   // Labels de formulário
font.title   // Títulos de seção
```

---

### **10.6. Padrões de Telas (Templates)**

#### **Template: Formulário de Cadastro/Edição**
```typescript
export default function ClienteFormPage() {
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  return (
    <Page title="Cadastro de Cliente">
      <Form onSubmit={handleSubmit}>
        <InputText
          label="Razão Social"
          value={razaoSocial}
          onChange={setRazaoSocial}
          error={errors.razaoSocial}
        />
        
        <InputText
          label="CNPJ"
          variant="cnpj_raiz"
          value={cnpj}
          onChange={setCnpj}
          error={errors.cnpj}
        />
        
        <Alert variant="info">
          Preencha todos os campos obrigatórios antes de salvar.
        </Alert>
        
        <ButtonGroup>
          <Button variant="secondary" onClick={handleCancel}>
            Cancelar
          </Button>
          <Button variant="primary" loading={loading}>
            Salvar Cliente
          </Button>
        </ButtonGroup>
      </Form>
    </Page>
  );
}
```

---

#### **Template: Importação/Processamento**
```typescript
export default function ImportacaoPage() {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  return (
    <Page title="Importação de Vendas">
      <Stepper
        steps={['Upload', 'Validação', 'Processamento', 'Resultado']}
        currentStep={step}
      />
      
      <Card>
        {step === 0 && (
          <FileUpload
            accept=".csv,.xlsx"
            onFileSelect={setFile}
            selectedFile={file}
          />
        )}
        
        {step === 1 && (
          <Alert variant="info">
            Arquivo validado com sucesso. Clique em Processar para continuar.
          </Alert>
        )}
        
        {step === 3 && result && (
          <Card variant="success">
            <h3>Processamento Concluído</h3>
            <p>{result.registros} registros importados</p>
          </Card>
        )}
      </Card>
      
      <ButtonGroup>
        <Button 
          variant="secondary" 
          disabled={step === 0}
          onClick={handleBack}
        >
          Voltar
        </Button>
        <Button 
          variant="primary" 
          loading={processing}
          disabled={!file}
          onClick={handleProcess}
        >
          {step === 0 ? 'Validar' : 'Processar'}
        </Button>
      </ButtonGroup>
    </Page>
  );
}
```

---

#### **Template: Listagem/Resultado**
```typescript
export default function VendasListPage() {
  const { vendas, loading, error } = useVendas();

  if (loading) return <Loading />;
  if (error) return <Alert variant="error">{error}</Alert>;

  return (
    <Page title="Vendas Processadas">
      <Card variant="success">
        <Stats
          total={vendas.length}
          valorTotal={calcularTotal(vendas)}
        />
      </Card>
      
      <Table
        variant="simple"
        columns={VENDAS_COLUMNS}
        data={vendas}
        onSort={handleSort}
      />
      
      <ButtonGroup>
        <Button variant="text" icon="download" onClick={handleExport}>
          Exportar para Excel
        </Button>
      </ButtonGroup>
    </Page>
  );
}
```

---

### **10.7. Acessibilidade (A11y) - Obrigatório**

**Focus Visível:**
```css
/* Todos elementos interativos devem ter focus visível */
button:focus, input:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

**Labels Associados:**
```typescript
// ✅ CORRETO
<label htmlFor="cnpj">CNPJ</label>
<input id="cnpj" type="text" />

// ❌ ERRADO
<div>CNPJ</div>
<input type="text" />
```

**ARIA Labels:**
```typescript
// Botões com ícones devem ter aria-label
<Button variant="icon" aria-label="Exportar relatório">
  <DownloadIcon />
</Button>
```

**Não depender de cor:**
```typescript
// ❌ ERRADO - apenas cor vermelha indica erro
<input style={{borderColor: 'red'}} />

// ✅ CORRETO - ícone + mensagem + cor
<InputText
  error="CNPJ inválido"
  aria-invalid="true"
/>
```

**Navegação por Teclado:**
- Tab: próximo elemento
- Shift+Tab: elemento anterior
- Enter: ativar botão/link
- Escape: fechar modal

---

### **10.8. Workflow para Agents (Passo a Passo)**

**Ao criar nova tela/componente:**

1. **Identificar padrão:**
   - É formulário? → Template Formulário
   - É importação? → Template Processamento
   - É listagem? → Template Resultado

2. **Mapear componentes:**
   - Quais inputs? → InputText com variantes
   - Tem upload? → FileUpload
   - Tem multi-etapas? → Stepper
   - Tem botões? → Button (apenas 1 primary)

3. **Definir estados:**
   ```typescript
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);
   const [data, setData] = useState(null);
   ```

4. **Usar tokens semânticos:**
   ```typescript
   // Não: style={{marginTop: '16px'}}
   // Sim: style={{marginTop: spacing.md}}
   ```

5. **Validar acessibilidade:**
   - [ ] Labels presentes?
   - [ ] ARIA quando necessário?
   - [ ] Focus visível?
   - [ ] Navegação por teclado?

6. **Documentar se novo:**
   Se criou componente novo, adicionar em `ui-design-system-nextjs.md`

---

### **10.9. Erros Comuns e Como Evitar**

#### **Erro 1: Estilos Inline**
```typescript
// ❌ NUNCA FAZER
<div style={{backgroundColor: '#f0f0f0', padding: '20px'}}>

// ✅ SEMPRE FAZER
<Card>
```

#### **Erro 2: Múltiplos Botões Primary**
```typescript
// ❌ ERRADO - confunde usuário
<Button variant="primary">Salvar</Button>
<Button variant="primary">Salvar e Continuar</Button>

// ✅ CORRETO - apenas 1 ação principal
<Button variant="secondary">Salvar Rascunho</Button>
<Button variant="primary">Salvar e Continuar</Button>
```

#### **Erro 3: Mensagens de Erro Genéricas**
```typescript
// ❌ NÃO AJUDA O USUÁRIO
<Alert variant="error">Erro ao processar</Alert>

// ✅ ORIENTA AÇÃO CORRETIVA
<Alert variant="error">
  Erro ao processar arquivo: formato inválido. 
  Utilize arquivos .csv ou .xlsx com as colunas obrigatórias.
</Alert>
```

#### **Erro 4: Ignorar Estados**
```typescript
// ❌ ESQUECEU LOADING E ERROR
const MyComponent = () => {
  const { data } = useData();
  return <Table data={data} />;
};

// ✅ PREVÊ TODOS OS ESTADOS
const MyComponent = () => {
  const { data, loading, error } = useData();
  
  if (loading) return <Loading />;
  if (error) return <Alert variant="error">{error}</Alert>;
  if (!data) return <Alert variant="info">Nenhum dado encontrado</Alert>;
  
  return <Table data={data} />;
};
```

---

### **10.10. Checklist Final (Antes de Commit)**

**UI/UX:**
- [ ] Componentes do Design System utilizados?
- [ ] Tokens semânticos aplicados (sem hard-coded)?
- [ ] Todos estados previstos (loading, error, disabled, success)?
- [ ] Apenas 1 botão primary por tela?
- [ ] Mensagens de erro são acionáveis?
- [ ] Template de tela apropriado utilizado?

**Acessibilidade:**
- [ ] Labels associados a inputs?
- [ ] ARIA labels em ícones/botões sem texto?
- [ ] Focus visível em elementos interativos?
- [ ] Navegação por teclado funcional?
- [ ] Não depende apenas de cor para comunicar estado?

**Código:**
- [ ] TypeScript sem erros?
- [ ] Componentes reutilizáveis criados?
- [ ] Custom hooks para lógica complexa?
- [ ] Props tipadas corretamente?

**Documentação:**
- [ ] Componente novo documentado em `ui-design-system-nextjs.md`?
- [ ] Comentários em lógica complexa?
- [ ] README atualizado se necessário?

---

### **10.11. Referência Rápida - Componentes por Caso de Uso**

| Caso de Uso | Componentes | Template |
|-------------|-------------|----------|
| Cadastro de cliente | InputText, Button, Alert | Formulário |
| Importação de arquivo | FileUpload, Stepper, Card, Alert | Processamento |
| Listagem de vendas | Table, Card, Button (icon) | Resultado |
| Configuração de taxas | InputText, Table, Button | Formulário + Resultado |
| Relatório financeiro | Card, Table, Button (download) | Resultado |
| Login/Autenticação | InputText (email/password), Button | Formulário |

---

### **10.12. Integração com Backend (FastAPI)**

**Sempre usar tipos compartilhados:**
```typescript
// types/vendas.ts (gerado do OpenAPI)
export interface Venda {
  id: number;
  data: string;
  valor: number;
  status: string;
}

// components/VendasTable.tsx
import { Venda } from '@/lib/types/vendas';

export function VendasTable({ vendas }: { vendas: Venda[] }) {
  return <Table data={vendas} columns={COLUMNS} />;
}
```

**Loading states sincronizados:**
```typescript
const { vendas, loading, error, refetch } = useVendas();

<Button 
  variant="primary" 
  loading={loading}  // Desabilita automaticamente
  onClick={refetch}
>
  Atualizar
</Button>
```

---

**Este Design System é MANDATÓRIO para todo desenvolvimento frontend. Qualquer desvio deve ser justificado e documentado.**

---

## 10. Context7 MCP — Documentação Sempre Atualizada

### **O que é Context7?**

Context7 é um servidor MCP (Model Context Protocol) que fornece **documentação atualizada em tempo real** de bibliotecas e frameworks diretamente para assistentes de IA. Elimina código desatualizado, APIs inexistentes e exemplos baseados em dados antigos.

**Benefícios:**
- ✅ Documentação sempre atual (não baseada em training data)
- ✅ APIs verificadas e funcionais
- ✅ Exemplos práticos específicos de versão
- ✅ Suporte a 1000+ bibliotecas

### **Configuração no Projeto**

**Arquivo: `.vscode/settings.json`**
```json
{
  "mcp": {
    "servers": {
      "context7": {
        "url": "https://mcp.context7.com/mcp"
      }
    }
  }
}
```

**Arquivo: `.cursorrules`**
```
Always use Context7 MCP when I need library/API documentation, code generation, 
setup or configuration steps without me having to explicitly ask.

When working with Python libraries (FastAPI, SQLAlchemy, Panel, Pydantic), 
automatically fetch documentation from Context7.

When working with TypeScript/JavaScript libraries (Next.js, React, pnpm), 
automatically fetch documentation from Context7.
```

### **Como Usar**

#### **1. Automático (Recomendado)**
Com `.cursorrules` configurado, basta fazer perguntas sobre código:
```
"Como criar endpoint FastAPI com validação Pydantic?"
"Setup Next.js 14 com TypeScript e App Router"
```

#### **2. Explícito**
Adicione `use context7` ao final do prompt:
```
"Implementar autenticação JWT no FastAPI. use context7"
"Criar middleware Next.js para validação. use context7"
```

#### **3. Com Library ID**
Para biblioteca específica, use o ID exato:
```
"Configure SQLAlchemy. use library /sqlalchemy/sqlalchemy for API and docs."
"Setup pnpm workspace. use library /pnpm/pnpm for API and docs."
```

### **Bibliotecas Principais do Projeto**

#### **Backend Python**
- FastAPI: `/tiangolo/fastapi`
- SQLAlchemy: `/sqlalchemy/sqlalchemy`
- Pydantic: `/pydantic/pydantic`
- Panel/HoloViz: `/holoviz/panel`
- Pandas: `/pandas-dev/pandas`
- pytest: `/pytest-dev/pytest`

#### **Frontend TypeScript**
- Next.js: `/vercel/next.js`
- React: `/facebook/react`
- TypeScript: `/microsoft/TypeScript`
- Axios: `/axios/axios`

#### **DevOps/Tooling**
- Poetry: `/python-poetry/poetry`
- pnpm: `/pnpm/pnpm`
- Docker: `/docker/docs`

### **Ferramentas MCP Context7**

1. **resolve-library-id**
   - Encontra o ID correto da biblioteca
   - Parâmetros: `query`, `libraryName`

2. **query-docs**
   - Busca documentação específica
   - Parâmetros: `libraryId`, `query`

### **Casos de Uso para Financial **

#### **Migração Frontend Panel → Next.js**
```
Como estruturar projeto Next.js 14 com App Router para migrar de Panel? 
Preciso manter autenticação atual e adaptar componentes de tabela. use context7
```

#### **Backend FastAPI Modularizado**
```
Como implementar Repository Pattern + Service Layer no FastAPI?
Preciso separar lógica de negócio do acesso a dados. use context7
```

#### **Dual Database (MySQL/SQLite)**
```
Como fazer SQLAlchemy funcionar com MySQL e SQLite no mesmo código?
Preciso adaptar queries específicas de cada banco. use context7
```

#### **Autenticação e Segurança**
```
Implementar JWT com refresh tokens no FastAPI seguindo best practices. use context7
```

#### **TypeScript Types da API**
```
Como gerar tipos TypeScript automáticos a partir do OpenAPI FastAPI? use context7
```

#### **Otimização de Queries**
```
Best practices para bulk insert com SQLAlchemy e Pandas to_sql. use context7
```

### **API Key (Opcional)**

Para limites maiores de requisições:

1. Acesse: https://context7.com/dashboard
2. Crie conta gratuita
3. Copie API key
4. Adicione em `.vscode/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "context7": {
        "url": "https://mcp.context7.com/mcp",
        "headers": {
          "Authorization": "Bearer SUA_API_KEY_AQUI"
        }
      }
    }
  }
}
```

### **Troubleshooting**

#### **Context7 não responde**
1. Verifique conexão: `ping mcp.context7.com`
2. Recarregue VSCode: `Ctrl+Shift+P → Reload Window`
3. Confirme configuração em `.vscode/settings.json`

#### **Respostas genéricas (não usou Context7)**
- Use explicitamente: `... use context7`
- Verifique `.cursorrules` está no root do projeto
- Mencione biblioteca específica: `use library /tiangolo/fastapi`

#### **Erro de rate limit**
- Crie API key gratuita em https://context7.com/dashboard
- Adicione header Authorization na configuração

### **Regras para Agente IA com Context7**

1. **Sempre usar Context7 para:**
   - Código de bibliotecas específicas (FastAPI, Next.js, etc.)
   - Configuração de ferramentas (Poetry, pnpm, Docker)
   - Best practices e patterns atualizados
   - Exemplos de código funcionais

2. **Especificar versão quando relevante:**
   ```
   "Como usar Server Components no Next.js 14? use context7"
   "Async endpoints no FastAPI 0.109+? use context7"
   ```

3. **Combinar com contexto do projeto:**
   ```
   "Migrar de Panel para Next.js mantendo arquitetura atual de 
   importação/cálculo/relatório. use context7"
   ```

4. **Atualizar este agente:**
   - Ao encontrar soluções via Context7, documentar aqui
   - Manter lista de Library IDs atualizada
   - Adicionar casos de uso específicos do projeto

### **Recursos**

- **Site:** https://context7.com
- **Docs:** https://context7.com/docs
- **GitHub:** https://github.com/upstash/context7
- **Discord:** https://upstash.com/discord
- **Guia Completo:** [CONTEXT7_GUIDE.md](../../CONTEXT7_GUIDE.md)

### **Checklist Context7 para Novos Desenvolvedores**

- [ ] Context7 configurado em `.vscode/settings.json`
- [ ] Regra automática em `.cursorrules` criada
- [ ] VSCode recarregado após configuração
- [ ] Teste básico: "Como criar endpoint FastAPI? use context7"
- [ ] API key configurada (opcional, para mais requests)
- [ ] Library IDs principais conhecidos (FastAPI, Next.js, etc.)

---

**Este arquivo é ponto único de verdade e conhecimento. Toda contribuição IA ou humana deve passar por aquí. Ao migrar para Next.js/FastAPI, este agente será a fonte de onboarding de devs, aprendizado contínuo e prevenção de bugs herdados.**
